# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import multiprocessing

from absl import app
import os

import sys

from tqdm import tqdm

sys.path.append('../')

from ml_collections import ConfigDict, config_flags
from domains import Domain, PDDLEnv
from pddl_utils import PDDLObj
import numpy as np
import uuid

from planning import evaluate_all_tasks_random_walk

DOMAINS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, os.pardir, 'data', 'domains')
_CONFIG = config_flags.DEFINE_config_dict(
    'cfg',
    ConfigDict(dict(
        run_id=str(uuid.uuid4())[:8],
        debug=False,
        seed=43,
        mode='rw_analysis',  # 'plan_inv', 'rw_analysis'
        exp_path='./experiments',
        n_gen_per_diff=100,
        max_diff=10,
        n_tasks=3,
        env_args=dict(
            fd_py_path='/path/to/planning_library.py',
            fd_search_time_limit=300,
            val_bin_path='/path/to/VAL/build/linux64/Release/bin/Validate',
            fd_alias=PDDLEnv.SUB_OPTIMAL_ALIAS,
        ),
        gpt_args=dict(
            api_key="your-openai-api-key",
            model_name='gpt-4-1106-preview',
        ),
        exp_flags=dict(
        ),
        domain_name='barman',
    ))
)


def _get_operands(precond_effect):
    if hasattr(precond_effect, '_operands'):
        return precond_effect._operands
    return [precond_effect]


def compare_domain_actions(domain, pddl1, pddl2):
    def compare_clause_list(lst1, lst2):
        clause_strs1 = set({str(clause) for clause in lst1})
        clause_strs2 = set({str(clause) for clause in lst2})
        return len(clause_strs1.symmetric_difference(clause_strs2))

    n_diff = 0
    pddl_obj1 = PDDLObj.from_pddl_str(pddl1, domain.get_domain_template_pddl())
    pddl_obj2 = PDDLObj.from_pddl_str(pddl2, domain.get_domain_template_pddl())
    action_names = {action.name for action in pddl_obj1.domain_pddl.actions}
    for action_name in action_names:
        action1 = pddl_obj1.get_action_by_name(action_name)
        action2 = pddl_obj2.get_action_by_name(action_name)
        n_diff += compare_clause_list(_get_operands(action1._precondition), _get_operands(action2._precondition))
        n_diff += compare_clause_list(_get_operands(action1._effect), _get_operands(action2._effect))
    return n_diff


def create_random_domain_removed(domain: Domain, total_remove):
    pddl_obj = PDDLObj.from_pddl_str(domain.get_domain_pddl(), domain.get_domain_template_pddl())
    remove_fns = []

    def _get_remove_fn(lst, element):
        def remove_clause():
            if len(lst) > 1 and element in lst:
                lst.remove(element)
                return 1
            return 0

        return remove_clause

    for action in pddl_obj.domain_pddl.actions:
        for lst in [_get_operands(action._precondition), _get_operands(action._effect)]:
            for i in range(len(lst)):
                remove_fns.append(_get_remove_fn(lst, lst[i]))
    max_removable = len(remove_fns) - 2 * len(pddl_obj.domain_pddl.actions)
    assert max_removable >= total_remove, f"Cannot remove {total_remove} clauses from the domain"
    n_removed = 0
    while n_removed < total_remove:
        idx = np.random.randint(len(remove_fns))
        n_removed += remove_fns[idx]()
    return pddl_obj.to_str()


def create_random_pair_removed(domain: Domain, total_remove, target_diff):
    pddl_objs = [PDDLObj.from_pddl_str(
        domain.get_domain_pddl(), domain.get_domain_template_pddl()
    ) for _ in range(2)]
    totals = [total_remove, total_remove + (total_remove - target_diff) % 2]

    def _get_remove_fn(lst, element):
        def remove_clause(do_remove):
            if len(lst) > 1 and element in lst:
                if do_remove:
                    lst.remove(element)
                return 1
            return 0

        return remove_clause

    remove_fn_list = []
    for pddl_obj in pddl_objs:
        remove_fns = []
        for action in pddl_obj.domain_pddl.actions:
            for lst in [_get_operands(action._precondition), _get_operands(action._effect)]:
                for i in range(len(lst)):
                    remove_fns.append(_get_remove_fn(lst, lst[i]))
        remove_fn_list.append(remove_fns)
    max_removable = len(remove_fn_list[0]) - 2 * len(pddl_objs[0].domain_pddl.actions)
    assert max_removable >= 2 * target_diff, f"Cannot remove {target_diff} clauses from the domain"

    list_perm = np.random.permutation(len(remove_fn_list[0]))
    ptr = 0
    n_commons = (totals[0] + totals[1] - target_diff) // 2
    totals[0] -= n_commons
    totals[1] -= n_commons
    while ptr < len(list_perm):
        if n_commons:
            if remove_fn_list[0][list_perm[ptr]](False) and remove_fn_list[1][list_perm[ptr]](False):
                remove_fn_list[0][list_perm[ptr]](True)
                remove_fn_list[1][list_perm[ptr]](True)
                n_commons -= 1
        elif totals[0] > 0:
            if remove_fn_list[0][list_perm[ptr]](True):
                totals[0] -= 1
        elif totals[1] > 0:
            if remove_fn_list[1][list_perm[ptr]](True):
                totals[1] -= 1
        else:
            break
        ptr += 1
    if ptr == len(list_perm):
        raise ValueError("Cannot remove the target number of clauses")
    pddl_strs = [pddl_obj.to_str() for pddl_obj in pddl_objs]
    np.random.shuffle(pddl_strs)
    return pddl_strs[0], pddl_strs[1]


def compute_rw_score(pddl_env, domain, pddl1, pddl2, n_tasks, exp_flags):
    problem_list = [domain.get_task_pddl(i) for i in range(n_tasks)]
    final_score, t_to_gen_frac, gen_to_t_frac = evaluate_all_tasks_random_walk(
        pddl_env=pddl_env,
        target_domain_pddl=pddl1,
        target_domain_problem_pddls=problem_list,
        target_gen_domain_pddl=pddl2,
        target_gen_problem_pddls=problem_list,
        exp_flags=exp_flags,
    )
    return final_score, t_to_gen_frac, gen_to_t_frac


def compute_rw_score_diff(cfg, diff_val, q):
    pddl_env = PDDLEnv(**cfg.env_args)
    domain = Domain(DOMAINS_PATH, cfg.domain_name)
    exp_flags = cfg.exp_flags
    final_results = []
    for i in range(cfg.n_gen_per_diff):
        pddl1, pddl2 = create_random_pair_removed(domain, cfg.max_diff // 2 + 1, diff_val)
        n_diff = compare_domain_actions(domain, pddl1, pddl2)
        assert n_diff == diff_val, f"n_diff: {n_diff}, diff_val: {diff_val}"
        rw_score, t_to_gen_frac, gen_to_t_frac = compute_rw_score(
            pddl_env, domain, pddl1, pddl2, cfg.n_tasks, exp_flags
        )
        print(
            f"Sample {i}: n_diff: {n_diff}, rw_score: {rw_score}, t_to_gen_frac: {t_to_gen_frac}, gen_to_t_frac: {gen_to_t_frac}"
        )
        final_results.append((n_diff, rw_score, t_to_gen_frac, gen_to_t_frac))
    q.put(final_results)


def run_rw_analysis(cfg):
    domain_name = cfg.domain_name
    final_results = []

    q = multiprocessing.Queue()
    processes = []
    for diff_val in range(cfg.max_diff + 1):
        p = multiprocessing.Process(target=compute_rw_score_diff, args=(cfg, diff_val, q))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    for _ in processes:
        final_results.extend(q.get(timeout=1.0))
    # Save the results
    save_dir = os.path.join(cfg.exp_path, 'rw_analysis3')
    os.makedirs(save_dir, exist_ok=True)
    np.save(os.path.join(save_dir, f'{domain_name}_{cfg.run_id}.npy'), np.array(final_results))


def compute_plan_inv(cfg, diff_val, q):
    pddl_env = PDDLEnv(**cfg.env_args)
    domain = Domain(DOMAINS_PATH, cfg.domain_name)
    results = []
    print(f"Computing plan inv for diff_val: {diff_val}")
    for i in tqdm(range(cfg.n_gen_per_diff)):
        pddl_gen = create_random_domain_removed(domain, diff_val)
        assert compare_domain_actions(domain, domain.get_domain_pddl(), pddl_gen) == diff_val
        tasks_solved = 0
        for task_index in range(cfg.n_tasks):
            pddl_problem = domain.get_task_pddl(task_index)
            plan, _, _ = pddl_env.search_plan(pddl_gen, pddl_problem)
            sol_found = 1 if plan is not None else 0
            tasks_solved += sol_found
        results.append((diff_val, tasks_solved / cfg.n_tasks))
    q.put(results)


def run_plan_inv(cfg):
    q = multiprocessing.Queue()
    processes = []
    for diff_val in range(cfg.max_diff + 1):
        p = multiprocessing.Process(target=compute_plan_inv, args=(cfg, diff_val, q))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    final_results = []
    for _ in processes:
        final_results.extend(q.get(timeout=1.0))
    save_dir = os.path.join(cfg.exp_path, 'plan_inv')
    os.makedirs(save_dir, exist_ok=True)
    np.save(os.path.join(save_dir, f'{cfg.domain_name}_{cfg.run_id}.npy'), np.array(final_results))


def main(_):
    cfg = _CONFIG.value
    np.random.seed(cfg.seed)
    if cfg.mode == 'rw_analysis':
        run_rw_analysis(cfg)
    elif cfg.mode == 'plan_inv':
        run_plan_inv(cfg)
    else:
        raise ValueError(f"Unknown mode: {cfg.mode}")


if __name__ == '__main__':
    app.run(main)
