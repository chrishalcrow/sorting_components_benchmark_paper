all_curation_data = []

for rec_name, recording, list_of_protocols, in zip(['np2', 'np1'], [np2_recording, np1_recording], [np2_protocols, np1_protocols] ):
    for protocol_name in list_of_protocols:

        analyzer_path = f"{rec_name}_srt-{protocol_name}_analyzer"
        analyzer = do_sorting(recording, analyzer_path, protocol_name)

        curation_data = get_automated_labels(analyzer)

        all_curation_data.append(curation_data)    

curation_data_df = pd.DataFrame(all_curation_data, columns=[])
curation_data_df.to_csv('all_curation_data.csv')


