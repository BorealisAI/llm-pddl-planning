# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

RANDOM_WALK_TARGET_TO_GEN_DESC = "Sampled a set of consecutive random actions from the ground truth environment, but the actions are not executable in the generated environment.\n"
RANDOM_WALK_GEN_TO_TARGET_DESC = "Sampled a set of consecutive random actions from the generated environment, but the actions are not executable in the ground truth environment.\n"
NO_EXECUTABLE_INITIAL_ACTION = "Could not find any valid actions to execute. All the initial actions violate at least one precondition. Make sure your predicate names match the ones in the problem instance."
