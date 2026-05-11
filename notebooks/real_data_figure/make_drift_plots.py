import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import spikeinterface.full as si

from pathlib import Path

repo_folder = Path("/home/nolanlab/fromgit/sorting_components_benchmark_paper/")
real_data_figure_folder = repo_folder / "notebooks/real_data_figure"
analyzers_folder = real_data_figure_folder / "analyzers"
drift_maps_folder = real_data_figure_folder / "drift_maps_and_probes"

bombcell_labels = ['good', 'mua', 'noise', 'non_soma_good', 'non_soma_mua']

protocol = 'no_motion_correction'

FONT_SIZE = 18

plotting_settings = {
    'ucl': {
        'protocol': 'no_motion_correction',
        'vmin': -600,
        'scatter_decimate': 20,
        'cbar_ticks': [-600,-500,-400,-300,-200,-100,0],
        'cbar_ticklabels': ['600','','400','','200','','0'],
        'yticklabels': ['','2.9', '', '3.1', '', '3.3', '', '3.5'],
        'xticks_s': [0,600,1200,1800],
    },
    'IBL': {
        'protocol': 'motion_correction',
        'vmin': -457.829994,
        'scatter_decimate': 20,
        'cbar_ticks': [-600,-500,-400,-300,-200,-100,0], 
        'cbar_ticklabels': ['600','','400','','200','','0'],
        'yticklabels': ['', '0', '', '1', '', '2', '', '3', ''],
        'xticks_s': [0,900,1800,2700,3600],
    },
    'Duszkiewicz': {
        'protocol': 'no_motion_correction',
        'vmin': -380,
        'scatter_decimate': 5,
        'cbar_ticks': [-400,-300,-200,-100,0],
        'cbar_ticklabels': [400,300,200,100,0],
        'yticklabels': ['', '', '0.2', '', '0.4', '', '0.6', '', '0.8'],
        'xticks_s': [0,3000,6000,9000,12000],
    }
}

for dataset_name, dataset_settings in plotting_settings.items():
   
    protocol = dataset_settings['protocol']
   
    analyzer_path =  analyzers_folder / f'{dataset_name}_kilosort4_{protocol}_analyzer'
    if analyzer_path.is_dir():
        analyzer = si.load_sorting_analyzer(analyzer_path)
    else:
        analyzer = si.load_sorting_analyzer(str(analyzer_path) + '.zarr')

    print(analyzer.get_total_duration())
        
    bombcell_unit_labels = si.bombcell_label_units(analyzer, split_non_somatic_good_mua=True)['bombcell_label'].values
    good_units = analyzer.unit_ids[bombcell_unit_labels == 'good']
    analyzer_good = analyzer.select_units(good_units)
    
    cmap_name = 'inferno'
    
    fig = si.plot_drift_raster_map(
        sorting_analyzer=analyzer_good, 
        cmap=cmap_name, 
        alpha=0.10,
        scatter_decimate=dataset_settings['scatter_decimate'], 
        figsize=(8,4.5)
    )
    # 1. Define your parameters
    vmin = dataset_settings['vmin']
    vmax = 0
    
    # 2. Create the Normalization and Mappable objects
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    sm = cm.ScalarMappable(cmap=plt.get_cmap(cmap_name), norm=norm)
    sm.set_array([]) # Required for the colorbar to initialize correctly
    
    # 3. Access your existing figure/axes and add the colorbar
    # Assuming 'fig' is your figure object
    ax = fig.figure.get_axes()[0] 
    cbar = fig.figure.colorbar(sm, ax=ax)
    
    # 2. Find the scatter plot and rasterize it
    # In Matplotlib, scatter plots are usually 'PathCollection' objects
    for artist in ax.get_children():
        if isinstance(artist, plt.matplotlib.collections.PathCollection):
            artist.set_rasterized(True)
    
    # 4. (Optional) Add a label
    cbar_ticks = dataset_settings['cbar_ticks']
    #cbar_ticks = [-80,-60,-40,-20,0]
    cbar.set_label('Abs peak amplitude [uV]', fontsize=FONT_SIZE)
    cbar.set_ticklabels(dataset_settings['cbar_ticklabels']) 
    cbar.ax.tick_params(labelsize=FONT_SIZE) # Font size for colorbar ticks
    
    ax.set_ylabel('Depth [mm]', fontsize=FONT_SIZE)
    ax.set_yticklabels(dataset_settings['yticklabels'], fontsize=FONT_SIZE)
    
    xticks_s = dataset_settings['xticks_s']
    ax.set_xticks(xticks_s)
    ax.set_xticklabels([int(xtick/60) for xtick in xticks_s], fontsize=FONT_SIZE)
    ax.set_xlabel('Time [min]', fontsize=FONT_SIZE)
    
    ax.set_title(label=None)
    
    fig.figure.savefig(drift_maps_folder / f'{dataset_name}_drift.svg',  bbox_inches='tight')
