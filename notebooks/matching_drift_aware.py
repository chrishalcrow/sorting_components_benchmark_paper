import spikeinterface.full as si
from pathlib import Path
import numpy as np
from spikeinterface.sortingcomponents.tools import remove_empty_templates
from spikeinterface.benchmark.benchmark_matching import MatchingStudy

from configuration import base_path
from slurm_tools import push_to_slurm
from dataset import get_dataset


from spikeinterface.benchmark.benchmark_motion_estimation import get_gt_motion_from_unit_displacement
from spikeinterface.generation.drift_tools import DriftingTemplates
from spikeinterface.sortingcomponents.motion import interpolate_motion


def run_study(motion_folder, study_folder, dataset_name, erase=True):

    study_folder = Path(study_folder)

    si.set_global_job_kwargs(n_jobs=20, chunk_duration="1s")

    static, drifting, sorting, analyzer_static, analyzer_drifting, extra_infos = get_dataset(dataset_name, with_extra_info=True)


    rec = static
    channel_locations = rec.get_channel_locations()
    duration = rec.get_duration()
    # motion bins size
    bin_s = 0.5
    temporal_bins_s = np.arange(0, duration, bin_s)
    spatial_bins_um = np.linspace(np.min(channel_locations[:, 1]), np.max(channel_locations[:, 1]), 4)

    gt_motion = get_gt_motion_from_unit_displacement(
        extra_infos["unit_displacements"],
        extra_infos["displacement_sampling_frequency"],
        extra_infos["unit_locations"],
        temporal_bins_s,
        spatial_bins_um,
        direction_dim=1,
    )

    
    gt_dense_templates = extra_infos["templates"]

    interpolate_motion_kwargs = dict(border_mode="force_extrapolate", spatial_interpolation_method="kriging", sigma_um=20.0, p=2)
    corrected = interpolate_motion(drifting, gt_motion, **interpolate_motion_kwargs)

    study_folder = study_folder

    datasets = {
        "static" : (static, sorting),
        "corrected" : (corrected, sorting),
        "drifting" : (drifting, sorting),
    }

    gt_dense_templates = extra_infos["templates"]
    noise_levels = si.get_noise_levels(rec, return_in_uV=False)
    sparsity = si.compute_sparsity(gt_dense_templates, noise_levels=noise_levels,
                                   method='snr', amplitude_mode='peak_to_peak', threshold=0.25)
    gt_sparse_templates = gt_dense_templates.to_sparse(sparsity)


    all_estimated_template = {}
    for dataset in ('static', 'corrected'):

        recording, gt_sorting = datasets[dataset]
        spikes = gt_sorting.to_spike_vector()
        # few_spikes = spikes[::10]
        fs = recording.sampling_frequency
        nbefore = int(1.5 * fs / 1000)
        nafter = int(3.0 * fs / 1000)
        # this is dense
        templates_array = si.estimate_templates(
            recording, spikes, 
            gt_sorting.unit_ids, nbefore, nafter, return_in_uV=False, job_name=None, operator="average",
        )
        
        dense_templates = si.Templates(
            templates_array=templates_array,
            sampling_frequency=fs,
            nbefore=nbefore,
            sparsity_mask=None,
            channel_ids=recording.channel_ids,
            unit_ids=gt_sorting.unit_ids,
            probe=recording.get_probe(),
            is_in_uV=False,
            )
        
        sparse_templates = dense_templates.to_sparse(sparsity)
        all_estimated_template[dataset] = sparse_templates

    cases = {}

    # we remove the *same* small ones on drifting/static
    not_empty = sparsity.mask.sum(axis=1) > 0
    gt_sparse_templates = gt_sparse_templates.select_units(gt_sparse_templates.unit_ids[not_empty])
    for dataset in all_estimated_template.keys():
        templates = all_estimated_template[dataset]
        all_estimated_template[dataset] = templates.select_units(templates.unit_ids[not_empty])


    engine = 'tdc-peeler'
    
    for dataset in datasets.keys():

        print('Setup ', engine, dataset)
        recording, gt_sorting = datasets[dataset]

        noise_levels = si.get_noise_levels(recording, return_in_uV=False)

        # templates are sparse
        if dataset  == "static":
            # 2 cases : estimated and GT

            method_kwargs = dict(
                noise_levels=noise_levels,
            )

            templates = all_estimated_template["static"]
            cases[dataset + '_estimated'] = {
                "label": f"{engine} {dataset}",
                "dataset": dataset,
                "params" : {
                    "templates": templates,
                    "method" : engine,
                    "method_kwargs" : method_kwargs
                },
            }

            cases[dataset + '_GT'] = {
                "label": f"{engine} {dataset}",
                "dataset": dataset,
                "params" : {
                    "templates": gt_sparse_templates,
                    "method" : engine,
                    "method_kwargs" : method_kwargs
                },
            }



        elif dataset == "corrected":
            templates = all_estimated_template["corrected"]

            method_kwargs = dict(
                noise_levels=noise_levels,
            )

            cases[dataset] = {
                "label": f"{engine} {dataset}",
                "dataset": dataset,
                "params" : {
                    "templates": templates,
                    "method" : engine,
                    "method_kwargs" : method_kwargs
                },
            }

        elif dataset == "drifting":
            # 2 cases : estimated interpolated and GT

            motion_step_um = 1.0
            min_, max_ = gt_motion.get_boundaries()
            steps = np.arange(min_, max_+motion_step_um/2, motion_step_um)
            displacements = np.zeros((steps.size, 2), dtype="float64")
            displacements[:, gt_motion.dim] = steps

            # estimated
            templates = all_estimated_template["static"]
            drifting_templates = DriftingTemplates.from_static_templates(templates)
            print('precompute_displacements')
            drifting_templates.precompute_displacements(displacements, interpolation_method="cubic")
            print('precompute_displacements DONE', drifting_templates.templates_array_moved.shape)
            # drifting_templates.precompute_displacements(displacements, interpolation_method="linear")
            

            method_kwargs = dict(
                drifting_templates=drifting_templates,
                motion_aware=True,
                motion=gt_motion,
                interpolation_time_bin_size_s=0.5,
                noise_levels=noise_levels,
            )

            cases[(dataset+"_interploated")] = {
                "label": f"{engine} {dataset} interploated",
                "dataset": dataset,
                "params" : {
                    "templates" :drifting_templates,
                    "method" : engine,
                    "method_kwargs" : method_kwargs
                },
            }

            # GT drifting_templates
            folder = base_path/ "SimulatedDatasetsCache" / dataset_name / "drifting_recording"
            rec = si.load(base_path/ "SimulatedDatasetsCache" / dataset_name / "drifting_recording" / "provenance.pkl", base_folder=folder)
            drifting_templates  = rec.drifting_templates

            # apply the same unit select in place
            drifting_templates.templates_array = drifting_templates.templates_array[not_empty, :, :]
            drifting_templates.templates_array_moved = drifting_templates.templates_array_moved[:, not_empty, :, :]
            drifting_templates.unit_ids = drifting_templates.unit_ids[not_empty]

            method_kwargs = dict(
                drifting_templates=drifting_templates,
                motion_aware=True,
                motion=gt_motion,
                interpolation_time_bin_size_s=0.5,
                noise_levels=noise_levels,
            )

            cases[(dataset+"_GT")] = {
                "label": f"{engine} {dataset} GT",
                "dataset": dataset,
                "params" : {
                    "templates": drifting_templates,
                    "method" : engine,
                    "method_kwargs" : method_kwargs
                },
            }



    if erase:
        import shutil
        if study_folder.exists():
            shutil.rmtree(study_folder)
        study = MatchingStudy.create(study_folder, datasets=datasets, cases=cases)
    else:
        study = MatchingStudy(study_folder)


    study.run(verbose=True)
    # study.compute_results(with_collision=True)
    study.compute_results(with_collision=False)
    study.compute_metrics()


if __name__ == "__main__":
    global_name = 'matching_drift_aware'
    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixels1-128_250_100.s'
    dataset_name = 'Neuropixels1-384_500_600.s'

    motion_folder = base_path / global_name / dataset_name / 'motion'
    study_folder = base_path / global_name / dataset_name / 'study'


    run_study(motion_folder, study_folder, dataset_name, erase=True)

    # push_to_slurm(run_study, motion_folder, study_folder,  dataset_name, erase=True)

