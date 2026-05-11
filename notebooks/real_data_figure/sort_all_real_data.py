"""
Based on code from https://github.com/MattNolanLab/nolanlab-ephys

The IBL data is the file
    sub-UCLA034_ses-3537d970-f515-4786-853f-23de525e110f_desc-raw_ecephys.nwb
from DANDI dataset 000409 - https://dandiarchive.org/dandiset/000409

The UCL data is the file
    AL032_2020-01-07
from https://rdr.ucl.ac.uk/articles/dataset/Chronic_recordings_from_Neuropixels_2_0_probes_in_mice/24411841
This needs to be untarred into a folder.

The Dus data is the file
    A3720-191126.nwb
from the DANDI dataset 000939 - https://dandiarchive.org/dandiset/000939

For this code to run, put all files in the "raw_data" folder and change the "repo_folder" below, to point at
your local copy of this repo. Your file organisation should look like

sorting_components_benchmark_paper/   <-- `repo_folder` points here
   notebooks/
       real_data_figure/
           sort_all_real_data.py
           raw_data/
               sub-UCLA034_ses-3537d970-f515-4786-853f-23de525e110f_desc-raw_ecephys.nwb
               A3702-191126.nwb
               AL032_2020-01-07/
                   ???
            analyzers/
            curation_results/

`cd` to the `real_data_figure` folder and run
>>> uv run sort_all_real_data.py

After this has run the `analyzers` folder should contain the following 12 analyzers:

analyzers/
    Duszkiewicz_kilosort4_no_motion_correction_analyzer
    Duszkiewicz_lupin_no_motion_correction_analyzer
    Duszkiewicz_spykingcircus2_no_motion_correction_analyzer
    Duszkiewicz_tridesclous2_no_motion_correction_analyzer
    IBL_kilosort4_motion_correction_analyzer
    IBL_lupin_motion_correction_analyzer
    IBL_spykingcircus2_motion_correction_analyzer
    IBL_tridesclous2_motion_correction_analyzer
    ucl_kilosort4_no_motion_correction_analyzer
    ucl_lupin_no_motion_correction_analyzer
    ucl_spykingcircus2_no_motion_correction_analyzer
    ucl_tridesclous2_no_motion_correction_analyzer 

"""

import spikeinterface.full as si
from pathlib import Path
from sort_one_piece_of_data import do_sorting

# edit this to point to the `sorting_components_benchmark_paper` on your own computer
repo_folder = Path("/home/nolanlab/fromgit/sorting_components_benchmark_paper/")

raw_data_folder = repo_folder / "notebooks/real_data_figure/raw_data"
analyzers_folder = repo_folder / "notebooks/real_data_figure/raw_data"

# NP1 data from IBL
np1_protocols = [
        'kilosort4_motion_correction',
        'lupin_motion_correction',
        'spykingcircus2_motion_correction'
        'tridesclous2A_motion_correction'
    ]
np1_data_folder = raw_data_folder / 'sub-UCLA034_ses-3537d970-f515-4786-853f-23de525e110f_desc-raw_ecephys.nwb'
np1_analyzer_folders = [
    analyzers_folder / f"IBL_{protocol}_analyzer" for protocol in np1_protocols
]

recording = si.read_nwb_recording(np1_data_folder, electrical_series_path = 'acquisition/ElectricalSeriesProbe00AP').frame_slice(start_frame=0, end_frame=30000*60)
for protocol_name, analyzer_folder in zip(np1_protocols, np1_analyzer_folders):
    do_sorting(recording, analyzer_folder, protocol_name)

# NP2 data from UCL
np2_protocols = [
        'kilosort4_no_motion_correction',
        'lupin_no_motion_correction',
        'spykingcircus2_no_motion_correction'
        'tridesclous2A_no_motion_correction'
    ]
np2_data_folder = raw_data_folder / 'AL032_2020-01-07'
np2_analyzer_folders = [
    analyzers_folder / f"ucl_{protocol}_analyzer" for protocol in np1_protocols
]

recording = si.read_cbin_ibl(np2_data_folder).frame_slice(start_frame=0, end_frame=30000*60)
for protocol_name, analyzer_folder in zip(np2_protocols, np2_analyzer_folders):
    do_sorting(recording, analyzer_folder, protocol_name)

# CN data from Adrian

cn_protocols = [
        'kilosort4_no_motion_correction',
        'lupin_no_motion_correction',
        'spykingcircus2_no_motion_correction'
        'tridesclous2A_no_motion_correction'
    ]
cn_analyzer_folders = [
    analyzers_folder / f"Duszkiewicz_{protocol}_analyzer" for protocol in cn_protocols
]
cn_data_folder = raw_data_folder / 'A3702-191126.nwb'
recording = si.read_nwb_recording(cn_data_folder)
for protocol_name, analyzer_folder in zip(cn_protocols, cn_analyzer_folders):
    do_sorting(recording, analyzer_folder, protocol_name)
