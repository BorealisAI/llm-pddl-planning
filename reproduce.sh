# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

FD_PY_PATH="/path/to/downward/fast-downward.py"
VAL_BIN_PATH="/path/to/VAL/build/linux64/Release/bin/Validate"
OPENAI_API_KEY="your-openai-api-key"
WANDB_ENTITY="your-wandb-team"
WANDB_PROJECT="your-wandb-project"

MODEL_NAME="gpt-4-1106-preview"


##################### Run Model (Table 2) #####################

for domain_name in "termes" "grippers" "grippers-ood" "hiking-agl14-strips" "floortile" "driverlog" "miconic" "movie"  "childsnack-opt14-strips" "barman"; do
  for seed in "42" "43" "44" "45"; do
   # P&D Chain
   python3 src/main.py --cfg.gpt_args.model_name=${MODEL_NAME} --cfg.log_prefix=paper_table_2/${domain_name}/gpt4-old-top1-trans1                  --cfg.seed=${seed} --cfg.planning_strategy_args.best_of_n=1  --cfg.problem_translation_args.active=True  --cfg.problem_translation_args.n_candidates=1 --cfg.target_domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH} --cfg.gpt_args.api_key=${OPENAI_API_KEY} --cfg.wandb_args.entity=${WANDB_ENTITY} --cfg.wandb_args.project=${WANDB_PROJECT}
   # P&D Tree
   python3 src/main.py --cfg.gpt_args.model_name=${MODEL_NAME} --cfg.log_prefix=paper_table_2/${domain_name}/gpt4-old-top10-trans5                 --cfg.seed=${seed} --cfg.planning_strategy_args.best_of_n=10 --cfg.problem_translation_args.active=True  --cfg.problem_translation_args.n_candidates=5 --cfg.target_domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH} --cfg.gpt_args.api_key=${OPENAI_API_KEY} --cfg.wandb_args.entity=${WANDB_ENTITY} --cfg.wandb_args.project=${WANDB_PROJECT}
   # P&D Tree + DomProp
   python3 src/main.py --cfg.gpt_args.model_name=${MODEL_NAME} --cfg.log_prefix=paper_table_2/${domain_name}/gpt4-old-top10-trans5-domain-proposal --cfg.seed=${seed} --cfg.planning_strategy_args.best_of_n=10 --cfg.problem_translation_args.active=True  --cfg.problem_translation_args.n_candidates=5 --cfg.problem_translation_args.add_domain_proposal=True --cfg.target_domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH} --cfg.gpt_args.api_key=${OPENAI_API_KEY} --cfg.wandb_args.entity=${WANDB_ENTITY} --cfg.wandb_args.project=${WANDB_PROJECT}
   # Intrinsic No CoT
   python3 src/intrinsic_planning.py --cfg.gpt_args.model_name=${MODEL_NAME} --cfg.log_prefix=paper_table_2/${domain_name}/intrinsic-gpt4 --cfg.seed=${seed} --cfg.target_domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH} --cfg.gpt_args.api_key=${OPENAI_API_KEY} --cfg.wandb_args.entity=${WANDB_ENTITY} --cfg.wandb_args.project=${WANDB_PROJECT}
   # Intrinsic CoT
   python3 src/intrinsic_planning.py --cfg.gpt_args.model_name=${MODEL_NAME} --cfg.log_prefix=paper_table_2/${domain_name}/intrinsic-cot-gpt4 --cfg.seed=${seed} --cfg.use_cot=True --cfg.target_domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH} --cfg.gpt_args.api_key=${OPENAI_API_KEY} --cfg.wandb_args.entity=${WANDB_ENTITY} --cfg.wandb_args.project=${WANDB_PROJECT}
  done
done

##################### Exploration Walk Analysis (Figure 2 and Figure 4) #####################

cd src/rw_analysis
for domain_name in "grippers" "termes" "floortile" "storage" "childsnack-opt14-strips" "barman" "tyreworld" "depot" "driverlog" "hiking-agl14-strips" "logistics00" "miconic" "mprime" "parking-opt11-strips" "rovers" "satellite" "scanalyzer-08-strips" "trucks" "zenotravel"; do
  python3 rw_analysis.py --cfg.domain_name=${domain_name} --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH}
  python3 rw_analysis.py --cfg.domain_name=${domain_name} --cfg.mode=plan_inv --cfg.max_diff=10 --cfg.n_gen_per_diff=100 --cfg.n_tasks=5 --cfg.env_args.fd_py_path=${FD_PY_PATH} --cfg.env_args.val_bin_path=${VAL_BIN_PATH}
done
