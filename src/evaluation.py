# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from dataclasses import dataclass
from typing import Union

from ml_collections import config_dict
from tqdm import tqdm

from domains import PDDLEnv
import error_messages
from pddl_utils import PDDLObj
from utils import extract_code, get_function_from_code, harmonic_mean


class PlanRatings:
    EMPTY_CODE = -6.0
    INVALID_MODIFICATION = -5.0
    PDDL_SANITY_ERROR = -4.0  # empty effect actions
    INVALID_DOMAIN = -3.0  # e.g., undefined predicates
    NO_PLAN = -1.0  # e.g., disconnected initial state and goal state
    # 0.0 <= rating <= 1.0: ratio of random walks that are executable
    SOLUTION_FOUND = 2.0


@dataclass
class PlanningEvaluation:
    rating: float
    error_msg: Union[str, None]
    new_pddl_obj: PDDLObj
    solution_found: bool = False


class PlanningEvaluator:
    def __init__(
            self, env: PDDLEnv, target_domain_pddl: str, target_problem_pddl: str, target_gen_problem_pddl: str,
            rw_feedback: bool, predicate_descriptor_py: str, exp_flags: config_dict.ConfigDict,
            bi_rw_feedback: bool = True,
    ):
        self.env = env
        self.rw_feedback = rw_feedback
        self.bi_rw_feedback = bi_rw_feedback
        self.target_domain_pddl = target_domain_pddl
        self.target_problem_pddl = target_problem_pddl
        self.target_gen_problem_pddl = target_gen_problem_pddl
        self.exp_flags = exp_flags
        self.predicate_descriptor_fn = get_function_from_code(predicate_descriptor_py, 'describe_predicate')

    def rate_domain_modification(self, cur_pddl_obj: PDDLObj, gpt_output: str) -> PlanningEvaluation:
        new_pddl_obj = cur_pddl_obj.copy_object()
        func_modification, err_msg = self._try_extracting_python_code(gpt_output)
        if err_msg is not None:
            return PlanningEvaluation(rating=PlanRatings.EMPTY_CODE, error_msg=err_msg, new_pddl_obj=new_pddl_obj)
        error_msg = new_pddl_obj.modify_domain(func_modification)
        if error_msg is not None:
            return PlanningEvaluation(
                rating=PlanRatings.INVALID_MODIFICATION, error_msg=error_msg, new_pddl_obj=new_pddl_obj
            )
        return self.rate_domain(new_pddl_obj)

    def rate_domain(self, pddl_obj) -> PlanningEvaluation:
        err_msg = pddl_obj.sanity_check_domain()
        gen_pddl_str = pddl_obj.to_str()
        if err_msg is not None:
            return PlanningEvaluation(rating=PlanRatings.PDDL_SANITY_ERROR, error_msg=err_msg, new_pddl_obj=pddl_obj)
        is_plan_valid, err_msg, aux_test = self._test_generated_pddl(
            gen_pddl_str, rw_feedback=self.rw_feedback
        )
        rw_rating, _, _ = self.evaluate_generated_domain_with_random_walks(gen_pddl_str)
        if is_plan_valid and abs(rw_rating - 1.0) < 1e-6:
            return PlanningEvaluation(
                rating=PlanRatings.SOLUTION_FOUND, error_msg=None, new_pddl_obj=pddl_obj, solution_found=True
            )

        return PlanningEvaluation(rw_rating, err_msg, pddl_obj)

    def _try_extracting_python_code(self, gpt_output: str):
        code_lang = 'python'
        try:
            generated_code = extract_code(gpt_output, lang=code_lang)
            err_msg = None
        except ValueError:
            logging.warning(f"Could not extract {code_lang} code from the GPT response:\n{gpt_output}")
            err_msg = "Your response does not contain any modification code."
            generated_code = ""
        return generated_code, err_msg

    def _test_generated_pddl(
            self, domain_gen_pddl, rw_feedback
    ):
        # generate a plan from generated pddl
        aux = {'all_plans': []}
        gen_plan, is_domain_valid, error_msg = self.env.search_plan(domain_gen_pddl, self.target_gen_problem_pddl)
        aux['all_plans'].append(self.env.plan_to_str(gen_plan))
        if gen_plan is None:
            if is_domain_valid and rw_feedback:
                return False, self._get_random_walk_feedback(domain_gen_pddl), aux
            else:
                logging.info("Issue with generating a plan." + error_msg)
                return False, error_msg, aux

        # validate the plan
        is_plan_valid, _ = self.env.validate_plan(self.target_domain_pddl, self.target_problem_pddl, gen_plan)
        if not is_plan_valid:
            logging.info("Plan generated, but it is not valid.")
        else:
            logging.info("Plan generated and it is valid.")
            aux['plan'] = self.env.plan_to_str(gen_plan)
            aux['gen_domain_pddl'] = domain_gen_pddl
        return is_plan_valid, None, aux

    def _get_random_walk_feedback(self, domain_gen_pddl: str):
        max_steps = 5
        max_random_walk_tries = 100
        for i in range(1, max_random_walk_tries + 1):
            target_to_gen_turn = self._is_target_to_gen_turn(i)
            if target_to_gen_turn:
                random_walk_plan, state_descs = self.env.get_random_walk_plan(
                    self.target_domain_pddl, self.target_problem_pddl,
                    predicate_descriptor_fn=self.predicate_descriptor_fn, max_steps=max_steps,
                )
                is_executable, exec_feedback = self.env.get_plan_execution_feedback(
                    domain_gen_pddl, self.target_gen_problem_pddl, random_walk_plan,
                    state_descs, predicate_descriptor_fn=None
                )
                error_prefix = error_messages.RANDOM_WALK_TARGET_TO_GEN_DESC
            else:
                random_walk_plan, _ = self.env.get_random_walk_plan(
                    domain_gen_pddl, self.target_gen_problem_pddl,
                    predicate_descriptor_fn=None, max_steps=max_steps
                )
                if len(random_walk_plan) == 0:
                    exec_feedback = error_messages.NO_EXECUTABLE_INITIAL_ACTION
                    logging.info(exec_feedback)
                    return exec_feedback
                is_executable, exec_feedback = self.env.get_plan_execution_feedback(
                    self.target_domain_pddl, self.target_problem_pddl, random_walk_plan,
                    state_descs=None, predicate_descriptor_fn=self.predicate_descriptor_fn
                )
                error_prefix = error_messages.RANDOM_WALK_GEN_TO_TARGET_DESC
            if is_executable:
                logging.info(
                    f"Found a random walk (target to gen turn {target_to_gen_turn}) plan with length {len(random_walk_plan)} and is executable. Skipping this plan."
                )
            else:
                logging.info(
                    f"Found a random walk (target to gen turn {target_to_gen_turn}) plan with length {len(random_walk_plan)} and is not executable. Using this plan."
                )
                return error_prefix + exec_feedback
            if i % 5 == 0:
                max_steps += 2
                logging.info(
                    f"Could not find an invalid random walk plan with {max_steps - 2} steps. Increasing the steps to {max_steps}."
                )
        logging.warning("All random walks are executable (probably a dead loop).")
        return None

    def evaluate_generated_domain_with_random_walks(
            self, domain_gen_pddl: str
    ):
        gen_plan, is_domain_valid, error_msg = self.env.search_plan(domain_gen_pddl, self.target_gen_problem_pddl)
        if not is_domain_valid:
            return PlanRatings.INVALID_DOMAIN, 0, 0
        exec_cnt, all_cnt = 0, 0
        t_to_gen_exec, gen_to_t_exec = 0, 0
        t_to_gen_all, gen_to_t_all = 0, 0
        for i in tqdm(range(100)):  # 100 random walks
            if self._is_target_to_gen_turn(i):
                max_steps = (t_to_gen_all % 10) + 1
                random_walk_plan, state_descs = self.env.get_random_walk_plan(
                    self.target_domain_pddl, self.target_problem_pddl,
                    predicate_descriptor_fn=self.predicate_descriptor_fn, max_steps=max_steps
                )
                # Empty plan should not exist!
                is_executable, _ = self.env.get_plan_execution_feedback(
                    domain_gen_pddl, self.target_gen_problem_pddl, random_walk_plan,
                    state_descs, predicate_descriptor_fn=None
                )
                t_to_gen_all += 1
                t_to_gen_exec += (is_executable is True)
            else:
                max_steps = (gen_to_t_all % 10) + 1
                random_walk_plan, _ = self.env.get_random_walk_plan(
                    domain_gen_pddl, self.target_gen_problem_pddl,
                    predicate_descriptor_fn=None, max_steps=max_steps
                )
                if len(random_walk_plan) == 0:
                    return PlanRatings.NO_PLAN, 0, 0
                is_executable, _ = self.env.get_plan_execution_feedback(
                    self.target_domain_pddl, self.target_problem_pddl, random_walk_plan,
                    state_descs=None, predicate_descriptor_fn=self.predicate_descriptor_fn
                )
                gen_to_t_all += 1
                gen_to_t_exec += (is_executable is True)
            all_cnt += 1
            exec_cnt += (is_executable is True)

        total_avg = harmonic_mean(t_to_gen_exec / t_to_gen_all, gen_to_t_exec / gen_to_t_all)
        return total_avg, t_to_gen_exec / t_to_gen_all, gen_to_t_exec / gen_to_t_all

    def _is_target_to_gen_turn(self, idx):  # Generate random walk based on target, test on generated pddl
        if not self.bi_rw_feedback:
            return False
        return idx % 2 == 0
