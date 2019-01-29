#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import logging
import itertools
import datetime
import multiprocessing.pool

import numpy as np

from src.util import dump, load_from
from src.preprocessing import (get_network,
                               get_network_subset,
                               generate_ecdf_geo_prior,
                               get_contact_zones,
                               simulate_background_distribution,
                               simulate_contact, compute_feature_prob,
                               precompute_feature_likelihood,
                               define_contact_features)

from src.sampling.zone_sampling import ZoneMCMC
from src.postprocessing import stepping_stone_sampler


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


now = datetime.datetime.now().__str__().rsplit('.')[0]
now = now.replace(':', '-')
now = now.replace(' ', '_')


TEST_SAMPLING_DIRECTORY = 'data/results/test/marginal_lh/{experiment}/'.format(experiment=now)
TEST_SAMPLING_RESULTS_PATH = TEST_SAMPLING_DIRECTORY + 'marginal_lh_z{z}_e{e}_{run}.pkl'
TEST_SAMPLING_LOG_PATH = TEST_SAMPLING_DIRECTORY + 'marginal_lh.log'


# Make directory if it doesn't exist yet
if not os.path.exists(TEST_SAMPLING_DIRECTORY):
    os.mkdir(TEST_SAMPLING_DIRECTORY)


logging.basicConfig(filename=TEST_SAMPLING_LOG_PATH, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

###############################
# Simulation
################################

# Zones
test_zone = [101, 102]

# Intensity: proportion of sites, which are indicative of contact
i = [0.5, 0.9]

# Features: proportion of features affected by contact
f = [0.5, 0.9]

test_ease = range(0, len(f))
# [0] Hard: Unfavourable zones with low intensity and few features affected by contact
# [1] Easy: Favourable zones  with high intensity and many features affected by contact

marginal_lh__param_grid = list(itertools.product(test_ease, test_zone))
print(marginal_lh__param_grid)

# Feature probabilities
TOTAL_N_FEATURES = 30
P_SUCCESS_MIN = 0.05
P_SUCCESS_MAX = 0.95

# Geo-prior
GEO_PRIOR_SAMPLES = 1000

#################################
# STEPPING STONE SAMPLER
#################################

# General
N_RUNS = 1
N_STEPS = 10000
N_SAMPLES = 100
BURN_IN = 2000

# Steepness of the likelihood function
LH_WEIGHT = 1

# Markov chain coupled MC (mc3)
N_CHAINS = 5                    # Number of independent chains
SWAP_PERIOD = 200
N_SWAPS = 1                     # Attempted inter-chain swaps after each SWAP_PERIOD

# Zone sampling
MIN_SIZE = 5
MAX_SIZE = 40
START_SIZE = 25
CONNECTED_ONLY = False
P_TRANSITION_MODE = {
    'swap': 0.5,
    'grow': 0.75,
    'shrink': 1.}

# Stepping Stone Sampler
N_TEMP = 100

# At the moment not needed and set to default
MODEL = 'particularity'
N_ZONES = 1


def evaluate_marginal_lh(params):
    e, z = params

    # Retrieve the complete network from the DB
    network = get_network(reevaluate=True)

    # Generate an empirical distribution for estimating the geo-likelihood
    ecdf_geo = generate_ecdf_geo_prior(net=network, min_n=MIN_SIZE, max_n=MAX_SIZE,
                                       nr_samples=GEO_PRIOR_SAMPLES,
                                       reevaluate=False)

    contact_zones_idxs = get_contact_zones(z)
    n_zones = len(contact_zones_idxs)
    contact_zones = np.zeros((n_zones, network['n']), bool)

    for k, cz_idxs in enumerate(contact_zones_idxs.values()):
        contact_zones[k, cz_idxs] = True

    network_areal_prior = get_network_subset(areal_subset=z)

    for run in range(N_RUNS):

        initial_zones = [[None] * N_CHAINS] * N_ZONES
        # Simulation
        f_names, contact_f_names = define_contact_features(n_feat=TOTAL_N_FEATURES, r_contact_feat=f[e],
                                                           contact_zones=contact_zones_idxs)

        features_bg = simulate_background_distribution(features=f_names,
                                                       n_sites=len(network['vertices']),
                                                       contact_features=contact_f_names,
                                                       p_min=P_SUCCESS_MIN, p_max=P_SUCCESS_MAX,
                                                       p_max_contact=i[e],
                                                       reevaluate=True)

        features = simulate_contact(features=features_bg, contact_features=contact_f_names,
                                    p=i[e], contact_zones=contact_zones_idxs, reevaluate=True)
        feature_prob = compute_feature_prob(features, reevaluate=True)
        lh_lookup = precompute_feature_likelihood(MIN_SIZE, MAX_SIZE, feature_prob,
                                                  log_surprise=True, reevaluate=True)

        temperatures = np.linspace(0.0001, 1, N_TEMP)

        ml = {'m_lh_full': [],
              'm_lh_areal_prior': [],
              'temperatures': temperatures}

        # Collect samples for different temperatures, this will be needed as an input to the stepping stone sampler
        for t in temperatures:
            # Sampling without areal prior
            zone_sampler_full = ZoneMCMC(network=network, features=features,
                                         min_size=MIN_SIZE, max_size=MAX_SIZE, start_size=START_SIZE,
                                         p_transition_mode=P_TRANSITION_MODE, n_zones=N_ZONES, connected_only=CONNECTED_ONLY,
                                         feature_ll_mode=MODEL, geo_prior_mode=MODEL,
                                         lh_lookup=lh_lookup, lh_weight=LH_WEIGHT, ecdf_geo=ecdf_geo, ecdf_type="mst",
                                         n_chains=N_CHAINS, initial_zones=initial_zones,
                                         swap_period=SWAP_PERIOD, temperature=t, chain_swaps=N_SWAPS, print_logs=False)

            # Sampling with areal prior
            zone_sampler_areal_prior = ZoneMCMC(network=network_areal_prior, features=features,
                                                min_size=MIN_SIZE, max_size=MAX_SIZE, start_size=START_SIZE,
                                                p_transition_mode=P_TRANSITION_MODE, n_zones=N_ZONES,
                                                connected_only=CONNECTED_ONLY,
                                                feature_ll_mode=MODEL, geo_prior_mode=MODEL,
                                                lh_lookup=lh_lookup, lh_weight=LH_WEIGHT, ecdf_geo=ecdf_geo, ecdf_type="mst",
                                                n_chains=N_CHAINS, initial_zones=initial_zones,
                                                swap_period=SWAP_PERIOD, temperature=t, chain_swaps=N_SWAPS, print_logs=False)

            # Run sampler and aggregate results
            zone_sampler_full.generate_samples(N_STEPS, N_SAMPLES, BURN_IN, return_steps=False)
            temp_stats_full = zone_sampler_full.statistics

            zone_sampler_areal_prior.generate_samples(N_STEPS, N_SAMPLES, BURN_IN, return_steps=False)
            temp_stats_areal_prior = zone_sampler_areal_prior.statistics

            # Store all results
            ml['m_lh_full'].append(temp_stats_full)
            ml['m_lh_areal_prior'].append(temp_stats_areal_prior)

        path = TEST_SAMPLING_RESULTS_PATH.format(z=z, e=e, run=run)
        dump(ml, path)

    return 0


if __name__ == '__main__':

    # Test ease
    with MyPool(4) as pool:
        all_stats = pool.map(evaluate_marginal_lh, marginal_lh__param_grid)