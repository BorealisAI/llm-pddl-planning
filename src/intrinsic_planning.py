# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import numpy as np
import random
from absl import app
from ml_collections.config_dict import ConfigDict
from ml_collections import config_flags
import uuid
import logging
from gpt_client import GPTClient, GPTConfig
from domains import Domain, PDDLEnv
import coloredlogs
import json
import wandb

from utils import wrap_code, extract_code

_CONFIG = config_flags.DEFINE_config_dict(
    'cfg',
    ConfigDict(dict(
        run_id=str(uuid.uuid4())[:8],
        debug=False,
        data_path='./data',
        exp_path='./experiments',
        log_prefix="test",
        seed=42,
        use_cot=False,
        gpt_args=dict(
            api_key="your-openai-api-key",
            model_name='gpt-4-1106-preview',
        ),
        env_args=dict(
            fd_py_path='/path/to/planning/library.py',
            fd_search_time_limit=300,
            val_bin_path='/path/to/VAL/bin/Validate',
        ),
        wandb_args=dict(
            project="llm-planning",
            entity="your-wandb-entity",
        ),
        max_tasks=10,  # Maximum number of tasks to evaluate
        context_domain_name='blocksworld',
        target_domain_name='grippers',
    ))
)

SYSTEM_MESSAGE = """You are a helpful assistant, skilled in producing Planning Domain Definition Language (PDDL) plans given a natural language description of a planning domain. You always wrap your code in the appropriate markdown or PDDL syntax."""
BLOCKSWORLD_COT_PLAN = """; Initial state:
; (arm-empty)
; (on b1 b4)
; (on b2 b5)
; (on b3 b2)
; (on-table b4)
; (on b5 b1)
; (clear b3)

; Goal state:
; (on b4 b3)

; Step 1: Unstack b3 from b2
(unstack b3 b2)
; Effects: (holding b3) (clear b2) (not (on b3 b2)) (not (clear b3)) (not (arm-empty))

; Step 2: Putdown b3 on the table
(putdown b3)
; Effects: (clear b3) (arm-empty) (on-table b3) (not (holding b3))

; Step 3: Unstack b2 from b5
(unstack b2 b5)
; Effects: (holding b2) (clear b5) (not (on b2 b5)) (not (clear b2)) (not (arm-empty))

; Step 4: Putdown b2 on the table
(putdown b2)
; Effects: (clear b2) (arm-empty) (on-table b2) (not (holding b2))

; Step 5: Unstack b5 from b1
(unstack b5 b1)
; Effects: (holding b5) (clear b1) (not (on b5 b1)) (not (clear b5)) (not (arm-empty))

; Step 6: Putdown b5 on the table
(putdown b5)
; Effects: (clear b5) (arm-empty) (on-table b5) (not (holding b5))

; Step 7: Unstack b1 from b4
(unstack b1 b4)
; Effects: (holding b1) (clear b4) (not (on b1 b4)) (not (clear b1)) (not (arm-empty))

; Step 8: Putdown b1 on the table
(putdown b1)
; Effects: (clear b1) (arm-empty) (on-table b1) (not (holding b1))

; Step 9: Pickup b4 from the table
(pickup b4)
; Effects: (holding b4) (not (clear b4)) (not (on-table b4)) (not (arm-empty))

; Step 10: Stack b4 on b3
(stack b4 b3)
; Effects: (arm-empty) (clear b4) (on b4 b3) (not (clear b3)) (not (holding b4))

; Final state:
; (arm-empty)
; (on b4 b3)
; (clear b4)
"""
BLOCKSWORLD_NO_COT_PLAN = """(unstack b3 b2)
(putdown b3)
(unstack b2 b5)
(putdown b2)
(unstack b5 b1)
(putdown b5)
(unstack b1 b4)
(putdown b1)
(pickup b4)
(stack b4 b3)
"""
INTERNAL_PLAN_PROMPT_TEMPLATE = """Given a natural language description of a planning domain in PDDL format as well as domain template and an example problem description, your task is to generate a valid PDDL plan which starting from the initial state of the problem, reaches a goal state, while respecting the domain preconditions and effects.
Below, you are given an example from the Blocks World domain.

Example Domain Description:
```markdown
The robot has four actions: pickup, putdown, stack, and unstack. The domain assumes a world where there are a set of blocks that can be stacked on top of each other, an arm that can hold one block at a time, and a table where blocks can be placed.
The actions defined in this domain include:
pickup: allows the arm to pick up a block from the table if it is clear and the arm is empty. After the pickup action, the arm will be holding the block, and the block will no longer be on the table or clear.
putdown: allows the arm to put down a block on the table if it is holding a block. After the putdown action, the arm will be empty, and the block will be on the table and clear.
stack: allows the arm to stack a block on top of another block if the arm is holding the top block and the bottom block is clear. After the stack action, the arm will be empty, the top block will be on top of the bottom block, and the bottom block will no longer be clear.
unstack: allows the arm to unstack a block from on top of another block if the arm is empty and the top block is clear. After the unstack action, the arm will be holding the top block, the top block will no longer be on top of the bottom block, and the bottom block will be clear.
```

Example Domain Template:
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

Example Problem Description:
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

Example Problem Template:
```pddl
(define (problem BW-rand-5)
    (:domain blocksworld-4ops)
    (:objects b1 b2 b3 b4 b5)
    (:init )
    (:goal (and ))
)
```

Example Plan:
{blocksworld_plan}

Target Domain Description:
{target_domain_nl}

Target Domain Template:
{target_domain_pddl}

Target Problem Description:
{target_problem_nl}

Target Problem Template:
{target_problem_pddl}

Target Plan:
"""


def _remove_comments(plan_code):
    return '\n'.join([line for line in plan_code.split('\n') if not line.strip().startswith(';')])


def _evaluate_task(gpt_client: GPTClient, pddl_env, target_domain: Domain, task_index, use_cot):
    if use_cot:
        blocksworld_plan = BLOCKSWORLD_COT_PLAN
    else:
        blocksworld_plan = BLOCKSWORLD_NO_COT_PLAN
    prompt = INTERNAL_PLAN_PROMPT_TEMPLATE.format(
        blocksworld_plan=wrap_code(blocksworld_plan, 'pddl'),
        target_domain_nl=wrap_code(target_domain.get_domain_nl(), 'markdown'),
        target_domain_pddl=wrap_code(target_domain.get_domain_pddl(), 'pddl'),
        target_problem_nl=wrap_code(target_domain.get_task_nl(task_index), 'markdown'),
        target_problem_pddl=wrap_code(target_domain.get_task_pddl(task_index), 'pddl'),
    )
    conv_id, chat = gpt_client.make_new_chat(SYSTEM_MESSAGE)
    _, completion, _ = gpt_client.complete_one_chat(conv_id, prompt)
    original_plan = extract_code(completion, 'pddl')
    commmentless_plan = _remove_comments(original_plan)
    is_plan_valid, _ = pddl_env.validate_plan(
        target_domain.get_domain_pddl(), target_domain.get_task_pddl(task_index), commmentless_plan
    )
    aux = {'plan': commmentless_plan, 'original_plan': original_plan, 'task_index': task_index}
    print("Is Plan Valid? ", is_plan_valid)
    if is_plan_valid:
        return 1, aux
    return 0, aux


def run(cfg):
    logging.getLogger().handlers.clear()
    coloredlogs.install(level="INFO")
    logging.info(f"Running with config: {cfg.to_dict()}")
    assert cfg.context_domain_name != cfg.target_domain_name, "Context and target domains must be different."
    assert cfg.context_domain_name == 'blocksworld', "Context domain must be blocksworld"
    _seed_all(cfg.seed)
    run_exp_dir = os.path.join(cfg.exp_path, f"{cfg.log_prefix}/seed_{cfg.seed}")
    os.makedirs(run_exp_dir, exist_ok=True)
    summary_log_path = os.path.join(run_exp_dir, "summary_logs.json")
    if os.path.exists(summary_log_path):
        logging.warning(
            f"Summary log path already exists: {summary_log_path}, either delete it or change the prefix or seed"
        )
        exit(0)
    wandb_run = _config_wandb(cfg)

    gpt_client = GPTClient(GPTConfig(**cfg.gpt_args))
    target_domain = Domain(os.path.join(cfg.data_path, 'domains'), cfg.target_domain_name)
    pddl_env = PDDLEnv(**cfg.env_args)

    aux = {}
    task_results = []
    for task_index in range(cfg.max_tasks):
        task_result, task_aux = _evaluate_task(gpt_client, pddl_env, target_domain, task_index, cfg.use_cot)
        aux[f'task_{task_index}'] = task_aux
        task_results.append(task_result)
    correct_tasks_frac = np.mean(task_results)

    # Save and log the results
    summary_metrics = {
        'correct_tasks_score': correct_tasks_frac,
        'rw_score': -1,
        'rw_t_to_gen_frac': -1,
        'rw_gen_to_t_frac': -1,
        'used_prompt_tokens': gpt_client.used_prompt_tokens,
        'used_completion_tokens': gpt_client.used_completion_tokens,
        'cost_dollars': gpt_client.get_cost(),
    }
    wandb_run.summary.update(summary_metrics)
    gpt_client.save_chats(save_dir=os.path.join(run_exp_dir, "chats"))
    file_logger = get_file_logger(os.path.join(run_exp_dir, f"run.log"))
    # Save aux as file
    summary_log_dict = {
        'aux': aux, 'cfg': cfg.to_dict(), 'summary_metrics': summary_metrics,
    }
    with open(summary_log_path, 'w') as f:
        json.dump(summary_log_dict, f, indent=2)
    wandb_run.save(summary_log_path)
    file_logger.info(f"Used tokens: {gpt_client.used_tokens}")


def main(_):
    cfg = _CONFIG.value
    run(cfg)


def get_file_logger(log_path):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    return logger


def _seed_all(seed):
    """Sets the random seed"""
    np.random.seed(seed)
    random.seed(seed)


def _config_wandb(cfg):
    log_prefix = cfg.log_prefix
    debug = cfg.debug
    wandb_run = wandb.init(
        **cfg.wandb_args, mode="disabled" if debug else None,
        config=cfg.to_dict(), name=f"{log_prefix}/{cfg.run_id}"
    )
    wandb.config.update(cfg.to_dict())
    wandb.run.save()
    return wandb_run


if __name__ == '__main__':
    app.run(main)
