# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import numpy as np

from pddl_utils import get_problem_pddl_empty_goal, extract_atom_arguments
from utils import postprocess, safe_function_execute
import subprocess
from utils import get_random_temp_file_name, read_and_remove_file, as_file
import logging
from typing import List
import fast_downward
from fast_downward import Atom, Operator, close_lib

DOMAIN_NAMES = [
    "barman", "blocksworld", "floortile", "grippers", "grippers-ood", "storage",
    "termes", "tyreworld", "manipulation", "childsnack-opt14-strips",
    'depot', 'driverlog', 'hiking-agl14-strips', 'logistics00', 'miconic', 'movie', 'mprime', 'openstacks',
    'parking-opt11-strips', 'rovers', 'satellite', 'scanalyzer-08-strips', 'trucks', 'zenotravel',
]


class Domain:
    def __init__(self, base_path, name):
        assert name in DOMAIN_NAMES
        self.name = name
        self.domain_dir = os.path.join(base_path, name)
        self.tasks = []  # should be list of tuples like (descritpion, ground_truth_pddl)

        self.grab_tasks()

    def grab_tasks(self):
        path = self.domain_dir
        p_pddls = []
        for i in range(1, 100):
            pddl = f"p{i:02d}.pddl"
            if os.path.isfile(os.path.join(path, pddl)):
                p_pddls.append(pddl)
        sorted_pddls = sorted(p_pddls)
        self.tasks = sorted_pddls

    def __len__(self):
        return len(self.tasks)

    def get_task_suffix(self, i):
        nl, pddl = self.tasks[i]
        return f"{self.name}/{pddl}"

    def get_task_file(self, i):
        pddl = self.tasks[i]
        return os.path.join(self.domain_dir, pddl)

    def get_domain_predicate_descriptor(self):
        with open(os.path.join(self.domain_dir, "predicate_descriptor.py"), 'r') as f:
            return f.read()

    def get_task(self, i):
        pddl_f = self.get_task_file(i)
        with open(pddl_f, 'r') as f:
            pddl = f.read()
        with open(pddl_f.replace(".pddl", ".nl"), 'r') as f:
            nl = f.read()
        with open(pddl_f.replace(".pddl", "_template.pddl"), 'r') as f:
            template = f.read()
        return postprocess(pddl), postprocess(nl), postprocess(template)

    def get_task_nl(self, i):
        return self.get_task(i)[1]

    def get_domain_pddl(self):
        domain_pddl_f = self.get_domain_pddl_file()
        with open(domain_pddl_f, 'r') as f:
            domain_pddl = f.read()
        return postprocess(domain_pddl)

    def get_domain_template_pddl(self):
        domain_pddl_path = os.path.join(self.domain_dir, "domain_template.pddl")
        with open(domain_pddl_path, 'r') as f:
            domain_pddl = f.read()
        return postprocess(domain_pddl)

    def get_domain_pddl_file(self):
        domain_pddl_f = os.path.join(self.domain_dir, "domain.pddl")
        return domain_pddl_f

    def get_domain_nl(self):
        domain_nl_f = self.get_domain_nl_file()
        try:
            with open(domain_nl_f, 'r') as f:
                domain_nl = f.read()
        except:
            raise Exception(f"Could not read domain nl file: {domain_nl_f}")
        return postprocess(domain_nl)

    def get_task_pddl(self, i):
        return self.get_task(i)[0]

    def get_domain_nl_file(self):
        domain_name = "domain.nl"
        domain_nl_f = os.path.join(self.domain_dir, domain_name)
        return domain_nl_f

    def get_task_template(self, i):
        return self.get_task(i)[2]


class PDDLEnv:
    OPTIMAL_ALIAS = "seq-opt-fdss-1"
    SUB_OPTIMAL_ALIAS = "lama-first"

    def __init__(
            self, fd_py_path: str, val_bin_path: str, fd_search_time_limit: int, fd_alias: str = SUB_OPTIMAL_ALIAS
    ) -> None:
        self.fd_py_path = fd_py_path
        self.fd_search_time_limit = fd_search_time_limit
        self.val_bin_path = val_bin_path
        self.fd_alias = fd_alias

    def search_plan(self, domain_pddl: str, problem_pddl: str):
        domain_pddl_path = as_file(domain_pddl)
        problem_pddl_path = as_file(problem_pddl)
        temp_plan_path = get_random_temp_file_name()
        temp_sas_path = get_random_temp_file_name()
        output = subprocess.run(
            [
                "python3",
                self.fd_py_path,
                "--alias",
                self.fd_alias,
                "--search-time-limit",
                f"{self.fd_search_time_limit}",
                "--plan-file",
                temp_plan_path,
                "--sas-file",
                temp_sas_path,
                domain_pddl_path,
                problem_pddl_path
            ],
            capture_output=True,
            text=True,
            universal_newlines=True,
        )

        search_output = output.stdout
        search_error = output.stderr
        read_and_remove_file(domain_pddl_path)
        read_and_remove_file(problem_pddl_path)
        if "Solution found." in search_output:
            plan = postprocess(read_and_remove_file(temp_plan_path))
            return plan, True, "Solution found."
        elif "Search stopped without finding a solution." in search_output:
            return None, True, "Generated PDDL domain is valid, but plan search stopped without finding a solution."
        elif "Time limit has been reached." in search_output:
            return None, True, "Generated PDDL domain is valid, but search Time limit has been reached."
        else:
            return None, False, search_error

    def validate_plan(self, domain_pddl: str, problem_pddl: str, plan: str):
        domain_pddl_path = as_file(domain_pddl)
        problem_pddl_path = as_file(problem_pddl)
        plan_file = as_file(plan)
        val_output = subprocess.run(
            [
                self.val_bin_path,
                "-v",
                domain_pddl_path,
                problem_pddl_path,
                plan_file
            ],
            capture_output=True,
            text=True,
            universal_newlines=True,
        )
        read_and_remove_file(domain_pddl_path)
        read_and_remove_file(problem_pddl_path)
        is_valid, val_message = self._parse_val_output(val_output.stdout)
        return is_valid, val_message

    def get_random_walk_plan(
            self, domain_pddl: str, problem_pddl: str, predicate_descriptor_fn, max_steps: int
    ):
        seed = np.random.randint(2 ** 32 - 1)
        while True:
            func_result = safe_function_execute(
                self._get_random_walk_plan, domain_pddl, problem_pddl, predicate_descriptor_fn, max_steps, seed
            )
            if func_result is not None:
                plan, state_descs = func_result
                return plan, state_descs

    def _get_random_walk_plan(
            self, domain_pddl: str, problem_pddl: str, predicate_descriptor_fn, max_steps: int, seed
    ):
        rng = np.random.default_rng(seed)
        problem_pddl = get_problem_pddl_empty_goal(problem_pddl)
        lib = fast_downward.load_lib()
        task, sas = fast_downward.pddl2sas(domain_pddl, problem_pddl)
        lib.load_sas(sas.encode('utf-8'))

        plan, state_descs = [], []
        if predicate_descriptor_fn is not None:
            state_descs.append(self._get_state_natural_language(lib, predicate_descriptor_fn, action_name=None))
        for _ in range(max_steps):
            available_actions = self._get_applicable_actions(lib)
            available_action_names = list(available_actions.keys())
            if len(available_action_names) == 0:
                break
            action_name = rng.choice(available_action_names)
            plan.append(action_name)
            action = available_actions[action_name]
            if predicate_descriptor_fn is not None:
                state_descs.append(self._get_state_natural_language(lib, predicate_descriptor_fn, action_name))
            _ = self._apply_action(lib, action)
        close_lib(lib)
        return plan, state_descs

    def get_plan_execution_feedback(
            self, domain_pddl: str, problem_pddl: str, plan: List[str], state_descs,
            predicate_descriptor_fn
    ):
        while True:
            feedback = safe_function_execute(
                self._get_plan_execution_feedback, domain_pddl, problem_pddl, plan, state_descs, predicate_descriptor_fn
            )
            if feedback is not None:
                return feedback

    def _get_plan_execution_feedback(
            self, domain_pddl: str, problem_pddl: str, plan: List[str], state_descs: List[str], predicate_descriptor_fn
    ):
        assert state_descs is not None or predicate_descriptor_fn is not None, "Either state_descs or predicate_descriptor_fn must be provided."
        problem_pddl = get_problem_pddl_empty_goal(problem_pddl)
        lib = fast_downward.load_lib()
        task, sas = fast_downward.pddl2sas(domain_pddl, problem_pddl)
        lib.load_sas(sas.encode('utf-8'))
        plan_so_far = []
        feedback = "The plan is executable."
        executable = True
        for action_name in plan:
            plan_so_far.append(f"({action_name})")
            available_actions = self._get_applicable_actions(lib)
            available_action_names = list(available_actions.keys())
            if action_name not in available_action_names:
                if state_descs is not None:
                    state_desc_str = state_descs[len(plan_so_far) - 1]
                    if len(state_desc_str) > 1000:
                        state_desc_str = state_desc_str[:1000] + "..."
                        logging.warning(f"State description is too long: {state_desc_str}, truncating.")
                    feedback = (f"Error when executing the action ({action_name}).\n"
                                f"Current state: {state_desc_str}\n"
                                f"This action is not executable on the environment.")
                elif predicate_descriptor_fn is not None:
                    feedback = (f"Error when executing the action ({action_name}).\n"
                                f"Current state: {self._get_state_natural_language(lib, predicate_descriptor_fn, action_name)}\n"
                                f"This action is executable on the environment, but your generated environment recognizes this as an illegal action.")
                else:
                    feedback = f"Error when executing the action ({action_name}). This action is not executable on the environment."
                executable = False
                break
            else:
                action = available_actions[action_name]
                _ = self._apply_action(lib, action)

        exec_description = f"Executing the following actions sequentially on the environment:\n{self.plan_to_str(plan_so_far)}\n\nResult: "
        close_lib(lib)
        return executable, f"{exec_description}{feedback}"

    def _get_applicable_actions(self, lib) -> dict:
        operator_count = lib.get_applicable_operators_count()
        operators = (Operator * operator_count)()
        lib.get_applicable_operators(operators)
        return {op.name: op for op in operators}

    def _apply_action(self, lib, action):
        effects = (Atom * action.nb_effect_atoms)()
        lib.apply_operator(action.id, effects)
        return effects

    def _get_state_natural_language(self, lib, predicate_desc_fn, action_name=None):
        if action_name is None:
            relevant_facts = self._get_all_atom_facts(lib)
        else:
            relevant_facts = self._get_relevant_atom_facts(lib, action_name)

        fact_descriptions = []
        for i in range(len(relevant_facts)):
            is_not, atom_name, fact_args = relevant_facts[i]
            fact_descriptions.append(
                predicate_desc_fn(atom_name, fact_args)[1 if is_not else 0]
            )  # 0 for positive, 1 for negative
        return " ".join(fact_descriptions)

    def _get_relevant_atom_facts(self, lib, action_name):
        action_params = action_name.split()[1:]
        relevant_facts = []
        for (is_not, atom_name, fact_args) in self._get_all_atom_facts(lib):
            if len(fact_args) == 0:
                relevant_facts.append((is_not, atom_name, fact_args))
            if set(fact_args).issubset(set(action_params)):
                relevant_facts.append((is_not, atom_name, fact_args))
        return relevant_facts

    def _get_all_atom_facts(self, lib):
        state_size = lib.get_state_size()
        atoms = (Atom * state_size)()
        lib.get_state(atoms)
        atom_names = list(set(map(str, atoms)))
        atom_names = [x.replace("NegatedAtom ", "not ").replace("Atom ", "") for x in atom_names]
        # 'new-axiom@0' is a special atom that is not relevant to the user
        atom_names = [x for x in atom_names if 'new-axiom@0' not in x]
        atoms_parsed = [
            (is_not, atom_name, fact_args) for is_not, atom_name, fact_args in map(extract_atom_arguments, atom_names)
        ]
        return atoms_parsed

    def _parse_val_output(self, val_output: str):
        plan_val_text = "Plan Validation details\n-----------------------"
        if "Plan valid" in val_output:
            return True, "The plan is valid."
        elif plan_val_text in val_output:
            val_output = val_output.split(plan_val_text)[1].strip()
            return False, val_output
        elif "Goal not satisfied" in val_output:
            return False, "The goal is not satisfied."
        elif "Plan invalid" in val_output:
            return False, "The plan is invalid."
        else:
            logging.info("Unknown validation output: " + val_output)
            return False, "Unknown error."

    def plan_to_str(self, plan):
        if isinstance(plan, list):
            return "\n".join(plan)
        else:
            return str(plan)
