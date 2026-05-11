"""
Generates curation results from computed analyzers.

Once you have the analyzers, run this code by `cd`ing into the `real_data_figure` 
folder, then running
>>> uv run generate_curation_data.py

"""

import spikeinterface.full as si
import numpy as np
import pandas as pd
from pathlib import Path

repo_folder = Path("/home/nolanlab/fromgit/sorting_components_benchmark_paper/")
real_data_figure_folder = repo_folder / "notebooks/real_data_figure"
analyzers_folder = real_data_figure_folder / "analyzers"

dataset_protocols = {
    'IBL': ['kilosort4_motion_correction', 'lupin_motion_correction', 'tridesclous2_motion_correction','spykingcircus2_motion_correction'],
    'ucl': ['kilosort4_no_motion_correction', 'lupin_no_motion_correction', 'tridesclous2_no_motion_correction','spykingcircus2_no_motion_correction'],
    'Duszkiewicz': ['kilosort4_no_motion_correction', 'lupin_no_motion_correction', 'tridesclous2_no_motion_correction','spykingcircus2_no_motion_correction'],
}

bombcell_labels = ['good', 'mua', 'noise', 'non_soma_good', 'non_soma_mua']
unitrefine_labels = ['sua', 'mua', 'noise']
merge_presets = ['slay']

for dataset_name, protocols in dataset_protocols.items():
    bombcell_results = []
    unitrefine_results = []
    all_protocols_data = []
    for protocol in protocols:

        analyzer_path = analyzers_folder / f"{dataset_name}_{protocol}_analyzer"
        if analyzer_path.is_dir():
            analyzer = si.load_sorting_analyzer(analyzer_path)
        else:
            analyzer = si.load_sorting_analyzer(str(analyzer_path) + '.zarr')
        
        bombcell_unit_label = si.bombcell_label_units(analyzer, split_non_somatic_good_mua=True)['bombcell_label'].values
        bombcell_results = {label: np.sum(bombcell_unit_label == label) for label in bombcell_labels}

        # You need to donwload the UnitRefine models `noise_neural_classifier_lightweight` and `sua_mua_classifier_lightweight` from
        # https://huggingface.co/AnoushkaJain3
        unitrefine_unit_label = si.unitrefine_label_units(analyzer, noise_neural_classifier='/home/nolanlab/Downloads/noise_neural_classifier_lightweight', sua_mua_classifier='/home/nolanlab/Downloads/sua_mua_classifier_lightweight')
        unitrefine_results = {label: np.sum(unitrefine_unit_label['unitrefine_label'] == label) for label in unitrefine_labels}

        merge_results = {merge_preset: len(si.compute_merge_unit_groups(analyzer, preset=merge_preset)) for merge_preset in merge_presets}

        protocol_data = [
            protocol,
            analyzer.get_num_units(),
            bombcell_results['good'] + bombcell_results['non_soma_good'],
            unitrefine_results['sua'],
            bombcell_results['mua'] + bombcell_results['non_soma_mua'],
            unitrefine_results['mua'],
            merge_results['slay'],
            bombcell_results['noise'],
            unitrefine_results['noise'],
        ]

        all_protocols_data.append(protocol_data)

    results = pd.DataFrame(all_protocols_data, columns=["sorter", "total units", "bombcell good", "unitrefine sua", "bombcell mua", "unitrefine mua", "# slay merges", "bombcell noise", "unitrefine noise"], index=None)

    results.to_csv(real_data_figure_folder / f"curation_results/{dataset_name}_results.csv", index=False)  

    # render for typst rendering
    for row in results.iterrows():
        for cell in row[1]:
            print(f"[{cell}], ", end="")
        print("")
