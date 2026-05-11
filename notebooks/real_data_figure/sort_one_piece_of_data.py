"""
Based on code from https://github.com/MattNolanLab/nolanlab-ephys
"""
import spikeinterface.full as si

protocols = {
    "kilosort4_no_motion_correction": {
        "preprocessing": {
        },
        "sorting": {
            "sorter_name": "kilosort4",
            "do_correction": False,
            "use_binary_file": False,
        },
        "preprocessing_for_analyzer": {
            "common_reference": {},
            "bandpass_filter": {},
        },
    },
    "spykingcircus2_no_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "spykingcircus2",
            "apply_motion_correction": False,
            "cache_preprocessing": {"mode": "folder", "folder": "sk2_pre"},
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
    "tridesclous2A_no_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "tridesclous2",
            "cache_preprocessing_mode": "folder",
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
    "lupin_no_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "spykingcircus2",
            "apply_motion_correction": False,
            "cache_preprocessing": {"mode": "folder", "folder": "sk2_pre"},
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
    "kilosort4_motion_correction": {
        "preprocessing": {
        },
        "sorting": {
            "sorter_name": "kilosort4",
            "do_correction": True,
            "use_binary_file": False,
        },
        "preprocessing_for_analyzer": {
            "common_reference": {},
            "bandpass_filter": {},
        },
    },
    "spykingcircus2_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "spykingcircus2",
            "apply_motion_correction": True,
            "cache_preprocessing": {"mode": "folder", "folder": "sk2_pre"},
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
    "tridesclous2A_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "tridesclous2",
            "cache_preprocessing_mode": "folder",
            "apply_motion_correction": True,
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
    "lupin_no_motion_correction": {
        "preprocessing": {},
        "sorting": {
            "sorter_name": "spykingcircus2",
            "apply_motion_correction": True,
            "cache_preprocessing": {"mode": "folder", "folder": "sk2_pre"},
        },
        "preprocessing_for_analyzer": {
            "bandpass_filter": {},
            "common_reference": {},
        },
    },
}

postprocessing_extensions_to_compute = {
    "unit_locations": {},
    "random_spikes": {},
    "noise_levels": {},
    "waveforms": {},
    "templates": {},
    "spike_amplitudes": {"peak_sign": "both"},
    "amplitude_scalings": {},
    "isi_histograms": {},
    "spike_locations": {"peak_sign": "both"},
    "correlograms": {},
    "template_similarity": {"method": "l2"},
    "quality_metrics": {},
    "template_metrics": {},
}

def do_sorting(recording, analyzer_path, protocol_name, n_jobs=8):

    si.set_global_job_kwargs(n_jobs=n_jobs)

    protocol_info = protocols[protocol_name]

    pp_recording = si.apply_preprocessing_pipeline(
        recording, protocol_info["preprocessing"]
    )
    sorting = si.run_sorter(
        recording=pp_recording,
        **protocol_info["sorting"],
        remove_existing_folder=True,
        verbose=True,
    )

    preprocessed_recording_for_analyzer = si.apply_preprocessing_pipeline(
        recording, protocol_info["preprocessing_for_analyzer"]
    )

    analyzer = si.create_sorting_analyzer(
        recording=preprocessed_recording_for_analyzer,
        sorting=sorting,
        folder=analyzer_path,
        format="binary_folder",
        peak_sign="both",
        radius_um=70,
    )

    analyzer.compute(postprocessing_extensions_to_compute)
