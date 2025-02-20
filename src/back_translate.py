# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os
from gpt_client import GPTClient, GPTConfig
from utils import wrap_code, extract_code
from domains import DOMAIN_NAMES

DOMAIN_TRANSLATION_PROMPT = """Your task is to translate PDDL files into natural language. 
Ensure that the resulting text covers natural language description of its actions, their preconditions, and effects.
DO NOT translate the problem PDDL files, only use problem PDDL to understand the domain. ALWAYS wrap your code in the appropriate markdown syntax.
Two examples are provided below.

Q:
Domain PDDL:
{context1_pddl}
Problem PDDL:
{context1_example_problem_pddl}

A:
{context1_nl}

Q:
Domain PDDL:
{context2_pddl}
Problem PDDL:
{context2_example_problem_pddl}

A:
{context2_nl}

Q:
Domain PDDL:
{context3_pddl}
Problem PDDL:
{context3_example_problem_pddl}

A:
{context3_nl}

Q:
Domain PDDL:
{domain_pddl}
Problem PDDL:
{domain_example_problem_pddl}

"""

PREDICATE_TRANSLATION_PROMPT = """Your task is to generate python predicate descriptor for each environment. You are given the natural language description of the domain along with the PDDL code.

Q:
Domain Description:
{context1_domain_nl}
Domain PDDL:
{context1_domain_pddl}

A:
{context1_python_code}

Q:
Domain Description:
{domain_nl}
Domain PDDL:
{domain_pddl}

A:
"""

PROBLEM_TRANSLATION_PROMPT = """Your task is to translate problem PDDL files into natural language. Ensure that the resulting description covers all initial state and goal conditions. 
DO NOT be lazy in your response, be extremely precise in your descriptions such that all conditions are covered in your description and there is no ambiguity in your description.
If you do not find any common rule about some conditions, list all of them.
For the initial conditions, start with "Initially:", and for the goal conditions, start with "Your goal is to".
ALWAYS wrap your code in the appropriate markdown syntax.
Two examples are provided below.

Q:
Domain Description:
{context1_domain_nl}
Problem PDDL:
{context1_problem_pddl}

A:
{context1_problem_nl}

Q:
Domain Description:
{context2_domain_nl}
Problem PDDL:
{context2_problem_pddl}

A:
{context2_problem_nl}

Q:
Domain Description:
{target_domain_nl}
Problem PDDL:
{target_problem_pddl}

A:
"""

TARGET_DOMAIN_NAMES = DOMAIN_NAMES

data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'data')
gpt_client = GPTClient(GPTConfig(
    api_key=os.environ['OPENAI_KEY'],
    model_name='gpt-4-1106-preview',
))


def _get_domain_pddl(domain_name: str) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/domain.pddl"), 'r') as f:
        return f.read()


def _get_domain_predicate_descriptors(domain_name: str) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/predicate_descriptor.py"), 'r') as f:
        return f.read()


def _get_domain_nl(domain_name: str) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/domain.nl"), 'r') as f:
        return f.read()


def _get_problem_pddl(domain_name: str, problem_name) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/{problem_name}.pddl"), 'r') as f:
        return f.read()


def _get_problem_nl(domain_name: str, problem_name) -> str:
    with open(os.path.join(data_path, 'domains', f"{domain_name}/{problem_name}.nl"), 'r') as f:
        return f.read()


def _get_problem_list(domain_name: str):
    problem_path = os.path.join(data_path, 'domains', domain_name)
    p_list = []
    for p_idx in range(1, 100):
        problem_name = f"p{p_idx:02d}"
        if os.path.isfile(os.path.join(problem_path, f"{problem_name}.pddl")):
            p_list.append(problem_name)
    return p_list


def back_translate_domains(context1_name='grippers', context2_name='childsnack-opt14-strips', context3_name='termes'):
    """
    Back-translate all TARGET_DOMAIN_NAMES domains, given context1, context2, context3 as in-context examples.
    """
    context1_pddl, context1_nl, context1_example_problem_pddl = _get_domain_pddl(context1_name), _get_domain_nl(
        context1_name), _get_problem_pddl(context1_name, 'p_example')
    context2_pddl, context2_nl, context2_example_problem_pddl = _get_domain_pddl(context2_name), _get_domain_nl(
        context2_name), _get_problem_pddl(context2_name, 'p_example')
    context3_pddl, context3_nl, context3_example_problem_pddl = _get_domain_pddl(context3_name), _get_domain_nl(
        context3_name), _get_problem_pddl(context3_name, 'p_example')

    context_domains = [context1_name, context2_name, context3_name]
    for domain_name in TARGET_DOMAIN_NAMES:
        if domain_name in context_domains:
            print(f"Skipping {domain_name} since it is in context domains.")
            continue
        chat_id, _ = gpt_client.make_new_chat(
            system_message='You are a helpful assistant, skilled in translating PDDL code to human-understandable natural language.'
        )
        domain_pddl = _get_domain_pddl(domain_name)
        domain_example_problem_pddl = _get_problem_pddl(domain_name, 'p_example')
        domain_pddl_wrapped = wrap_code(domain_pddl, lang='pddl')
        user_input = DOMAIN_TRANSLATION_PROMPT.format(
            context1_pddl=wrap_code(context1_pddl, lang='pddl'),
            context1_nl=wrap_code(context1_nl, lang='markdown'),
            context1_example_problem_pddl=wrap_code(context1_example_problem_pddl, lang='pddl'),
            context2_pddl=wrap_code(context2_pddl, lang='pddl'),
            context2_nl=wrap_code(context2_nl, lang='markdown'),
            context2_example_problem_pddl=wrap_code(context2_example_problem_pddl, lang='pddl'),
            context3_pddl=wrap_code(context3_pddl, lang='pddl'),
            context3_nl=wrap_code(context3_nl, lang='markdown'),
            context3_example_problem_pddl=wrap_code(context3_example_problem_pddl, lang='pddl'),
            domain_pddl=domain_pddl_wrapped,
            domain_example_problem_pddl=wrap_code(domain_example_problem_pddl, lang='pddl'),
        )
        _, completion, _ = gpt_client.complete_one_chat(chat_id, user_input)
        extracted_nl = extract_code(completion, lang='markdown')
        with open(os.path.join(data_path, 'domains', f"{domain_name}/domain.nl"), 'w') as f:
            f.write(extracted_nl)
        print(f"Domain: {domain_name} Done")

    print(f"Used tokens: {gpt_client.used_tokens}")


def get_problem_prompt(domain1, domain2, target_domain_nl, target_problem_pddl):
    context1_domain_nl = _get_domain_nl(domain1)
    context1_problem_pddl = _get_problem_pddl(domain1, 'p_example')
    context1_problem_nl = _get_problem_nl(domain1, 'p_example')
    context2_domain_nl = _get_domain_nl(domain2)
    context2_problem_pddl = _get_problem_pddl(domain2, 'p_example')
    context2_problem_nl = _get_problem_nl(domain2, 'p_example')
    user_input = PROBLEM_TRANSLATION_PROMPT.format(
        context1_domain_nl=wrap_code(context1_domain_nl, lang='markdown'),
        context1_problem_pddl=wrap_code(context1_problem_pddl, lang='pddl'),
        context1_problem_nl=wrap_code(context1_problem_nl, lang='markdown'),
        context2_domain_nl=wrap_code(context2_domain_nl, lang='markdown'),
        context2_problem_pddl=wrap_code(context2_problem_pddl, lang='pddl'),
        context2_problem_nl=wrap_code(context2_problem_nl, lang='markdown'),
        target_domain_nl=wrap_code(target_domain_nl, lang='markdown'),
        target_problem_pddl=wrap_code(target_problem_pddl, lang='pddl')
    )
    return user_input


def back_translate_problems(domain1='termes', domain2='satellite'):
    """
    First, we back-translate the p_example then we use p_example to back-translate the rest.
    """

    for domain_name in TARGET_DOMAIN_NAMES:
        problem_list = _get_problem_list(domain_name)
        for problem_name in ['p_example'] + problem_list:
            chat_id, _ = gpt_client.make_new_chat(
                system_message='You are a helpful assistant, skilled in translating Planning Domain Definition Language (PDDL) code to natural language with high precision. You always wrap your code in the appropriate markdown syntax.'
            )
            target_domain_nl = _get_domain_nl(domain_name)
            target_problem_pddl = _get_problem_pddl(domain_name, problem_name)
            user_input = get_problem_prompt(domain1, domain2, target_domain_nl, target_problem_pddl)
            _, completion, _ = gpt_client.complete_one_chat(chat_id, user_input)
            print(f"Domain: {domain_name}, Problem: {problem_name}")
            extracted_nl = extract_code(completion, lang='markdown')
            with open(os.path.join(data_path, 'domains', f"{domain_name}/{problem_name}.nl"), 'w') as f:
                f.write(extracted_nl)
            if problem_name == 'p_example':
                domain2 = domain_name
    print(f"Used tokens: {gpt_client.used_tokens}")


def back_translate_predicate_descriptors(domain1='blocksworld'):
    """
    Back-translate all TARGET_DOMAIN_NAMES predicate descriptors, given domain1 as in-context example.
    """
    for domain_name in TARGET_DOMAIN_NAMES:
        if domain_name == domain1:
            print(f"Skipping {domain_name} since it is in context domain.")
            continue
        domain1_pddl, domain1_nl, = _get_domain_pddl(domain1), _get_domain_nl(domain1)
        domain1_predicate_descriptor = _get_domain_predicate_descriptors(domain1)
        chat_id, _ = gpt_client.make_new_chat(
            system_message='You are a helpful assistant, skilled in generating python code with high precision. You always wrap your code in the appropriate python syntax.'
        )
        target_domain_pddl, target_domain_nl = _get_domain_pddl(domain_name), _get_domain_nl(domain_name)
        user_input = PREDICATE_TRANSLATION_PROMPT.format(
            context1_domain_pddl=wrap_code(domain1_pddl, lang='pddl'),
            context1_domain_nl=wrap_code(domain1_nl, lang='markdown'),
            context1_python_code=wrap_code(domain1_predicate_descriptor, lang='python'),
            domain_nl=wrap_code(target_domain_nl, lang='markdown'),
            domain_pddl=wrap_code(target_domain_pddl, lang='pddl'),
        )
        _, completion, _ = gpt_client.complete_one_chat(chat_id, user_input)
        print(f"Domain: {domain_name}")
        extracted_python = extract_code(completion, lang='python')
        with open(os.path.join(data_path, 'domains', f"{domain_name}/predicate_descriptor.py"), 'w') as f:
            f.write(extracted_python)
    print(f"Used tokens: {gpt_client.used_tokens}")


if __name__ == '__main__':
    back_translate_domains()
    back_translate_problems()
    back_translate_predicate_descriptors()
