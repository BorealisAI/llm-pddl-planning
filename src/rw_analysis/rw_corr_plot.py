# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import numpy as np
import matplotlib.pyplot as plt

domain_translations = {
    'parking-opt11-strips': 'Parking',
    'satellite': 'Satellite',
    'scanalyzer-08-strips': 'Scanalyzer',
    'zenotravel': 'Zenotravel',
    'rovers': 'Rovers',
    'movie': 'Movie',
    'mprime': 'Mprime',
    'miconic': 'Miconic',
    'logistics00': 'Logistics',
    'depot': 'Depot',
    'hiking-agl14-strips': 'Hiking',
    'driverlog': 'Driverlog',
    'barman': 'Barman',
    'blocksworld': 'Blocksworld',
    'floortile': 'Floortile',
    'grippers': 'Grippers',
    'grippers-ood': 'Grippers-ood',
    'storage': 'Storage',
    'termes': 'Termes',
    'trucks': 'Trucks',
    'tyreworld': 'Tyreworld',
    'manipulation': 'Manipulation',
    'childsnack-opt14-strips': 'Childsnack',
}


def group_avg(n_diff, data):
    assert len(n_diff) == len(data)
    n_diffs = sorted(np.unique(n_diff))
    avg_data = []
    se_data = []
    for n in n_diffs:
        avg_data.append(np.mean(data[n_diff == n]))
        se_data.append(np.std(data[n_diff == n]) / np.sqrt(np.sum(n_diff == n)))
    return n_diffs, np.array(avg_data), np.array(se_data)


def analyze_rw_random_del(rw_tag):
    rw_path = f'/tmp/{rw_tag}'
    plt.figure(figsize=(13, 10))
    for i, f in enumerate(os.listdir(rw_path)):
        if f.endswith('.npy'):
            domain_name = f.split('_')[0]
            data = np.load(os.path.join(rw_path, f))
            n_diff, rw_score, t_to_gen_frac, gen_to_t_frac = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
            plt.subplot(4, 4, i + 1)
            n_diffs, avg_rw_score, se_rw_score = group_avg(n_diff, rw_score)
            plt.plot(n_diffs, avg_rw_score, marker='.')
            plt.fill_between(n_diffs, avg_rw_score - se_rw_score, avg_rw_score + se_rw_score, alpha=0.2)
            plt.title(domain_translations[domain_name])
            plt.xticks(n_diffs)
            plt.xlabel('Term Difference')
            plt.ylabel('Average EW Score')
    plt.tight_layout()
    plt.savefig(f'/tmp/rw_corr.png')
    plt.savefig(f'/tmp/rw_corr.pdf')
    print(f'Plotted.')


def analyze_domain_plan_inv(tag):
    plan_path = f'/tmp/{tag}'
    plt.figure(figsize=(13, 10))
    n_rows = 4
    n_cols = 4
    domain_data = {}
    for i, f in enumerate(os.listdir(plan_path)):
        if f.endswith('.npy'):
            domain_name = f.split('_')[0]
            data = np.load(os.path.join(plan_path, f))
            n_diff, exists = data[:, 0], data[:, 1]
            n_diffs, avg_exists, se_exists = group_avg(n_diff, exists)
            domain_data[domain_name] = n_diffs, avg_exists, se_exists
    for i, domain_name in enumerate(sorted(domain_data.keys())):
        plt.subplot(n_rows, n_cols, i + 1)
        n_diffs, avg_exists, se_exists = domain_data[domain_name]
        avg_not_exists = 1 - avg_exists
        plt.plot(n_diffs, avg_not_exists, marker='.')
        plt.fill_between(n_diffs, avg_not_exists - se_exists, avg_not_exists + se_exists, alpha=0.2)
        plt.title(domain_translations[domain_name])
        plt.xticks(n_diffs)
        plt.xlabel('Plan-Not-Found Percentage')
        plt.ylabel('Nonexistence Plan Percentage')
    plt.tight_layout()
    plt.savefig(f'/tmp/{tag}.png')
    plt.savefig(f'/tmp/{tag}.pdf')
    plt.clf()

    plt.figure(figsize=(4, 2.5))
    plt.grid(True, linestyle='--', alpha=0.7)
    for i, domain_name in enumerate(sorted(domain_data.keys())):
        n_diffs, avg_exists, se_exists = domain_data[domain_name]
        avg_not_exists = 1 - avg_exists
        plt.plot(n_diffs, avg_not_exists, color='gray', alpha=0.3)
    avg_avg_exists = np.mean([domain_data[domain_name][1] for domain_name in domain_data], axis=0)
    avg_avg_not_exists = 1 - avg_avg_exists
    print(f"Average not exists: {avg_avg_not_exists}")
    n_diffs = list(domain_data.values())[0][0]
    plt.plot(n_diffs, avg_avg_not_exists, marker='.', linewidth=3, color='red', markersize=10, label='Average')
    plt.legend(fontsize=12, loc='upper left')
    plt.xticks(n_diffs)
    plt.xlabel('Number of Removed Terms ($k$)')
    plt.ylabel('Plan-Not-Found Fraction')
    plt.tight_layout()
    plt.savefig(f'/tmp/{tag}_avg.png')
    plt.savefig(f'/tmp/{tag}_avg.pdf')
    print(f'Plotted.')


def main():
    analyze_rw_random_del(rw_tag='rw_analysis3')
    analyze_domain_plan_inv(tag='plan_inv')


if __name__ == '__main__':
    main()
