# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from typing import List

from pddl.logic import Predicate
from pddl.logic.base import Or, And
from pddl.parser.domain import DomainParser
from pddl.formatter import domain_to_string, problem_to_string
import functools

from pddl.parser.problem import ProblemParser


class PDDLObj:
    def __init__(self, domain_pddl, domain_template_pddl):
        self.domain_pddl = domain_pddl
        self.domain_pddl_template = domain_template_pddl

    @staticmethod
    def from_pddl_str(domain_pddl, domain_pddl_template):
        domain_pddl = PDDLObj.maybe_add_dummy_predicate(domain_pddl)
        pddl_obj = PDDLObj(DomainParser()(domain_pddl), domain_pddl_template)
        return pddl_obj

    def to_str(self):
        # if any dummy predicate was added and now non-dummy predicates exist, remove the dummy predicate
        self.maybe_remove_dummy_predicate()
        domain_pddl_str = domain_to_string(self.domain_pddl)
        domain_pddl_str = domain_pddl_str.replace('(or )', '()')
        return domain_pddl_str

    def add_or_update_predicates(self, predicate_strs: list):
        parsed_predicates = self.parse_predicates(predicate_strs)
        parsed_predicates = self._add_existing_predicates(parsed_predicates)
        self._assert_no_duplicate_predicates(parsed_predicates)
        self.domain_pddl._predicates = parsed_predicates

    def modify_action(self, action_name, preconditions, effects):
        action = self.get_action_by_name(action_name)
        self._erase_action_details(action)
        new_domain_pddl_str = self._inject_action_details(action_name, preconditions, effects)
        self.domain_pddl = PDDLObj.from_pddl_str(new_domain_pddl_str, self.domain_pddl_template).domain_pddl
        self._assert_declared_predicates()

    def modify_domain(self, func_modification: str):
        add_or_update_predicates = functools.partial(self.add_or_update_predicates)
        modify_action = functools.partial(self.modify_action)
        error_msg = None
        try:
            exec(func_modification)
        except Exception as e:
            logging.info(f"Exception while modifying the domain: {e}")
            error_msg = f"Error while executing your code: {e}"
        return error_msg

    def sanity_check_domain(self):
        empty_effect_actions = []
        for action in self.domain_pddl.actions:
            if str(action.effect).count('(') <= 1:  # only one open parenthesis, i.e. no effect
                empty_effect_actions.append(action.name)
        if len(empty_effect_actions) > 0:
            return f"The following actions have no effect: {empty_effect_actions}"

    def copy_object(self):
        pddl_str = self.to_str()
        return PDDLObj.from_pddl_str(pddl_str, self.domain_pddl_template)

    @staticmethod
    def maybe_add_dummy_predicate(domain_pddl: str):
        if '(:predicates)' in domain_pddl:
            return domain_pddl.replace('(:predicates)', '(:predicates (dummy-predicate))')
        else:
            return domain_pddl

    def maybe_remove_dummy_predicate(self):
        predicate_list = list(self.domain_pddl.predicates)
        new_predicate_list = [
            predicate for predicate in predicate_list if predicate.name != 'dummy-predicate'
        ]
        if len(new_predicate_list) != 0 and len(new_predicate_list) != len(predicate_list):
            self.domain_pddl._predicates = set(new_predicate_list)

    def parse_predicates(self, predicate_strs: list):
        # This is a hacky way to parse predicates from a string. We use the domain template to parse the predicates
        assert '(:predicates)' in self.domain_pddl_template, "Domain template must contain empty predicate section."
        pred_concat = "\n".join(predicate_strs)
        template_predicates = self.domain_pddl_template.replace(
            '(:predicates)', f'(:predicates {pred_concat})'
        )
        return set(PDDLObj.from_pddl_str(template_predicates, self.domain_pddl_template).domain_pddl.predicates)

    def _assert_no_duplicate_predicates(self, predicate_list):
        predicate_names = [predicate.name for predicate in predicate_list]
        # More than one occurrence of a predicate name is not allowed
        duplicate_predicate_names = {name for name in predicate_names if predicate_names.count(name) > 1}
        assert len(duplicate_predicate_names) == 0, f"Duplicate predicate names found: {duplicate_predicate_names}."

    def _add_existing_predicates(self, new_predicates):
        new_updated_predicates = set(new_predicates)
        new_predicate_names = {predicate.name for predicate in new_predicates}
        cur_predicates = set(self.domain_pddl.predicates)
        for predicate in cur_predicates:
            if predicate.name not in new_predicate_names:
                new_updated_predicates.add(predicate)
        return new_updated_predicates

    def get_action_by_name(self, action_name):
        for action in self.domain_pddl.actions:
            if action.name == action_name:
                return action
        else:
            raise ValueError(f"Could not find action {action_name} in domain.")

    def _erase_action_details(self, action):
        action._precondition = Or()
        action._effect = Or()

    def _inject_action_details(self, action_name, preconditions: List[str], effects: List[str]):
        domain_pddl_str = self.to_str()
        precondition_str = self._concat_cond_list(preconditions)
        effect_str = self._concat_cond_list(effects)

        def replace_precondition_effect(cur_domain, is_precond, replace_str):
            slang = 'precondition' if is_precond else 'effect'
            find_str = f':{slang} ()'
            in_action = False
            for i in range(len(cur_domain)):
                if cur_domain[i:i + len(action_name)] == action_name:
                    in_action = True
                if in_action and cur_domain[i:].startswith(find_str):
                    return (
                            cur_domain[:i] + f':{slang} ' + replace_str + cur_domain[i + len(find_str):]
                    )
            raise ValueError(f"Could not replace precondition or effect for action {action_name}.")

        domain_pddl_str = replace_precondition_effect(domain_pddl_str, True, precondition_str)
        domain_pddl_str = replace_precondition_effect(domain_pddl_str, False, effect_str)

        return domain_pddl_str

    def _concat_cond_list(self, lst):
        if len(lst) == 0:
            return f'()'
        else:
            return f'(and {" ".join(lst)})'

    def _assert_declared_predicates(self):
        predicate_names = {predicate.name for predicate in self.domain_pddl.predicates}
        all_used_predicates = set()
        for action in self.domain_pddl.actions:
            for formula in [action.precondition, action.effect]:
                all_used_predicates.update(self._extract_formula_predicate_names(formula))
        undeclared_predicates = all_used_predicates.difference(predicate_names)
        assert len(undeclared_predicates) == 0, (f"Undeclared predicates found: {undeclared_predicates}."
                                                 f"You must declare all predicates before using them.")

    def _extract_formula_predicate_names(self, formula):
        predicate_names = set()
        if isinstance(formula, Predicate):
            return {formula.name}
        if hasattr(formula, 'operands'):
            for operand in formula.operands:
                predicate_names.update(self._extract_formula_predicate_names(operand))
            return predicate_names
        if hasattr(formula, 'argument'):
            return self._extract_formula_predicate_names(formula.argument)
        logging.warning(f"Could not extract predicate names from formula {formula}.")
        return predicate_names


class ProblemPDDLObj:
    def __init__(self, problem_pddl):
        self.problem_pddl = problem_pddl

    @staticmethod
    def from_pddl_str(problem_pddl):
        return ProblemPDDLObj(ProblemParser()(problem_pddl))

    def goal_count(self):
        return len(self.problem_pddl.goal.operands)

    def init_count(self):
        return len(self.problem_pddl.init)


def get_problem_pddl_empty_goal(problem_pddl: str):
    problem_parsed = ProblemParser()(problem_pddl)
    problem_parsed._goal = And()
    return problem_to_string(problem_parsed)


def get_problem_pddl_empty_goal_and_init(problem_pddl: str):
    problem_parsed = ProblemParser()(problem_pddl)
    problem_parsed._goal = And()
    problem_parsed._init = set()
    problem_str = problem_to_string(problem_parsed)
    return problem_str


def validate_problem_pddl(problem_pddl):
    ProblemParser()(problem_pddl)
    return True


def extract_atom_arguments(atom_str):
    """
    not contains(shot3, ingredient1)
    """
    is_not = atom_str.strip().startswith('not ')
    atom_name = atom_str.split('(')[0].split()[-1]
    args = atom_str.split('(')[1].split(')')[0].split(',')
    args_strip = [arg.strip() for arg in args]
    return is_not, atom_name, args_strip
