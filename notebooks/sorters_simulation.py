import spikeinterface.full as si
from pathlib import Path


import numpy as np
import matplotlib.pyplot as plt


from configuration import base_path, kilosort2_5_path
from slurm_tools import push_to_slurm
from dataset import get_dataset
from spikeinterface.preprocessing import bandpass_filter

from spikeinterface.benchmark import SorterStudy


def preprocess(rec):
    rec = bandpass_filter(rec, freq_min=150., freq_max=9000., ftype="bessel", dtype='float32', margin_ms=35.)
    return rec

def run_study(study_folder, dataset_name, erase=True):
    si.set_global_job_kwargs(n_jobs=0.8, pool_engine='process', chunk_duration="0.2s")
    
    study_folder = Path(study_folder)

    seeds = [ 2205, 2406, 2308, 1110, 2512]
    # seeds = [ 2205,  ]

    datasets = {}
    for s, seed in enumerate(seeds):
        static, drifting, sorting, analyzer_static, analyzer_drifting = get_dataset(dataset_name, seed=seed)

        static = preprocess(static)
        drifting = preprocess(drifting)

        datasets[f"static_{s}"] = (static, sorting)
        datasets[f"drifting_{s}"] = (drifting, sorting)

    cases = {}
    for s, seed in enumerate(seeds):
        for motion_case in ["static", "drifting"]:

            data_name = f"{motion_case}_{s}"

            is_drifting = (motion_case == 'drifting')

            case_key = ('kilosort4', motion_case, f"{s}")
            cases[case_key] = {
                    "label": f"kilosort4 {data_name}",
                    "dataset": data_name,
                    "params": {"sorter_name": "kilosort4"},
            }
            cases[case_key]["params"]["do_correction"] = is_drifting
            cases[case_key]["params"]["verbose"] = True

            # case_key = ('kilosort4like', motion_case, f"{s}")
            # cases[case_key] = {
            #         "label": f"kilosort4like {data_name}",
            #         "dataset": data_name,
            #         "params": {"sorter_name": "kilosort4like"},
            # }
            # cases[case_key]["params"]["apply_motion_correction"] = is_drifting
            # cases[case_key]["params"]["verbose"] = True

            case_key = ('tridesclous2', motion_case, f"{s}")
            cases[case_key] = {
                    "label": f"tridesclous2 {data_name}",
                    "dataset": data_name,
                    "params": {"sorter_name": "tridesclous2"},
            }
            cases[case_key]["params"]["apply_motion_correction"] = is_drifting
            cases[case_key]["params"]["verbose"] = True
            

            case_key = ('spykingcircus2', motion_case, f"{s}")
            cases[case_key] = {
                    "label": f"spykingcircus2 {data_name}",
                    "dataset": data_name,
                    "params": {
                        "sorter_name": "spykingcircus2"},
                }
            cases[case_key]["params"]["apply_motion_correction"] = is_drifting
            cases[case_key]["params"]["verbose"] = True

            case_key = ('lupin', motion_case, f"{s}")
            cases[case_key] = {
                    "label": f"lupin {data_name}",
                    "dataset": data_name,
                    "params": {
                        "sorter_name": "lupin",
                        "template_matching_engine": "wobble",
                    },
                }
            cases[case_key]["params"]["apply_motion_correction"] = is_drifting
            cases[case_key]["params"]["verbose"] = True
    
    if erase:
        import shutil
        if study_folder.exists():
            shutil.rmtree(study_folder)
        study = si.SorterStudy.create(study_folder, datasets=datasets, cases=cases, levels=["sorter_name", "drifting", "num"])
    else:
        study = si.SorterStudy(study_folder)
    
    study.run(verbose=True)
    study.compute_results()
    study.compute_metrics()


if __name__ == "__main__":
    global_name = 'sorters_simulation'

    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixels1-128_250_100.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    dataset_name = 'Neuropixels1-384_500_1800.s'

    study_folder = base_path / global_name / dataset_name / 'study'

    # run_study(study_folder, dataset_name, erase=True)


    # push_to_slurm(run_study,  study_folder,  dataset_name, erase=True,
    #               slurm_option={'mem': '90G', 'cpus-per-task': 70, 'partition': 'GPU'},
    #               block_mode=True,
    #               )
    
    study = SorterStudy(study_folder)
    print(study)
    si.set_global_job_kwargs(n_jobs=0.8, pool_engine='process', chunk_duration="0.2s")
    some_cases = [k for k in study.cases.keys() if k[0] == 'lupin']
    print(some_cases)


    study.run(case_keys=some_cases, keep=False, verbose=True)
    # study.run(case_keys=None, keep=True, verbose=True)

    study.compute_results()
    study.compute_metrics()

