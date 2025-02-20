# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from typing import List

from ml_collections import ConfigDict

import prompts
from domains import Domain
from gpt_client import GPTClient
from pddl_utils import validate_problem_pddl
from utils import wrap_code, extract_code


def generate_exact_n_problem_translation_candidates(
        *,
        n_candidates: int,
        **kwargs
) -> List[str]:
    gen_list = []
    for tries in range(3):
        remaining_candidates = n_candidates - len(gen_list)
        if remaining_candidates <= 0:
            break
        candidates = generate_problem_translation_candidates(
            n_candidates=remaining_candidates,
            **kwargs
        )
        gen_list.extend(candidates)
    if len(gen_list) < n_candidates:
        logging.warning(
            f"Could not generate {n_candidates} problem translation candidates. Only {len(gen_list)} were generated."
        )
    return gen_list


def generate_problem_translation_candidates(
        gpt_client: GPTClient,
        context_domain: Domain,
        target_domain: Domain,
        task_index: int,
        n_candidates: int,
        logprob_selection: bool,
        logprob_candidates: int,
        add_domain_proposal: bool,
        one_domain_per_candidate: bool,
        exp_flags: ConfigDict,
) -> List[str]:
    assert context_domain.name == 'blocksworld', "Only blocksworld is supported to be the context domain."
    if logprob_selection:
        assert n_candidates < logprob_candidates, "The number of candidates should be less than the number of logprob candidates."
        assert gpt_client.is_openai_model(), "Logprob selection is only supported for OpenAI Models."
    assert not (
            logprob_selection and one_domain_per_candidate), "Either logprob_selection or one_domain_per_candidate should be False."
    generation_candidates = n_candidates if not logprob_selection else logprob_candidates
    problem_pddl, problem_nl, problem_pddl_template = target_domain.get_task(task_index)
    if add_domain_proposal:
        n_domain_candidates = generation_candidates if one_domain_per_candidate else 1
        generated_domains = generate_domain_translation_candidates(
            gpt_client=gpt_client,
            context_domain=context_domain,
            target_domain=target_domain,
            task_index=task_index,
            n_candidates=n_domain_candidates,
            exp_flags=exp_flags
        )
        target_domain_proposed_pddls = [wrap_code(domain, lang='pddl') for domain in generated_domains]
    else:
        target_domain_proposed_pddls = [None]
    assert len(target_domain_proposed_pddls) == 1 or len(target_domain_proposed_pddls) == generation_candidates
    final_gpt_outputs = []
    for target_domain_proposed_pddl in target_domain_proposed_pddls:
        candidates_to_generate = generation_candidates if len(target_domain_proposed_pddls) == 1 else 1
        system_prompt, few_shot_messages, user_input = prompts.get_problem_translation_messages(
            target_domain_nl=wrap_code(target_domain.get_domain_nl(), lang='markdown'),
            target_problem_nl=wrap_code(problem_nl, lang='markdown'),
            target_problem_template_pddl=wrap_code(problem_pddl_template, lang='pddl'),
            target_domain_pddl=target_domain_proposed_pddl,
        )
        conv_id, _ = gpt_client.make_new_chat(system_message=prompts.PROBLEM_TRANSLATION_SYSTEM_MESSAGE)
        gpt_client.add_chat_messages(conv_id, few_shot_messages)
        if candidates_to_generate == 1:
            conv_id, gpt_output, aux = gpt_client.complete_one_chat(conv_id, user_input)
            gpt_outputs = [gpt_output]
        else:
            conv_ids, gpt_outputs, aux = gpt_client.complete_n_chats(conv_id, user_input, candidates_to_generate,
                                                                     temp=0.7)

        if logprob_selection:
            logprobs = aux['logprob_means']
            logprob_indices = sorted(range(len(logprobs)), key=lambda i: logprobs[i], reverse=True)
            gpt_outputs = [gpt_outputs[i] for i in logprob_indices[:n_candidates]]
        final_gpt_outputs.extend(gpt_outputs)

    assert len(final_gpt_outputs) <= n_candidates
    # Verify that the generated PDDL is valid
    valid_problems = []
    for output in final_gpt_outputs:
        try:
            extracted_pddl = extract_code(output, lang='pddl')
            validate_problem_pddl(extracted_pddl)
            valid_problems.append(extracted_pddl)
        except Exception as e:
            pass

    return valid_problems


def generate_domain_translation_candidates(
        gpt_client: GPTClient,
        context_domain: Domain,
        target_domain: Domain,
        task_index: int,
        n_candidates: int,
        exp_flags: ConfigDict,
) -> List[str]:
    assert context_domain.name == 'blocksworld', "Only blocksworld is supported to be the context domain."
    system_prompt, few_shot_messages, user_input = prompts.get_domain_translation_messages(
        context_domain_nl=wrap_code(context_domain.get_domain_nl(), lang='markdown'),
        context_problem_nl=wrap_code(context_domain.get_task_nl(0), lang='markdown'),
        context_domain_template_pddl=wrap_code(context_domain.get_domain_template_pddl(), lang='pddl'),
        context_domain_pddl=wrap_code(context_domain.get_domain_pddl(), lang='pddl'),
        target_domain_nl=wrap_code(target_domain.get_domain_nl(), lang='markdown'),
        target_problem_nl=wrap_code(target_domain.get_task_nl(task_index), lang='markdown'),
        target_domain_template_pddl=wrap_code(target_domain.get_domain_template_pddl(), lang='pddl'),
    )
    conv_id, _ = gpt_client.make_new_chat(system_message=prompts.DOMAIN_TRANSLATION_SYSTEM_MESSAGE)
    gpt_client.add_chat_messages(conv_id, few_shot_messages)
    if n_candidates == 1:
        conv_id, gpt_output, _ = gpt_client.complete_one_chat(conv_id, user_input)
        gpt_outputs = [gpt_output]
    else:
        conv_ids, gpt_outputs, _ = gpt_client.complete_n_chats(conv_id, user_input, n_candidates, temp=0.7)
    pddl_codes = [extract_code(output, lang='pddl') for output in gpt_outputs]
    return pddl_codes


def translate_problems_given_one_task(
        gpt_client: GPTClient,
        domain_pddl: str,
        domain_nl: str,
        context_problem_pddl: str,
        context_problem_nl,
        context_problem_template_pddl: str,
        target_problem_nls: List[str],
        target_problem_templates: List[str],
):
    system_message = prompts.PROBLEM_TRANSLATION_SYSTEM_MESSAGE
    results = []
    for target_problem_nl, target_problem_template in zip(target_problem_nls, target_problem_templates):
        prompt = prompts.ONE_SHOT_PROBLEM_TRANSLATION_PROMPT.format(
            domain_nl=wrap_code(domain_nl, lang='markdown'),
            domain_pddl=wrap_code(domain_pddl, lang='pddl'),
            context_problem_nl=wrap_code(context_problem_nl, lang='markdown'),
            context_problem_pddl=wrap_code(context_problem_pddl, lang='pddl'),
            context_problem_template_pddl=wrap_code(context_problem_template_pddl, lang='pddl'),
            target_problem_nl=wrap_code(target_problem_nl, lang='markdown'),
            target_problem_template_pddl=wrap_code(target_problem_template, lang='pddl'),
        )
        conv_id, _ = gpt_client.make_new_chat(system_message=system_message)
        conv_id, gpt_output, _ = gpt_client.complete_one_chat(conv_id, prompt)
        generated_pddl = extract_code(gpt_output, lang='pddl')
        results.append(generated_pddl)
    return results
