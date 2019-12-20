

if __name__ == '__main__':
    from src.util import load_from, transform_weights_from_log,transform_p_from_log, samples2res
    from src.preprocessing import compute_network, get_sites
    from src.postprocessing import compute_dic
    from src.plotting import plot_posterior_frequency, plot_trace_lh, plot_trace_recall_precision, \
        plot_zone_size_over_time, plot_dics, plot_correlation_weights, plot_histogram_weights, plot_correlation_p, \
        plot_posterior_frequency_family1, plot_posterior_frequency_family2
    import os



    PATH = '../../../../' # relative path to contact_zones_directory
    PATH_SIMULATION = PATH + '/src/experiments/simulation/'
    TEST_ZONE_DIRECTORY = 'results/contact_areas/2019-10-21_14-49/'

    PLOT_PATH = PATH + 'plots/contact_areas/'
    if not os.path.exists(PLOT_PATH): os.makedirs(PLOT_PATH)

    # Inheritance and number of runs
    inheritance = 1
    inheritances = [0, 1]
    run = 0

    # general parameters for plots
    ts_posterior_freq = 0.8
    ts_low_frequency = 0.5
    burn_in =  0.2


    for inheritance in inheritances:

        scenario_plot_path = f'{PLOT_PATH}i{inheritance}_{run}/'
        if not os.path.exists(scenario_plot_path):
            os.makedirs(scenario_plot_path)

        # Load the MCMC results
        sample_path = PATH_SIMULATION + TEST_ZONE_DIRECTORY + 'contact_areas_i' + str(inheritance) + '_' + str(run) + '.pkl'
        samples = load_from(sample_path)
        mcmc_res = samples2res(samples)
        zones = mcmc_res['zones']

        # Retrieve the sites from the csv and transform into a network
        sites, site_names = get_sites(PATH_SIMULATION + 'data/sites_simulation.csv')
        network = compute_network(sites)

        # plot posterior frequency including family

        plot_posterior_frequency_family2(
            mcmc_res,
            net = network,
            nz = -1,
            ts_low_frequency = ts_low_frequency,
            ts_posterior_freq = ts_posterior_freq,
            burn_in = burn_in,
            show_zone_bbox = True,
            show_axes = False,
            fname = f'{scenario_plot_path}posterior_frequency_family_i{inheritance}_{run}'
        )


        # Plot trace of likelihood, recall and precision
        plot_trace_lh(
            mcmc_res,
            burn_in = burn_in,
            true_lh = True,
            fname = f'{scenario_plot_path}trace_likelihood_i{inheritance}_{run}'
        )

        plot_trace_recall_precision(
            mcmc_res,
            burn_in = burn_in,
            fname = f'{scenario_plot_path}trace_recall_precision_i{inheritance}_{run}'
        )

        # Plot zone size over time
        plot_zone_size_over_time(
            mcmc_res,
            r = 0,
            burn_in = burn_in,
            fname = f'{scenario_plot_path}zone_size_over_time_i{inheritance}_{run}'
        )

