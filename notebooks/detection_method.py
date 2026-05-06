import spikeinterface.full as si
from pathlib import Path
import numpy as np
from spikeinterface.sortingcomponents.tools import remove_empty_templates

from spikeinterface.benchmark.benchmark_peak_detection import PeakDetectionStudy

from configuration import base_path
from slurm_tools import push_to_slurm
from dataset import get_dataset


def run_study(study_folder, dataset_name, erase = True):
    si.set_global_job_kwargs(n_jobs=0.8, chunk_duration="1s")

    static, drifting, sorting, analyzer_static, analyzer_drifting = get_dataset(dataset_name)

    study_folder = study_folder

    datasets = {
        "static" : (static, sorting),
    }

    prototypes = {}
    peaks = {}
    for dataset in datasets.keys():

        ms_before = 1.0
        ms_after = 2.0
        rec, sorting = datasets[dataset]
        from spikeinterface.sortingcomponents.tools import get_prototype_and_waveforms_from_recording
        from spikeinterface.sortingcomponents.peak_detection import detect_peaks
        from spikeinterface.core.template_tools import get_template_extremum_channel

        detection_params = {"peak_sign": "neg", "detect_threshold": 5, "exclude_sweep_ms" : 2.0}
        
        prototypes[dataset], _, _ = get_prototype_and_waveforms_from_recording(rec, 5000, ms_before, ms_after, **detection_params)

        sorting_analyzer = si.create_sorting_analyzer(sorting, rec, format="memory", sparse=False)
        sorting_analyzer.compute(["random_spikes", "templates"])
        
        extremum_channel_inds = get_template_extremum_channel(sorting_analyzer, outputs="index")
        spikes = sorting.to_spike_vector(extremum_channel_inds=extremum_channel_inds)
        peaks[dataset] = spikes
    
    cases = {}

    for engine in ['locally_exclusive', 'matched_filtering']:
        for key in datasets.keys():
            cases[(engine, key)] = {
                "label": f"{engine} {key}",
                "dataset": key,
                "init_kwargs": {"gt_peaks" : peaks[key]},
                "params" : {"method" : engine, "method_kwargs" : {"exclude_sweep_ms" : 2.0}},
            }
            if engine == 'matched_filtering':
                cases[(engine, key)]['params']['method_kwargs']["prototype"] = prototypes[key]
                cases[(engine, key)]['params']['method_kwargs']["ms_before"] = ms_before

    if erase:
        import shutil
        if study_folder.exists():
            shutil.rmtree(study_folder)
        study = PeakDetectionStudy.create(study_folder, datasets=datasets, cases=cases)
        
    else:
        study = PeakDetectionStudy(study_folder)


    study.run(verbose=True)
    study.compute_results()
    study.compute_metrics()


if __name__ == "__main__":
    global_name = 'detection_method'

    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixel-128_250_300.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    dataset_name = 'Neuropixels1-384_500_1800.s'

    
    study_folder = base_path / global_name / dataset_name / 'study'
    run_study(study_folder, dataset_name)


    # push_to_slurm(run_study,  study_folder,  dataset_name, erase=True,
    #               slurm_option={'mem': '90G', 'cpus-per-task': 70, 'partition': 'GPU'},
    #               block_mode=False,
    #               )