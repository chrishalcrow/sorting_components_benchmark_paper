import spikeinterface.full as si
# import spikeinterface.generate as generate_drifting_recording
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

import pickle

from configuration import base_path

# from spikeinterface.sortingcomponents.tools import remove_empty_templates
# from spikeinterface.core.node_pipeline import sorting_to_peaks
# from spikeinterface.sortingcomponents.benchmark.benchmark_clustering import ClusteringStudy



def create_dataset(dataset_name, seed=None):

    keys = dataset_name.split('_')

    probe_name = keys[0]
    num_units = int(keys[1])
    duration = keys[2]
    assert duration.endswith('s')
    duration = float(duration[:-1])

    if probe_name == 'Neuropixels1-384':
        distribution = "multimodal"
        num_modes = 3
    elif probe_name == 'Neuropixels1-128':
        distribution = "multimodal"
        num_modes = 2
    else:
        distribution="uniform"
        num_modes = 1

    # to make backward compatible
    if seed is None:
        seed = 2205

    # gama not too much at zero (shape=1.01)
    rng = np.random.default_rng(seed=seed)
    firing_rates = rng.gamma(shape=1.01, scale=5,size=num_units)

    static, drifting, sorting, extra_infos = si.generate_drifting_recording(
        probe_name=probe_name,
        num_units=num_units,
        duration=duration,
        seed=seed,
        extra_outputs=True,
        generate_unit_locations_kwargs=dict(
            margin_um=20.0,
            minimum_z=5.0,
            maximum_z=50.0,
            minimum_distance=18.0,
            max_iteration=100,
            distance_strict=False,
            # distribution="uniform",
            distribution=distribution,
            num_modes=num_modes,
        ),
        generate_displacement_vector_kwargs=dict(
            displacement_sampling_frequency=5.0,
            drift_start_um=[0, -40],
            drift_stop_um=[0, 40],
            drift_step_um=1,
            motion_list=[
                dict(
                    drift_mode="zigzag",
                    # amplitude_factor=0.4,
                    amplitude_factor=0.2,
                    non_rigid_gradient=None,
                    # t_start_drift=60.0,
                    t_start_drift=None,
                    t_end_drift=None,
                    period_s=200,
                ),
                dict(
                    drift_mode="random_walk",
                    # amplitude_factor=0.6,
                    amplitude_factor=0.8,
                    non_rigid_gradient=None,
                    # t_start_drift=60.0,
                    t_start_drift=None,
                    t_end_drift=None,
                ),
            ],
        ),
        generate_templates_kwargs=dict(
            ms_before=1.5,
            ms_after=3.0,
            mode="ellipsoid",
            unit_params=dict(
                # alpha=(100.0, 500.0),
                # alpha=(50.0, 250.0),
                alpha=(75.0, 350.0),
                spatial_decay=(10., 35.),
                ellipse_shrink=(0.4, 1),
                ellipse_angle=(0, np.pi * 2),
            ),
        ),
        generate_sorting_kwargs=dict(
            firing_rates=firing_rates,
            refractory_period_ms=4.0
        ),
        generate_noise_kwargs=dict(
            noise_levels=(6.0, 8.0),
            spatial_decay=25.0
        ),

    )

    return static, drifting, sorting, extra_infos



def get_dataset(dataset_name, with_extra_info=False, seed=None):

    if seed is None:
        dataset_folder = base_path / 'SimulatedDatasetsCache' / dataset_name
    else:
        dataset_folder = base_path / 'SimulatedDatasetsCache' / f"{dataset_name}_seed{seed}"

    static_rec_folder = dataset_folder / 'static_recording'
    drifting_rec_folder = dataset_folder / 'drifting_recording'
    sorting_folder = dataset_folder / 'sorting_recording'
    static_analyzer_folder =  dataset_folder / 'static_gt_analyzer'
    drifting_analyzer_folder =  dataset_folder / 'drifting_gt_analyzer'

    
    if not static_rec_folder.exists():
        static, drifting, sorting, extra_infos = create_dataset(dataset_name, seed=seed)

        dataset_folder.mkdir(parents=True, exist_ok=True)

        # save extra info using pickle
        with open(dataset_folder / "extra_info.pickle", mode="wb") as f:
            pickle.dump(extra_infos, f)


        static_saved = static.save(folder=static_rec_folder)
        drifting_saved = drifting.save(folder=drifting_rec_folder)
        sorting_saved = sorting.save(folder=sorting_folder)


        max_channel_index = sorting.get_property("max_channel_index")
        channel_locations = static.get_channel_locations()
        sparsity_mask = np.zeros((sorting.unit_ids.size, channel_locations.shape[0]))
        distances = np.linalg.norm(channel_locations[:, np.newaxis] - channel_locations[np.newaxis, :], axis=2)
        radius_um = 100.
        for unit_ind, unit_id in enumerate(sorting.unit_ids):
            chan_ind = max_channel_index[unit_ind]
            (chan_inds,) = np.nonzero(distances[chan_ind, :] <= radius_um)
            sparsity_mask[unit_ind, chan_inds] = True
        sparsity = si.ChannelSparsity(sparsity_mask, sorting.unit_ids, static.channel_ids)




        analyzer_static = si.create_sorting_analyzer(sorting_saved, static_saved, sparsity=sparsity,
                                                     format="memory",
                                                    #  format="binary_folder", folder=static_analyzer_folder, 
                                                     )
        analyzer_drifting = si.create_sorting_analyzer(sorting_saved, drifting_saved, sparsity=sparsity,
                                                       format="memory",
                                                    #    format="binary_folder", folder=drifting_analyzer_folder,
                                                       )
        
        for analyzer in (analyzer_static, analyzer_drifting):
            analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
            analyzer.compute("waveforms")
            analyzer.compute("templates")
            analyzer.compute("noise_levels")
            analyzer.compute("unit_locations")
            analyzer.compute("isi_histograms", window_ms=50., bin_ms=1., method="numba")
            analyzer.compute("correlograms", window_ms=50., bin_ms=1.)
            analyzer.compute("template_similarity", method="l2")
            analyzer.compute("principal_components", n_components=3, mode='by_channel_global', whiten=True)
            # sorting_analyzer.compute("principal_components", n_components=3, mode='by_channel_local', whiten=True, **job_kwargs)
            analyzer.compute("quality_metrics", metric_names=["snr", "firing_rate"])
            analyzer.compute("spike_amplitudes")
        
        analyzer_static = analyzer_static.save_as(format="binary_folder", folder=static_analyzer_folder, )
        analyzer_drifting = analyzer_drifting.save_as(format="binary_folder", folder=drifting_analyzer_folder, )


    else:
        static_saved = si.load(static_rec_folder)
        drifting_saved = si.load(drifting_rec_folder)
        sorting_saved = si.load(sorting_folder)
        analyzer_static = si.load_sorting_analyzer(static_analyzer_folder)
        analyzer_drifting = si.load_sorting_analyzer(drifting_analyzer_folder)

        with open(dataset_folder / "extra_info.pickle", mode="rb") as f:
            extra_infos =  pickle.load(f)


    if  not with_extra_info:
        return static_saved, drifting_saved, sorting_saved, analyzer_static, analyzer_drifting
    else:
        return static_saved, drifting_saved, sorting_saved, analyzer_static, analyzer_drifting, extra_infos


def open_sigui(dataset_name, static=True):

    static_saved, drifting_saved, sorting_saved, analyzer_static, analyzer_drifting = get_dataset(dataset_name)

    if static:
        analyzer = analyzer_static
    else:
        analyzer = analyzer_drifting

    si.plot_sorting_summary(analyzer, backend="spikeinterface_gui")

    

if __name__ == '__main__':
    # si.set_global_job_kwargs(n_jobs=-2, progress_bar=True, chunk_duration='1s', pool_engine='process', mp_context="spawn")
    si.set_global_job_kwargs(n_jobs=-2, progress_bar=True, chunk_duration='1s', pool_engine='process', mp_context="fork")
    # dataset_name = 'Neuronexus-32_50_300.s'
    # dataset_name = 'Neuropixels1-128_250_100.s'
    # dataset_name = 'Neuropixels1-384_500_600.s'
    # dataset_name = 'Neuropixels1-384_500_1800.s'

    
    # dataset_name = 'cambridgeneurotech#ASSY-37-H7b_50_1800.s'  # 32 chans
    # dataset_name = 'tetrode_8_1800.s'
    dataset_name = 'Neuropixels2-128_250_1800.s'

    

    # get_dataset(dataset_name)
    get_dataset(dataset_name, seed=2205)

    # seeds = [ 2205, 2406, 2308, 1110, 2512]
    # for seed in seeds:
    #     get_dataset(dataset_name, seed=seed)


