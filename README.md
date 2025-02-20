# [Neurips 2024] Leveraging Environment Interaction for Automated PDDL Translation and Planning with Large Language Models

[![arXiv](https://img.shields.io/badge/arXiv-2407.12979-b31b1b.svg)](https://arxiv.org/abs/2407.12979)

This is the official Repository to the paper [Leveraging Environment Interaction for Automated PDDL Translation and Planning with Large Language Models](https://arxiv.org/abs/2407.12979).

## Quick Run

To reproduce the experiments in our paper, follow below steps:

1. Prepare the data. You can obtain the original PDDL files from the [LLM+P repository](https://github.com/Cranial-XIX/llm-pddl) and [DownwardBenchmarks repository](https://github.com/aibasel/downward-benchmarks). We provide the pddl files for some of the environments in the `data` folder. You can then produce the back translations, templates, and descriptions using the files `back_translate.py, gen_pddl_template_pddl.py`.

2. Install the python requirements via 
```bash
pip install requirements.txt
```
**Note:** requires Python >= 3.9

3. Download the following external libraries:

* [VAL](https://github.com/KCL-Planning/VAL)
* [Fast Downward 22.06.1](https://github.com/aibasel/downward/releases/tag/release-22.06.1)

4. Configure the following environment variables in `reproduce.sh`: `FD_PY_PATH` (path to the .py file of fast downard), `VAL_BIN_PATH` (path to the VAL library binary file), `OPENAI_API_KEY` (OpenAI key), `WANDB_ENTITY` (wandb entity), `WANDB_PROJECT` (wandb project). We use the `gpt-4-1106-preview` GPT4 model in our project by default.

6. Run 
```
bash reproduce.sh
```
to reproduce the experiments.


## Repository Structure

The data used in our experiments can be found in the `data` directory. Each domain has the following format:

```
📦domain
 ├ 📜domain.pddl               # The domain PDDL file
 ├ 📜domain_template.pddl      # Domain template PDDL
 ├ 📜domain.nl                 # Natural language description of the domain (GPT-generated).
 ├ 📜predicate_descriptor.py   # Mapping between NL descriptions and predicates (GPT-generated).
 ├ 📜p{i}.pddl                 # The {i}-th problem PDDL file
 ├ 📜p{i}_template.pddl        # The {i}-th problem template 
 ├ 📜p{i}.nl                   # Natural language description of the {i}-th problem (GPT-generated).
 ├ 📜p_example.pddl            # Example problem PDDL file.
 ├ 📜p_example_template.pddl   # Example problem template.
 ├ 📜p_example.nl              # Example natural language description.
 └ 📜p_example.sol             # Example solution.
```

The following is the code structure for source files:
```
📦src
 ├ 📜back_translate.py         # Backtranslation utils for domain/problem/description natural language geneation
 ├ 📜domains.py              
 ├ 📜error_messages.py        
 ├ 📜evaluation.py            
 ├ 📜gen_pddl_template_pddl.py # Generates PDDL templates from the original PDDL files.
 ├ 📜gpt_client.py            
 ├ 📜intrinsic_planning.py     # Intrinsic planning baselines
 ├ 📜main.py                   # Main entry point for our method
 ├ 📜pddl_utils.py             # Utility functions to work with PDDL files.
 ├ 📜planning.py               # Core planning logic and functions.
 ├ 📜problem_domain_translation.py
 ├ 📜prompts.py               
 ├ 📂rw_analysis              # Analysis for exploration walk
 │  ├ 📜rw_analysis.py        # Core reward analysis logic.
 │  └ 📜rw_corr_plot.py       # Plots for reward correlation analysis.
 └ 📜utils.py 
```


## Citation

If you find this work useful, please cite our paper:
```
@inproceedings{
  mahdavi2024leveraging,
  title={Leveraging Environment Interaction for Automated {PDDL} Translation and Planning with Large Language Models},
  author={Sadegh Mahdavi and Raquel Aoki and Keyi Tang and Yanshuai Cao},
  booktitle={The Thirty-eighth Annual Conference on Neural Information Processing Systems},
  year={2024},
  url={https://openreview.net/forum?id=RzlCqnncQv}
}
```

## Questions/Bugs

Please submit a Github issue or contact smahdavi@ece.ubc.ca if you have any questions or find any bugs.
