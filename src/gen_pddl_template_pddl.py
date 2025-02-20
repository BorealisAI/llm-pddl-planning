# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os

from gpt_client import GPTClient, GPTConfig
from domains import DOMAIN_NAMES
from pddl_utils import get_problem_pddl_empty_goal_and_init
from utils import wrap_code, extract_code
import glob

TRANSLATION_PROMPT = """ You are given the PDDL code of a domain and your task is to modify the PDDL code and remove action preconditions, action effects, and all the predicates.
Please make sure to keep the action names and action signatures (parameter ordering) intact. An example final template is provided below.

{context_domain_pddl}

Now, please provide a template PDDL code for the following domain:

{domain_pddl}
"""

BLOCKS_WORLD_TEMPLATE = wrap_code("""
(define (domain blocksworld-4ops)
  (:requirements :strips)
  (:predicates)

  (:action pickup
    :parameters (?ob)
    :precondition ()
    :effect ()
  )

  (:action putdown
    :parameters (?ob)
    :precondition ()
    :effect ()
  )

  (:action stack
    :parameters (?ob ?underob)
    :precondition ()
    :effect ()
  )

  (:action unstack
    :parameters (?ob ?underob)
    :precondition ()
    :effect ()
  )
)
""", lang='pddl')

TARGET_DOMAIN_NAMES = DOMAIN_NAMES

data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'data')


def _get_domain_pddl(domain_name: str) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/domain.pddl"), 'r') as f:
        return f.read()


def generate_domain_templates():
    # data path is the parent of this file inside data folder

    gpt_client = GPTClient(GPTConfig(
        api_key=os.environ['OPENAI_KEY'],
        model_name='gpt-4-1106-preview',
    ))
    for domain_name in TARGET_DOMAIN_NAMES:
        chat_id, _ = gpt_client.make_new_chat(
            system_message='You are a helpful assistant, skilled in manipulating PDDL code.'
        )
        domain_pddl = _get_domain_pddl(domain_name)
        domain_pddl_wrapped = wrap_code(domain_pddl, lang='pddl')
        user_input = TRANSLATION_PROMPT.format(domain_pddl=domain_pddl_wrapped,
                                               context_domain_pddl=BLOCKS_WORLD_TEMPLATE)
        _, completion, _ = gpt_client.complete_one_chat(chat_id, user_input)
        template_pddl_code = extract_code(completion, lang='pddl')
        with open(os.path.join(data_path, 'domains', f"{domain_name}/domain_template.pddl"), 'w') as f:
            f.write(template_pddl_code)
        print(f"Domain: {domain_name} Done!")

    print(f"Used tokens: {gpt_client.used_tokens}")


def generate_problem_templates():
    for domain_name in TARGET_DOMAIN_NAMES:
        domain_dir = os.path.join(data_path, 'domains', domain_name)
        for file_name in glob.glob(f"{domain_dir}/p*.pddl"):
            if 'template' in file_name:
                continue
            with open(file_name, 'r') as f:
                problem_pddl = f.read()
            problem_pddl_empty_goal_and_init = get_problem_pddl_empty_goal_and_init(problem_pddl)
            with open(file_name.replace('.pddl', '_template.pddl'), 'w') as f:
                f.write(problem_pddl_empty_goal_and_init)
            print(f"Generated problem template for {file_name}")


if __name__ == '__main__':
    generate_domain_templates()
    generate_problem_templates()
