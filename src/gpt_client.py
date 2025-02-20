# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import json

import openai
from openai import OpenAI
from dataclasses import dataclass
import uuid
import logging
from copy import deepcopy
import backoff


@dataclass
class GPTConfig:
    api_key: str
    model_name: str = 'gpt-3.5-turbo-1106'
    max_tokens: int = 4000
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class GPTClient:
    OPENAI_MODELS = [
        'gpt-3.5-turbo-1106',
        'gpt-3.5-turbo-0125',
        'gpt-4-1106-preview',
        'gpt-4-0125-preview',
        'gpt-4-turbo-2024-04-09',
    ]
    PRICE_PER_M = {
        'gpt-3.5-turbo-1106': 1.0,
        'gpt-3.5-turbo-0125': 0.5,
        'gpt-4-1106-preview': 10,
        'gpt-4-0125-preview': 10,
        'gpt-4-turbo-2024-04-09': 10,
    }
    MAX_CALLS = 400

    def __init__(self, config: GPTConfig) -> None:
        self.config = config
        if config.model_name in self.OPENAI_MODELS:
            self.client = OpenAI(api_key=config.api_key)
        else:
            raise ValueError(f"Unsupported model name: {config.model_name}")
        self.used_prompt_tokens = 0
        self.used_completion_tokens = 0
        self.gpt_calls = 0
        self.conv_cache = {}

    def complete_one_chat(self, conv_id, user_input, temp=0.0):
        conv_ids, gpt_outputs, aux = self.complete_n_chats(conv_id, user_input, n_completions=1, temp=temp)
        return conv_ids[0], gpt_outputs[0], aux

    def complete_n_chats(self, conv_id, user_input, n_completions: int, temp: float):
        if self.gpt_calls >= self.MAX_CALLS:
            raise ValueError(f"Exceeded the maximum number of GPT calls: {self.MAX_CALLS}")
        self.add_chat_messages(conv_id, [{'role': 'user', 'content': user_input}])
        cur_chat = self.conv_cache[conv_id]
        conv_ids, chats = self._copy_chat(conv_id, n_completions)
        response_messages, (used_input_tokens, used_output_tokens), aux = self._complete_client_chat(
            messages=cur_chat, temperature=temp, n=n_completions, max_tokens=self.config.max_tokens
        )
        self.used_prompt_tokens += used_input_tokens
        self.used_completion_tokens += used_output_tokens
        self.gpt_calls += 1
        gpt_outputs = []
        for i in range(n_completions):
            msg_content = response_messages[i]
            gpt_outputs.append(msg_content)
            self.add_chat_messages(
                conv_ids[i], [{'role': 'assistant', 'content': msg_content}]
            )
        return conv_ids, gpt_outputs, aux

    def _complete_client_chat(self, messages, temperature, n, max_tokens):
        aux = {}
        if self.config.model_name in self.OPENAI_MODELS:
            completions = self.openai_completion_with_backoff(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                n=n,
                logprobs=True,
                max_tokens=max_tokens,
            )
            logprob_means = []
            for i in range(n):
                logprob_list = completions.choices[i].logprobs.content
                logprob_vals = [lp.logprob for lp in logprob_list]
                logprob_means.append(sum(logprob_vals) / len(logprob_vals))
            aux['logprob_means'] = logprob_means
            response_messages = [completions.choices[i].message.content for i in range(n)]
            used_input_tokens = completions.usage.prompt_tokens
            used_output_tokens = completions.usage.completion_tokens
        else:
            raise ValueError(f"Unsupported model name: {self.config.model_name}")
        return response_messages, (used_input_tokens, used_output_tokens), aux

    def make_new_chat(self, system_message):
        conv_id = str(uuid.uuid4())
        chat = [
            {'role': 'system', 'content': system_message},
        ]
        self.conv_cache[conv_id] = chat
        return conv_id, chat

    def add_chat_messages(self, conv_id, messages):
        self.conv_cache[conv_id].extend(messages)

    def get_chat_messages(self, conv_id):
        return self.conv_cache[conv_id]

    def _copy_chat(self, conv_id, n_times):
        conv_ids = [str(uuid.uuid4()) for _ in range(n_times)]
        chats = []
        for new_conv_id in conv_ids:
            self.conv_cache[new_conv_id] = deepcopy(self.conv_cache[conv_id])
            chats.append(self.conv_cache[new_conv_id])
        return conv_ids, chats

    def save_chats(self, save_dir):
        os.makedirs(save_dir, exist_ok=True)
        for conv_id, chat in self.conv_cache.items():
            f_name = os.path.join(save_dir, f"chat_{conv_id}.json")
            logging.info(f"Saving the chat history with GPT model to {f_name}")
            with open(f_name, 'w') as f:
                json.dump(chat, f)

    def is_openai_model(self):
        return self.config.model_name in self.OPENAI_MODELS

    @property
    def used_tokens(self):
        cost = self.get_cost()
        return f"{self.used_prompt_tokens} prompt tokens, {self.used_completion_tokens} completion tokens, " \
               f"costing ${cost:.3f}"

    def get_cost(self):
        try:
            base_price = self.PRICE_PER_M[self.config.model_name]
            output_factor = 3 if self.config.model_name in self.OPENAI_MODELS else 5
            return base_price * (self.used_prompt_tokens + output_factor * self.used_completion_tokens) / 1e6
        except:
            print("Error in getting cost")
            return -1


    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=5)
    def openai_completion_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)
