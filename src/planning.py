# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

from typing import List

from ml_collections import ConfigDict

from domains import Domain, PDDLEnv
from evaluation import PlanningEvaluator, PlanRatings
from gpt_client import GPTClient
from pddl_utils import PDDLObj
from utils import wrap_code, mean, harmonic_mean
import prompts
from dataclasses import dataclass
import logging


@dataclass
class PlanningStrategy:
    turns: int = 5
    best_of_n: int = 1
    rw_feedback: bool = True
    bi_rw_feedback: bool = True


STOCHASTIC_TEMPERATURE = 0.7
DETERMINISTIC_TEMPERATURE = 0.0

SYSTEM_MESSAGE = """You are a helpful assistant, skilled in producing Planning Domain Definition Language (PDDL) code of environments.
You are only allowed to modify the PDDL code using the following two python function interfaces:

```python
add_or_update_predicates(predicates: List[str])
modify_action(action_name: str, new_preconditions: List[str], new_effects: List[str])
```
"""


def evaluate_planning_on_problem_candidates(
        problem_translation_candidates: List[str],
        context_domain: Domain,
        target_domain: Domain,
        gpt_client: GPTClient,
        pddl_env: PDDLEnv,
        planning_strategy: PlanningStrategy,
        task_index: int,
        exp_flags: ConfigDict
):
    all_ratings = []
    best_best_rating, return_params = float('-inf'), None
    all_aux = {'problem_candidates_aux': [], 'best_candidate_idx': -1}
    for i, candidate in enumerate(problem_translation_candidates):
        logging.info(f"Evaluating candidate {i + 1}/{len(problem_translation_candidates)}")
        best_rating, best_generated_pddl, aux = evaluate_action_level_planning(
            context_domain=context_domain,
            target_domain=target_domain,
            target_gen_problem_pddl=candidate,
            gpt_client=gpt_client,
            pddl_env=pddl_env,
            planning_strategy=planning_strategy,
            task_index=task_index,
            exp_flags=exp_flags
        )
        aux['gen_problem_pddl'] = candidate
        logging.info(f"Best rating for candidate {i + 1}/{len(problem_translation_candidates)}: {best_rating}")
        logging.info(f"Candidate {i + 1}/{len(problem_translation_candidates)}: {candidate}")
        logging.info(
            f"Best generated PDDL for candidate {i + 1}/{len(problem_translation_candidates)}: {best_generated_pddl}")
        if best_rating > best_best_rating:
            best_best_rating = best_rating
            return_params = (best_rating, best_generated_pddl, candidate)
            all_aux['best_candidate_idx'] = i

        all_aux['problem_candidates_aux'].append(aux)
        all_ratings.append(best_rating)
        if best_rating == PlanRatings.SOLUTION_FOUND:
            logging.info(f"Solution found for candidate {i + 1}/{len(problem_translation_candidates)}")
            logging.info(f"Stopping early since a solution was found.")
            break
    return all_ratings, return_params, all_aux


def evaluate_action_level_planning(
        context_domain: Domain,
        target_domain: Domain,
        target_gen_problem_pddl: str,
        gpt_client: GPTClient,
        pddl_env: PDDLEnv,
        planning_strategy: PlanningStrategy,
        task_index: int,
        exp_flags: ConfigDict
):
    target_domain_nl_wrapped = wrap_code(target_domain.get_domain_nl(), lang='markdown')
    target_domain_pddl = target_domain.get_domain_pddl()
    target_domain_template_pddl = target_domain.get_domain_template_pddl()
    target_domain_template_pddl_wrapped = wrap_code(target_domain_template_pddl, lang='pddl')
    target_problem_pddl, _, _ = target_domain.get_task(task_index)
    target_gen_problem_pddl_wrapped = wrap_code(target_gen_problem_pddl, lang='pddl')

    assert context_domain.name == 'blocksworld', "Improved one-shot prompt is only supported for blocksworld."
    init_prompt = prompts.ONE_SHOT_INIT_PROMPT_TEMPLATE.format(
        context_domain_name=context_domain.name,
        target_domain_name=target_domain.name,
        context_shot_example=prompts.BLOCKS_WORLD_EXAMPLE,
        target_domain_nl=target_domain_nl_wrapped,
        target_domain_template_pddl=target_domain_template_pddl_wrapped,
        target_problem_pddl=target_gen_problem_pddl_wrapped
    )

    pddl_obj = PDDLObj.from_pddl_str(target_domain_template_pddl, domain_pddl_template=target_domain_template_pddl)
    planning_evaluator = PlanningEvaluator(
        pddl_env, target_domain_pddl, target_problem_pddl, target_gen_problem_pddl,
        planning_strategy.rw_feedback, target_domain.get_domain_predicate_descriptor(),
        exp_flags=exp_flags, bi_rw_feedback=planning_strategy.bi_rw_feedback
    )
    turns = planning_strategy.turns
    best_rating, best_generated_pddl, best_conv_id = float('-inf'), "", ""
    aux = {}
    conv_id, _ = gpt_client.make_new_chat(system_message=SYSTEM_MESSAGE)
    user_input = init_prompt
    for step in range(1, turns + 1):
        old_conv_id = conv_id
        conv_id, planning_evaluation, response_aux = _get_best_of_n_responses(
            gpt_client, planning_evaluator, pddl_obj, conv_id, user_input, planning_strategy.best_of_n
        )
        pddl_obj = planning_evaluation.new_pddl_obj
        new_domain_pddl = pddl_obj.to_str()
        err_msg = planning_evaluation.error_msg
        rating = planning_evaluation.rating

        if err_msg is not None and len(err_msg) > 0:
            maybe_error = f"The environment returned the following error:\n\n{err_msg}\n\n"
        else:
            maybe_error = ""
        logging.info(f"Generated Domain Rating: {rating}")
        if rating > best_rating:
            best_rating = rating
            best_generated_pddl = new_domain_pddl
            best_conv_id = conv_id
        if planning_evaluation.solution_found:
            break
        user_input = f"Incorrect. {maybe_error}Please reason about the issue with your generated code. The current domain pddl is as follows:\n\n{wrap_code(new_domain_pddl, lang='pddl')}\n\nIn your response, please generate a new code to fix the issue."

    aux.update({
        "best_conv_id": best_conv_id,
        "best_rating": best_rating,
        "best_generated_domain_pddl": best_generated_pddl,
    })
    logging.info(f"Best rating: {best_rating} with conversation id: {best_conv_id}")
    return best_rating, best_generated_pddl, aux


def evaluate_all_tasks(
        pddl_env: PDDLEnv,
        target_domain_pddl: str,
        target_domain_problem_pddls: List[str],
        target_gen_domain_pddl: str,
        target_gen_problem_pddls: List[str],
        exp_flags: ConfigDict,
):
    args = (
        pddl_env, target_domain_pddl, target_domain_problem_pddls, target_gen_domain_pddl, target_gen_problem_pddls,
        exp_flags
    )
    return _evaluate_all_tasks_plan_gen(*args), evaluate_all_tasks_random_walk(*args)


def _evaluate_all_tasks_plan_gen(
        pddl_env: PDDLEnv,
        target_domain_pddl: str,
        target_domain_problem_pddls: List[str],
        target_gen_domain_pddl: str,
        target_gen_problem_pddls: List[str],
        exp_flags: ConfigDict,
):
    assert len(target_domain_problem_pddls) == len(target_gen_problem_pddls)
    n_valids = 0
    for t_gen_p, t_gt_p in zip(target_gen_problem_pddls, target_domain_problem_pddls):
        gen_plan, is_domain_valid, error_msg = pddl_env.search_plan(target_gen_domain_pddl, t_gen_p)
        if gen_plan is not None:
            is_plan_valid, _ = pddl_env.validate_plan(target_domain_pddl, t_gt_p, gen_plan)
            if is_plan_valid:
                n_valids += 1
    return n_valids / len(target_domain_problem_pddls)


def evaluate_all_tasks_random_walk(
        pddl_env: PDDLEnv,
        target_domain_pddl: str,
        target_domain_problem_pddls: List[str],
        target_gen_domain_pddl: str,
        target_gen_problem_pddls: List[str],
        exp_flags: ConfigDict,
):
    assert len(target_domain_problem_pddls) == len(target_gen_problem_pddls)
    t_to_gen_scores, gen_to_t_score = [], []
    dummy_pred_desc = """def describe_predicate(*args, **kwargs): return ("", "")"""
    for t_gen_p, t_gt_p in zip(target_gen_problem_pddls, target_domain_problem_pddls):
        task_evaluator = PlanningEvaluator(
            env=pddl_env, target_domain_pddl=target_domain_pddl, target_problem_pddl=t_gt_p,
            target_gen_problem_pddl=t_gen_p, rw_feedback=True, predicate_descriptor_py=dummy_pred_desc,
            exp_flags=exp_flags, bi_rw_feedback=True,
        )
        _, t_to_gen_frac, gen_to_t_frac = task_evaluator.evaluate_generated_domain_with_random_walks(
            target_gen_domain_pddl
        )
        t_to_gen_scores.append(t_to_gen_frac)
        gen_to_t_score.append(gen_to_t_frac)
    t_to_gen_frac = mean(t_to_gen_scores)
    gen_to_t_frac = mean(gen_to_t_score)
    final_score = harmonic_mean(t_to_gen_frac, gen_to_t_frac)
    logging.info(f"Random walk scores on all tasks: {final_score}")

    return final_score, t_to_gen_frac, gen_to_t_frac


def _get_best_of_n_responses(gpt_client, planning_evaluator, pddl_obj, conv_id, user_input, n_completions):
    if n_completions == 1:
        best_conv_id, gpt_output, _ = gpt_client.complete_one_chat(conv_id, user_input)
        planning_evaluation = planning_evaluator.rate_domain_modification(
            pddl_obj, gpt_output
        )
        return best_conv_id, planning_evaluation, {"all_conv_ids": [best_conv_id],
                                                   "all_ratings": [planning_evaluation.rating]}
    else:
        conv_ids, gpt_outputs, _ = gpt_client.complete_n_chats(
            conv_id, user_input, n_completions, temp=STOCHASTIC_TEMPERATURE
        )
        all_evaluations = []
        best_evaluation = None
        best_conv_id = None
        for i in range(n_completions):
            gpt_output = gpt_outputs[i]
            planning_evaluation = planning_evaluator.rate_domain_modification(
                pddl_obj, gpt_output
            )
            all_evaluations.append(planning_evaluation)
            logging.info(f"Rating for completion {i}: {planning_evaluation.rating}")
            if best_evaluation is None or planning_evaluation.rating > best_evaluation.rating:
                best_evaluation = planning_evaluation
                best_conv_id = conv_ids[i]
        return best_conv_id, best_evaluation, {"all_conv_ids": conv_ids,
                                               "all_ratings": [e.rating for e in all_evaluations]}
