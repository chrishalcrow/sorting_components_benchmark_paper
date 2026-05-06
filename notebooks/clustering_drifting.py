import spikeinterface.full as si
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from spikeinterface.sortingcomponents.tools import remove_empty_templates
from spikeinterface.core.node_pipeline import sorting_to_peaks
from spikeinterface.benchmark.benchmark_clustering import ClusteringStudy

from configuration import base_path
from slurm_tools import push_to_slurm
from dataset import get_dataset


def preprocess(rec):
    rec_f = si.bandpass_filter(rec, freq_min=300., freq_max=6000., ftype="bessel", dtype='float32', margin_ms=20.)
    return rec_f

def run_study(motion_folder, study_folder, dataset_name='Neuronexus-32_50_300.s', erase=True):
    # si.set_global_job_kwargs(n_jobs=0.8, pool_engine='process')
    si.set_global_job_kwargs(n_jobs=30, pool_engine='process')
    
    rng = np.random.default_rng(seed=2205)

    motion_folder = Path(motion_folder)
    study_folder = Path(study_folder)

    if motion_folder.is_dir():
        import shutil
        shutil.rmtree(motion_folder)

    static, drifting, sorting, analyzer_static, analyzer_drifting = get_dataset(dataset_name)

    static = si.whiten(static, mode="local", radius_um=100.)
    drifting = si.whiten(drifting, mode="local", radius_um=100.)

    static = preprocess(static)
    drifting = preprocess(drifting)
    if dataset_name.startswith("Neuronexus-32"):
        motion_preset = 'rigid_fast'
    else:
        motion_preset='dredge_fast'

    static = si.whiten(static) # , regularize=True
    drifting = si.whiten(drifting)
    
    corrected, motion_info = si.correct_motion(drifting, folder=motion_folder, preset=motion_preset, output_motion_info=True)

    datasets = {
       "static" : (static, sorting),
       "corrected" : (corrected, sorting),
    }
    
    nb_spikes = sorting.to_spike_vector().size
    max_spikes = int(5000*static.get_num_channels())
    if nb_spikes < max_spikes:
        indices = np.arange(nb_spikes)
    else:
        indices = rng.choice(np.arange(nb_spikes), min(nb_spikes, max_spikes), replace=False)
    indices = np.sort(indices)
    subsampling_factor = nb_spikes / indices.size
    print('subsampling_factor', subsampling_factor)
    all_peaks = {}
    for dataset_name in datasets.keys():

        recording, gt_sorting = datasets[dataset_name]
        
        sorting_analyzer = si.create_sorting_analyzer(gt_sorting, recording, format="memory", sparse=False)
        sorting_analyzer.compute(["random_spikes", "templates"])
        sorting_analyzer.compute(["spike_amplitudes"])
        max_channel_index = gt_sorting.get_property('max_channel_index')
        extremum_channel_inds = dict(zip(gt_sorting.unit_ids, max_channel_index))

        spikes = gt_sorting.to_spike_vector(extremum_channel_inds=extremum_channel_inds)
        peaks = sorting_to_peaks(gt_sorting, extremum_channel_inds)
        peaks["amplitude"] = sorting_analyzer.get_extension("spike_amplitudes").get_data()
        all_peaks[dataset_name] = peaks
    
    cases = {}

    for engine in ['iterative-hdbscan', 'iterative-isosplit', 'graph-clustering', 'kilosort-clustering',]:


        for key in datasets.keys():
            cases[(engine, key)] = {
                "label": f"{engine} {key}",
                "dataset": key,
                "init_kwargs": {'indices' : indices, 'peaks' : all_peaks[key]},
                "params" : {"method" : engine, "method_kwargs" : {}            
                },
            }

            if engine in ('iterative-hdbscan', 'iterative-isosplit', ):
                cases[(engine, key)]['params']["method_kwargs"]["clean_low_firing"] = {"min_firing_rate": 0.1, "subsampling_factor": subsampling_factor}


                
        
    if erase:
        import shutil
        if study_folder.exists():
            shutil.rmtree(study_folder)
        study = ClusteringStudy.create(study_folder, datasets=datasets, cases=cases)
    else:
        study = ClusteringStudy(study_folder)
    
    study.run(verbose=True)
    
    study.compute_results()
    study.compute_metrics()



if __name__ == "__main__":
    global_name = 'clustering_drifting'

    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixels1-128_250_100.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    dataset_name = 'Neuropixels1-384_500_1800.s'

    motion_folder = base_path / global_name / dataset_name / 'motion'
    study_folder = base_path / global_name / dataset_name / 'study'

    run_study(motion_folder, study_folder, dataset_name, erase = True)


    # push_to_slurm(run_study,  motion_folder, study_folder,  dataset_name, erase=True,
    #               slurm_option={'mem': '90G', 'cpus-per-task': 50squ, 'partition': 'CPU'},
    #               block_mode=False,
    #               )

