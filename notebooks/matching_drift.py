
from pathlib import Path
import shutil

import numpy as np


import spikeinterface.full as si
from spikeinterface.sortingcomponents.tools import remove_empty_templates
from spikeinterface.benchmark.benchmark_matching import MatchingStudy

from configuration import base_path
from slurm_tools import push_to_slurm
from dataset import get_dataset

def preprocess(rec):
    rec_f = si.bandpass_filter(rec, freq_min=300., freq_max=6000., ftype="bessel", dtype='float32', margin_ms=20.)
    return rec_f

def run_study(motion_folder, study_folder, dataset_name, erase=True):
    # si.set_global_job_kwargs(n_jobs=0.8)
    # si.set_global_job_kwargs(n_jobs=20, chunk_duration="0.2s")
    si.set_global_job_kwargs(n_jobs=0.8, chunk_duration="0.2s")

    static, drifting, sorting, analyzer_static, analyzer_drifting = get_dataset(dataset_name)
    static = preprocess(static)
    drifting = preprocess(drifting)
    static = si.whiten(static, mode="local", radius_um=100.)
    drifting = si.whiten(drifting, mode="local", radius_um=100.)

    if erase and motion_folder.exists():
        shutil.rmtree(motion_folder)

    if dataset_name.startswith("Neuronexus-32"):
        motion_preset = 'rigid_fast'
    else:
        motion_preset='dredge_fast'

    corrected, motion_info = si.correct_motion(drifting, folder=motion_folder, preset=motion_preset, output_motion_info=True)

    study_folder = Path(study_folder)
    motion_folder = Path(motion_folder)
    
    datasets = {
        "static" : (static, sorting),
        "corrected" : (corrected, sorting)
    }
    
    templates = {}
    spatial= {}
    temporal = {}
    for data_key in datasets:

        ms_before = 1.5
        ms_after = 2.5
        recording, gt_sorting = datasets[data_key]
        spikes = gt_sorting.to_spike_vector()
        fs = recording.sampling_frequency
        nbefore = int(ms_before * fs / 1000)
        nafter = int(ms_after * fs / 1000)
        templates_array = si.estimate_templates(
            recording, spikes, 
            gt_sorting.unit_ids, nbefore, nafter, return_in_uV=False, job_name=None
        )
        
        temps = si.Templates(
             templates_array,
             fs,
             nbefore,
             sparsity_mask=None,
             channel_ids=recording.channel_ids,
             unit_ids=gt_sorting.unit_ids,
             probe=recording.get_probe(),
            is_in_uV=False,
            )
        
        noise_levels = si.get_noise_levels(recording, return_in_uV=False)
        sparsity = si.compute_sparsity(temps, noise_levels=noise_levels, method='snr', amplitude_mode='peak_to_peak', threshold=0.25)
        templates[data_key] = temps.to_sparse(sparsity)
        templates[data_key] = remove_empty_templates(templates[data_key])

        from spikeinterface.sortingcomponents.tools import get_prototype_and_waveforms
        prototype, wfs, few_peaks = get_prototype_and_waveforms(recording, ms_before=ms_before, ms_after=ms_after)
        import numpy as np
        n_components = 5

        from sklearn.cluster import KMeans
        wfs /= np.linalg.norm(wfs, axis=1)[:, None]
        model = KMeans(n_clusters=n_components, n_init=10).fit(wfs)
        temporal_components = model.cluster_centers_
        temporal_components = temporal_components / np.linalg.norm(temporal_components, axis=1)[:, None]
        temporal_components = temporal_components.astype(np.float32)
        
        from sklearn.decomposition import TruncatedSVD
        model = TruncatedSVD(n_components=n_components).fit(wfs)
        spatial[data_key] = model.components_.astype(np.float32)
        temporal[data_key] = temporal_components
    
    cases = {}
    
    for engine in ['wobble', 'circus-omp',  'tdc-peeler', 'kilosort-matching', 'nearest']:
    # for engine in [ 'tdc-peeler']:
        for data_key in datasets.keys():
            recording, gt_sorting = datasets[data_key]
            noise_levels = si.get_noise_levels(recording)

            cases[(engine, data_key)] = {
                "label": f"{engine} {data_key}",
                "dataset": data_key,
                "params" : {
                    "templates" : templates[data_key],
                    "method" : engine,
                    "method_kwargs" : {}},
            }

            if engine == "kilosort-matching":
                cases[(engine, data_key)]["params"]["method_kwargs"]["spatial_components"] = spatial[data_key]
                cases[(engine, data_key)]["params"]["method_kwargs"]["temporal_components"] = temporal[data_key]
            
            if engine in ['tdc-peeler', 'nearest']:
                cases[(engine, data_key)]["params"]["method_kwargs"]["noise_levels"] = noise_levels
    
    
    if erase:
        if study_folder.exists():
            shutil.rmtree(study_folder)
        study = MatchingStudy.create(study_folder, datasets=datasets, cases=cases)
        study.compute_metrics()
    else:
        study = MatchingStudy(study_folder)

    study.run(verbose=True)
    study.compute_results(with_collision=True)

if __name__ == "__main__":
    global_name = 'matching_drift'

    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixels1-128_250_100.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    dataset_name = 'Neuropixels1-384_500_1800.s'

    motion_folder = base_path / global_name / dataset_name / 'motion'
    study_folder = base_path / global_name / dataset_name / 'study'

    run_study(motion_folder, study_folder, dataset_name, erase=True)
    # push_to_slurm(run_study, motion_folder, study_folder,  dataset_name, erase=True)


    # study = MatchingStudy(study_folder)
    # print(study)
    # si.set_global_job_kwargs(n_jobs=0.8, chunk_duration="0.2s") 

    # study.run(case_keys=None, keep=True, verbose=True)
    # study.compute_results()
