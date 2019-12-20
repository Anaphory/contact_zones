if __name__ == '__main__':
    from src.util import load_from, transform_weights_from_log, transform_p_from_log, \
        read_languages_from_csv
    from src.preprocessing import compute_network
    from src.postprocessing import compute_dic, match_zones
    from src.plotting import plot_posterior_frequency, plot_trace_lh, plot_trace_recall_precision, \
        plot_zone_size_over_time, plot_dics, plot_correlation_weights, plot_histogram_weights, plot_correlation_p, \
        plot_posterior_frequency4

    import numpy as np
    import os

    PATH = '../../../../' # relative path to contact_zones_directory
    PATH_SA = f'{PATH}/src/experiments/south_america/'


    TEST_ZONE_DIRECTORY = 'results/contact_zones/2019-11-26_15-15/'

    # plotting directories
    PLOT_PATH = f'{PATH}plots/south_america/'
    if not os.path.exists(PLOT_PATH): os.makedirs(PLOT_PATH)

    # MAP SETTINGS
    PROJ4_STRING = '+proj=eqdc +lat_0=-32 +lon_0=-60 +lat_1=-5 +lat_2=-42 +x_0=0 +y_0=0 +ellps=aust_SA +units=m +no_defs '
    GEOJSON_MAP_PATH = 'data/map/ne_50m_land.geojson'
    GEOJSON_RIVER_PATH = 'data/map/ne_50m_rivers_lake_centerlines_scale_rank.geojson'

    # Zone, ease and number of runs
    n_zone = 3
    n_zone_file = 5
    run = 0
    n_zones = [1, 2, 3, 4, 5, 6, 7, 8]

    # general parameters
    ts_posterior_freq = 0.8
    ts_lower_freq = 0.5
    burn_in = 0.8


    for n_zone in n_zones:

        scenario_plot_path = f'{PLOT_PATH}nz{n_zone}_{run}/'
        if not os.path.exists(scenario_plot_path):
            os.makedirs(scenario_plot_path)

        # Load the MCMC results
        # sample_path = TEST_ZONE_DIRECTORY + '/sa_contact_zones_nz' + str(n_zone_file) + '_' + str(run) + '.pkl'
        sample_path = f'{PATH_SA}{TEST_ZONE_DIRECTORY}sa_contact_zones_nz{n_zone}_{run}.pkl'

        samples = load_from(sample_path)

        n_zones = samples['sample_zones'][0].shape[0]
        n_families = samples['sample_p_families'][0].shape[0]

        # Define output format for estimated samples
        mcmc_res = {'lh': [],
                    'prior': [],
                    'recall': [],
                    'precision': [],
                    'posterior': [],
                    'zones': [[] for _ in range(n_zones)],
                    'lh_single_zones': [[] for _ in range(n_zones)],
                    'posterior_single_zones': [[] for _ in range(n_zones)],
                    'weights': [],
                    'p_zones': [[] for _ in range(n_zones)],
                    'p_families': [[] for _ in range(n_families)]}


        for t in range(len(samples['sample_zones'])):

            # Zones and p_zones
            for z in range(n_zones):
                mcmc_res['zones'][z].append(samples['sample_zones'][t][z])
                mcmc_res['p_zones'][z].append(transform_p_from_log(samples['sample_p_zones'][t])[z])

            # Weights
            mcmc_res['weights'].append(transform_weights_from_log(samples['sample_weights'][t]))

            # p_families
            for fam in range(n_families):
                mcmc_res['p_families'][fam].append(transform_p_from_log(samples['sample_p_families'][t])[fam])

            # Likelihood, prior and posterior
            mcmc_res['lh'].append(samples['sample_likelihood'][t])
            mcmc_res['prior'].append(samples['sample_prior'][t])

            posterior = samples['sample_likelihood'][t] + samples['sample_prior'][t]

            # Likelihood and posterior of single zones
            for z in range(n_zones):
                mcmc_res['lh_single_zones'][z].append(samples['sample_lh_single_zones'][t][z])
                posterior_single_zone = samples['sample_lh_single_zones'][t][z] + samples['sample_prior_single_zones'][t][z]
                mcmc_res['posterior_single_zones'][z].append(posterior_single_zone)

            mcmc_res['posterior'].append(posterior)

        np.set_printoptions(suppress=True)

        # Retrieve the sites from the csv and transform into a network
        sites, site_names, _, _, _, _, _ = \
            read_languages_from_csv(f'{PATH_SA}data/features/features.csv')

        # read_features_from_csv(file_location="data/features/", log=True)


        network = compute_network(sites)

        # Change order and rank
        # mcmc_res = match_zones(mcmc_res)
        # mcmc_res = rank_zones(mcmc_res, rank_by="lh", burn_in=0.8)



        # Compute the dic
        dic = compute_dic(mcmc_res, burn_in=burn_in)


        # Plot posterior frequency
        plot_posterior_frequency4(
            mcmc_res,
            net = network,
            nz = 1,
            ts_posterior_freq = ts_posterior_freq,
            burn_in = burn_in,
            show_zone_bbox = False,
            show_axes = True,
            fname = f'{scenario_plot_path}posterior_frequency_nz{n_zone}_{run}'
        )

        """
        # Plot posterior frequency
        plot_posterior_frequency(mcmc_res, net=network, nz=n_zone, burn_in=0.8, bg_map=True,
                                 proj4=PROJ4_STRING,
                                 geojson_map=GEOJSON_MAP_PATH, geo_json_river=GEOJSON_RIVER_PATH,
                                 offset_factor=0.1)
        
        n_zone_file = 1
        dics = {}
        while True:
            print("here")
            try:
                # Load the MCMC results
                sample_path = TEST_ZONE_DIRECTORY + '/sa_contact_zones_nz' + str(n_zone_file) + '_' + str(run) + '.pkl'
                samples = load_from(sample_path)
    
            except FileNotFoundError:
                break
    
            # Define output format
            n_zones = samples['sample_zones'][0].shape[0]
    
            # Define output format
            mcmc_res_all = {'lh': []}
    
            for t in range(len(samples['sample_zones'])):
                # Likelihood, prior and posterior
                mcmc_res_all['lh'].append(samples['sample_likelihood'][t])
    
            dics[n_zone_file] = compute_dic(mcmc_res_all, 0.5)
            n_zone_file += 1
    
        plot_dics(dics)
    
        """