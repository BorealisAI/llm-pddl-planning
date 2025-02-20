# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import copy
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
from planning import evaluate_action_level_planning, PlanningStrategy, evaluate_planning_on_problem_candidates, \
    evaluate_all_tasks
import coloredlogs
import json
import wandb

from problem_domain_translation import translate_problems_given_one_task, \
    generate_exact_n_problem_translation_candidates

_CONFIG = config_flags.DEFINE_config_dict(
    'cfg',
    ConfigDict(dict(
        run_id=str(uuid.uuid4())[:8],
        debug=False,
        data_path='./data',
        exp_path='./experiments',
        log_prefix="test",
        seed=42,
        gpt_args=dict(
            api_key="your-openai-api-key",
            model_name='gpt-4-1106-preview',
        ),
        env_args=dict(
            fd_py_path='/path/to/downward/fast-downward.py',
            fd_search_time_limit=300,
            val_bin_path='/path/to/VAL/build/linux64/Release/bin/Validate',
        ),
        planning_strategy_args=dict(
            turns=4,  # How many turns to use for the conversation with LLM
            best_of_n=1,  # How many samples to generate from LLM and choose the best one
        ),
        problem_translation_args=dict(
            active=True,  # Whether to generate problem translation candidates, or use the target problem
            n_candidates=5,  # Number of candidates to generate
            one_domain_per_candidate=True,
            logprob_selection=False,
            # Whether to use logprob for selecting the best candidate among logprob_candidates candidates
            logprob_candidates=0,
            add_domain_proposal=False,  # Whether to add a domain proposal before the problem translation candidates
        ),
        max_tasks=10,  # Maximum number of tasks to evaluate
        context_domain_name='blocksworld', # This is strict, all the prompts are based on blocksworld
        target_domain_name='grippers',
        wandb_args=dict(
            project="llm-planning",
            entity="your-wandb-entity",
        ),
        exp_flags=dict(
        ),
    ))
)


def run(cfg):
    logging.getLogger().handlers.clear()
    coloredlogs.install(level="INFO")
    logging.info(f"Running with config: {cfg.to_dict()}")
    assert cfg.context_domain_name == 'blocksworld', "Context domain must be blocksworld"
    assert cfg.context_domain_name != cfg.target_domain_name, "Context and target domains must be different."
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
    context_domain = Domain(os.path.join(cfg.data_path, 'domains'), cfg.context_domain_name)
    target_domain = Domain(os.path.join(cfg.data_path, 'domains'), cfg.target_domain_name)
    pddl_env = PDDLEnv(**cfg.env_args)
    planning_strategy = PlanningStrategy(**cfg.planning_strategy_args)
    first_task_index = 0

    # Generate problem translation candidates without any ground truth
    target_problem_list = [target_domain.get_task_pddl(i) for i in range(cfg.max_tasks)]
    if cfg.problem_translation_args.active:
        problem_translation_candidates = generate_exact_n_problem_translation_candidates(
            n_candidates=cfg.problem_translation_args.n_candidates,
            gpt_client=gpt_client,
            context_domain=context_domain,
            target_domain=target_domain,
            task_index=first_task_index,
            logprob_selection=cfg.problem_translation_args.logprob_selection,
            logprob_candidates=cfg.problem_translation_args.logprob_candidates,
            add_domain_proposal=cfg.problem_translation_args.add_domain_proposal,
            one_domain_per_candidate=cfg.problem_translation_args.one_domain_per_candidate,
            exp_flags=cfg.exp_flags
        )
        logging.info(f"Generated {len(problem_translation_candidates)} problem translation candidates.")
        all_ratings, (
            best_rating, best_generated_pddl, best_generated_problem_pddl
        ), aux = evaluate_planning_on_problem_candidates(
            problem_translation_candidates=problem_translation_candidates,
            context_domain=context_domain,
            target_domain=target_domain,
            gpt_client=gpt_client,
            pddl_env=pddl_env,
            planning_strategy=planning_strategy,
            task_index=first_task_index,
            exp_flags=cfg.exp_flags
        )
        other_task_nls = [target_domain.get_task_nl(i) for i in range(1, cfg.max_tasks)]
        other_task_templates = [target_domain.get_task_template(i) for i in range(1, cfg.max_tasks)]
        gen_problem_list = [best_generated_problem_pddl] + translate_problems_given_one_task(
            gpt_client=gpt_client, domain_pddl=best_generated_pddl, domain_nl=target_domain.get_domain_nl(),
            context_problem_pddl=best_generated_problem_pddl,
            context_problem_nl=target_domain.get_task_nl(first_task_index),
            context_problem_template_pddl=target_domain.get_task_template(first_task_index),
            target_problem_nls=other_task_nls,
            target_problem_templates=other_task_templates
        )
        logging.info(f"All ratings: {all_ratings}")
    # Assume the target problem is given
    else:
        problem_translation_candidates = []
        target_problem_pddl, _, _ = target_domain.get_task(first_task_index)
        best_rating, best_generated_pddl, aux = evaluate_action_level_planning(
            context_domain=context_domain,
            target_domain=target_domain,
            target_gen_problem_pddl=target_problem_pddl,  # Use the target problem as the initial problem
            gpt_client=gpt_client,
            pddl_env=pddl_env,
            planning_strategy=planning_strategy,
            task_index=first_task_index,
            exp_flags=cfg.exp_flags
        )
        gen_problem_list = copy.deepcopy(target_problem_list)

    logging.info(f"Best generated domain: {best_generated_pddl}")
    correct_tasks_frac, (correct_tasks_rw_score, rw_t_to_gen_frac, rw_gen_to_t_frac) = evaluate_all_tasks(
        pddl_env=pddl_env,
        target_domain_pddl=target_domain.get_domain_pddl(),
        target_domain_problem_pddls=target_problem_list,
        target_gen_domain_pddl=best_generated_pddl,
        target_gen_problem_pddls=gen_problem_list,
        exp_flags=cfg.exp_flags,
    )

    # Save and log the results
    summary_metrics = {
        'correct_tasks_score': correct_tasks_frac,
        'rw_score': correct_tasks_rw_score,
        'rw_t_to_gen_frac': rw_t_to_gen_frac,
        'rw_gen_to_t_frac': rw_gen_to_t_frac,
        'used_prompt_tokens': gpt_client.used_prompt_tokens,
        'used_completion_tokens': gpt_client.used_completion_tokens,
        'cost_dollars': gpt_client.get_cost(),
    }
    wandb_run.summary.update(summary_metrics)
    gpt_client.save_chats(save_dir=os.path.join(run_exp_dir, "chats"))
    file_logger = get_file_logger(os.path.join(run_exp_dir, f"run.log"))
    # Save aux as file
    summary_log_dict = {
        'aux': aux,
        'cfg': cfg.to_dict(),
        'summary_metrics': summary_metrics,
        'gen_problem_list': gen_problem_list,
        'task_0_problem_translation_candidates': problem_translation_candidates,
        'best_gen_domain_pddl': best_generated_pddl,

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
