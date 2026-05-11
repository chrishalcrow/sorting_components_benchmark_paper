"""
Based on code from https://github.com/MattNolanLab/nolanlab-ephys

The IBL data is the file
    sub-UCLA034_ses-3537d970-f515-4786-853f-23de525e110f_desc-raw_ecephys.nwb
from DANDI dataset 000409 - https://dandiarchive.org/dandiset/000409

The UCL data is the file
    AL032_2020-01-07
from https://rdr.ucl.ac.uk/articles/dataset/Chronic_recordings_from_Neuropixels_2_0_probes_in_mice/24411841

The Dus data is the fil
    ???
from the DANDI dataset 000939 - https://dandiarchive.org/dandiset/000939
"""
import spikeinterface.full as si
import pandas as pd
from pathlib import Path
from .sort_one_piece_of_data import do_sorting

repo_folder = Path("/Users/christopherhalcrow/Work/fromgit/sorting_components_benchmark_paper/")
raw_data_folder = repo_folder / "notebooks/real_data_figure/raw_data"
analyzers_folder = repo_folder / "notebooks/real_data_figure/raw_data"

# NP1 data from IBL

np1_protocols = [
        'kilosort4_motion_correction',
        'lupin_motion_correction',
        'spykingcircus2_motion_correction'
        'tridesclous2A_motion_correction'
    ]
np1_data_folder = ""
np1_analyzer_folders = [
    analyzers_folder / f"ibl_{protocol}_analyzer" for protocol in np1_protocols
]

for protocol_name, analyzer_folder in zip(np1_protocols, np1_analyzer_folders):
    recording = ...
    do_sorting(recording, analyzer_folder, protocol_name)

# NP2 data from UCL

np2_protocols = [
        'kilosort4_no_motion_correction',
        'lupin_no_motion_correction',
        'spykingcircus2_no_motion_correction'
        'tridesclous2A_no_motion_correction'
    ]
np2_data_folder = ""
np2_analyzer_folders = [
    analyzers_folder / f"ucl_{protocol}_analyzer" for protocol in np1_protocols
]

for protocol_name, analyzer_folder in zip(np2_protocols, np2_analyzer_folders):
    recording = ...
    do_sorting(recording, analyzer_folder, protocol_name)

# CN data from Adrian

cn_protocols = [
        'kilosort4_no_motion_correction',
        'lupin_no_motion_correction',
        'spykingcircus2_no_motion_correction'
        'tridesclous2A_no_motion_correction'
    ]
cn_analyzer_folders = [
    analyzers_folder / f"cn_{protocol}_analyzer" for protocol in cn_protocols
]


for protocol_name, analyzer_folder in zip(cn_protocols, cn_analyzer_folders):
    recording = ...
    do_sorting(recording, analyzer_folder, protocol_name)




