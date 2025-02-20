# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os

from utils import wrap_code

ONE_SHOT_INIT_PROMPT_TEMPLATE = """You are given a natural language description of a planning problem in the domain {target_domain_name} along with one problem instance in PDDL format. Your task is to generate a PDDL domain for the target domain {target_domain_name} that is equivalent to its natural language description and is compatible with the provided problem instance. 

Starting from a PDDL domain template, you are allowed to modify the template using the following two python function interfaces:

```python
add_or_update_predicates(predicates: List[str])
modify_action(action_name: str, new_preconditions: List[str], new_effects: List[str])
```

An example of above functions applied to an example PDDL domain template is as follows:

{context_shot_example}

Target Domain Description:
{target_domain_nl}

Target Problem PDDL:
{target_problem_pddl}

Now, your task is to complete the following PDDL template by generating necessary predicates and action preconditions and effects:

Target PDDL Template:
{target_domain_template_pddl}

You must never modify action parameters, and you are only allowed to use the following two function interfaces to modify the template.

"""

BLOCKS_WORLD_EXAMPLE = """Example Domain Description:
```markdown
The robot has four actions: pickup, putdown, stack, and unstack. The domain assumes a world where there are a set of blocks that can be stacked on top of each other, an arm that can hold one block at a time, and a table where blocks can be placed.
The actions defined in this domain include:
pickup: allows the arm to pick up a block from the table if it is clear and the arm is empty. After the pickup action, the arm will be holding the block, and the block will no longer be on the table or clear.
putdown: allows the arm to put down a block on the table if it is holding a block. After the putdown action, the arm will be empty, and the block will be on the table and clear.
stack: allows the arm to stack a block on top of another block if the arm is holding the top block and the bottom block is clear. After the stack action, the arm will be empty, the top block will be on top of the bottom block, and the bottom block will no longer be clear.
unstack: allows the arm to unstack a block from on top of another block if the arm is empty and the top block is clear. After the unstack action, the arm will be holding the top block, the top block will no longer be on top of the bottom block, and the bottom block will be clear.
```

Example Problem PDDL:
```pddl
(define (problem BW-rand-5)
  (:domain blocksworld-4ops)
  (:objects b1 b2 b3 b4 b5 )
  (:init
    (arm-empty)
    (on b1 b4)
    (on b2 b5)
    (on b3 b2)
    (on-table b4)
    (on b5 b1)
    (clear b3)
  )
  (:goal
    (and
      (on b4 b3)
    )
  )
)
```

Example PDDL Template:
```pddl
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
```

Example Completion:
```python
add_or_update_predicates([
    '(clear ?x)',
    '(on-table ?x)',
    '(arm-empty)',
    '(holding ?x)',
    '(on ?x ?y)'
])
modify_action('pickup', [
    "(clear ?ob)",
    "(on-table ?ob)",
    "(arm-empty)"
], [
    "(holding ?ob)",
    "(not (clear ?ob))",
    "(not (on-table ?ob))",
    "(not (arm-empty))"
])

modify_action('putdown', [
    "(holding ?ob)"
], [
    "(clear ?ob)",
    "(arm-empty)",
    "(on-table ?ob)",
    "(not (holding ?ob))"
])

modify_action('stack', [
    "(clear ?underob)",
    "(holding ?ob)"
], [
    "(arm-empty)",
    "(clear ?ob)",
    "(on ?ob ?underob)",
    "(not (clear ?underob))",
    "(not (holding ?ob))"
])

modify_action('unstack', [
    "(on ?ob ?underob)",
    "(clear ?ob)",
    "(arm-empty)"
], [
    "(holding ?ob)",
    "(clear ?underob)",
    "(not (on ?ob ?underob))",
    "(not (clear ?ob))",
    "(not (arm-empty))"
])
```
"""
ACTION_LEVEL_INIT_PROMPT_TEMPLATE = """You are given a natural language description of a planning problem in the domain {target_domain_name} along with one problem instance in PDDL format. Your task is to generate a PDDL domain for the target domain {target_domain_name} that is equivalent to its natural language description and is compatible with the provided problem instance. The following is an example of a valid PDDL domain:

{context_domain_pddl}

Natural language description of the domain:

{target_domain_nl}

PDDL description of the problem:

{target_problem_pddl}

Now, your task is to complete the following PDDL template by generating necessary predicates and action preconditions and effects:

{target_domain_template_pddl}

You must never modify action parameters, and you are only allowed to use the following two function interfaces to modify the template.

```python
add_or_update_predicates(predicates: List[str])
modify_action(action_name: str, new_preconditions: List[str], new_effects: List[str])
```

An example of above functions is as follows:

```python
add_or_update_predicates(['(is-robot ?x)'])
modify_action('move', ['(is-robot ?x)'], ['(is-robot ?y)'])
```
"""

# Problem Translation

PROBLEM_TRANSLATION_SYSTEM_MESSAGE = """You are a helpful assistant, skilled in producing Planning Domain Definition Language (PDDL) code of problems given a natural language description of a planning problem."""
with open(os.path.join(os.path.dirname(__file__), os.pardir, 'data/domains/blocksworld/domain.pddl'), 'r') as f:
    BLOCKS_WORLD_DOMAIN_PDDL_WRAPPED = wrap_code(f.read(), lang='pddl')
with open(os.path.join(os.path.dirname(__file__), os.pardir, 'data/domains/blocksworld/domain.nl'), 'r') as f:
    BLOCKS_WORLD_DOMAIN_NL_WRAPPED = wrap_code(f.read(), lang='markdown')
PROBLEM_TRANSLATION_BLOCKS_WORLD_INPUT = """Domain Description:
{blocks_world_domain_nl_wrapped}
{maybe_context_domain_pddl}

Problem Description:
```markdown
You are tasked with manipulating a set of blocks using a robotic arm that can perform four actions: pickup, putdown, stack, and unstack.

Initially:
- The robotic arm is empty.
- Block b1 is on block b4.
- Block b2 is on block b5.
- Block b3 is on block b2, and it is clear.
- Block b4 is on the table.
- Block b5 is on block b1.

Your goal is to achieve the following configuration:
- Block b4 must be stacked on top of block b3.
```

Problem PDDL Template:
```pddl
(define (problem BW-rand-5)
    (:domain blocksworld-4ops)
    (:objects b1 b2 b3 b4 b5)
    (:init )
    (:goal (and ))
)
```
"""
PROBLEM_TRANSLATION_BLOCKS_WORLD_OUTPUT = """Problem PDDL:
```markdown
(define (problem BW-rand-5)
  (:domain blocksworld-4ops)
  (:objects b1 b2 b3 b4 b5 )
  (:init
    ; The robotic arm is empty.
    (arm-empty)
    ; Block b1 is on block b4.
    (on b1 b4)
    ; Block b2 is on block b5.
    (on b2 b5)
    ; Block b3 is on block b2, and it is clear.
    (on b3 b2)
    (clear b3)
    ; Block b4 is on the table.
    (on-table b4)
    ; Block b5 is on block b1.
    (on b5 b1)
  )
  (:goal
    (and
      ; Block b4 must be stacked on top of block b3.
      (on b4 b3)
    )
  )
)
```
"""
PROBLEM_TRANSLATION_USER_INPUT_TEMPLATE = """Domain Description:
{target_domain_nl}
{maybe_target_domain_pddl}

Problem Description:
{target_problem_nl}

Problem PDDL Template:
{target_problem_template_pddl}
"""


def get_problem_translation_messages(
        target_domain_nl, target_problem_nl, target_problem_template_pddl, target_domain_pddl=None
):
    if target_domain_pddl is not None:
        maybe_context_domain_pddl = f"\nDomain PDDL:\n{BLOCKS_WORLD_DOMAIN_PDDL_WRAPPED}"
        maybe_target_domain_pddl = f"\nDomain PDDL:\n{target_domain_pddl}"
    else:
        maybe_context_domain_pddl = ""
        maybe_target_domain_pddl = ""

    return PROBLEM_TRANSLATION_SYSTEM_MESSAGE, [
        {'role': 'user',
         'content': 'Given a natural language description of a planning problem in PDDL format, your task is to generate a complete PDDL problem instance that is equivalent to its natural language description and is thorough and complete.'},
        {'role': 'assistant',
         'content': 'Sure, please provide the natural language description of the planning problem, and I will help you generate the corresponding PDDL problem instance.'},
        {'role': 'user', 'content': PROBLEM_TRANSLATION_BLOCKS_WORLD_INPUT.format(
            blocks_world_domain_nl_wrapped=BLOCKS_WORLD_DOMAIN_NL_WRAPPED,
            maybe_context_domain_pddl=maybe_context_domain_pddl
        )},
        {'role': 'assistant', 'content': PROBLEM_TRANSLATION_BLOCKS_WORLD_OUTPUT},
    ], PROBLEM_TRANSLATION_USER_INPUT_TEMPLATE.format(
        target_domain_nl=target_domain_nl,
        maybe_target_domain_pddl=maybe_target_domain_pddl,
        target_problem_nl=target_problem_nl,
        target_problem_template_pddl=target_problem_template_pddl,
    )


# Domain Translation

DOMAIN_TRANSLATION_SYSTEM_MESSAGE = """You are a helpful assistant, skilled in producing Planning Domain Definition Language (PDDL) code of domains given a natural language description of a planning domain. You always wrap your code in the appropriate markdown or PDDL syntax."""
DOMAIN_TRANSLATION_CONTEXT_DOMAIN_INPUT = """Domain Description:
{context_domain_nl}

Problem Description:
{context_problem_nl}

Domain PDDL Template:
{context_domain_template_pddl}
"""
DOMAIN_TRANSLATION_CONTEXT_DOMAIN_OUTPUT = """Domain PDDL:
{context_domain_pddl}
"""
DOMAIN_TRANSLATION_USER_INPUT_TEMPLATE = """Domain Description:
{target_domain_nl}

Problem Description:
{target_problem_nl}

Domain PDDL Template:
{target_domain_template_pddl}
"""


def get_domain_translation_messages(
        context_domain_nl, context_problem_nl, context_domain_template_pddl, context_domain_pddl,
        target_domain_nl, target_problem_nl, target_domain_template_pddl
):
    return DOMAIN_TRANSLATION_SYSTEM_MESSAGE, [
        {'role': 'user',
         'content': 'Given a natural language description of a planning domain in PDDL format as well as domain template and an example problem description, your task is to generate a complete PDDL domain that is equivalent to its natural language description and is thorough and complete.'},
        {'role': 'assistant',
         'content': 'Sure, I would be happy to help you generate a PDDL domain based on the natural language description and domain template you provide. Please share the natural language description of the planning domain, the domain template, and the example problem description, and I will assist you in creating the corresponding PDDL domain.'},
        {'role': 'user', 'content': DOMAIN_TRANSLATION_CONTEXT_DOMAIN_INPUT.format(
            context_domain_nl=context_domain_nl,
            context_problem_nl=context_problem_nl,
            context_domain_template_pddl=context_domain_template_pddl
        )},
        {'role': 'assistant', 'content': DOMAIN_TRANSLATION_CONTEXT_DOMAIN_OUTPUT.format(
            context_domain_pddl=context_domain_pddl
        )},
    ], DOMAIN_TRANSLATION_USER_INPUT_TEMPLATE.format(
        target_domain_nl=target_domain_nl,
        target_problem_nl=target_problem_nl,
        target_domain_template_pddl=target_domain_template_pddl
    )


ONE_SHOT_PROBLEM_TRANSLATION_PROMPT = """Your task is to generate PDDL code for problems given a natural language description of a planning problem and a PDDL template for the problem instance.
To achieve this task, you are also given a natural language description of the domain, the PDDL code of the domain, and a PDDL problem instance.
Always wrap your code in the appropriate PDDL syntax.

Domain Description:
{domain_nl}

Domain PDDL:
{domain_pddl}

Q:
Problem Description:
{context_problem_nl}
Problem PDDL Template:
{context_problem_template_pddl}

A:
{context_problem_pddl}

Now, please provide a PDDL code for the following problem:

Q:
Problem Description:
{target_problem_nl}
Problem PDDL Template:
{target_problem_template_pddl}

A:
"""
