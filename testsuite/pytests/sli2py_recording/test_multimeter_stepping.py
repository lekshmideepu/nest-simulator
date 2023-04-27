# -*- coding: utf-8 -*-
#
# test_multimeter_stepping.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.

"""
Test multimeter recording in stepwise simulation.
"""

import pandas as pd
import pandas.testing as pdtest
import pytest

import nest

skip_models = [
    'gauss_rate_ipn',
    'lin_rate_ipn',
    'sigmoid_rate_ipn',
    'sigmoid_rate_gg_1998_ipn',
    'tanh_rate_ipn',
    'threshold_lin_rate_ipn',
    'lin_rate_opn',
    'tanh_rate_opn',
    'threshold_lin_rate_opn',
    'rate_transformer_gauss',
    'rate_transformer_lin',
    'rate_transformer_sigmoid',
    'rate_transformer_sigmoid_gg_1998',
    'rate_transformer_tanh',
    'rate_transformer_threshold_lin',
    'iaf_psc_alpha_multisynapse',  # Rport 0 SE
    'iaf_psc_exp_multisynapse',  # Rport 0 SE
    'gif_psc_exp_multisynapse',  # Rport 0 SE
    'glif_psc',  # Receptor type 0 in glif_psc does not accept SpikeEvent.
    'ac_generator',
    'dc_generator',
    'noise_generator',
    'step_current_generator',
    'step_rate_generator',
    'sinusoidal_poisson_generator',
    'erfc_neuron',
    'ginzburg_neuron',
    'mcculloch_pitts_neuron',
    'iaf_cond_alpha_mc',  # Rport 0 SE
    'sinusoidal_gamma_generator',
    'gif_cond_exp_multisynapse',  # Rport 0 SE
    'glif_cond',  # Rport 0 SE
    'ht_neuron',  # Receptor type 0 is not available in ht_neuron.
    'aeif_cond_beta_multisynapse',  # Rport 0 SE
    'aeif_cond_alpha_multisynapse',  # Rport 0 SE
    'siegert_neuron',
    'pp_cond_exp_mc_urbanczik',  # Rport 0 SE
]

# Obtain all models with non-empty recordables list
models = (model for model in nest.node_models
          if (nest.GetDefaults(model).get('recordables') and model not in skip_models))


def build_net(model):
    """
    Build network to be tested.

    A multimeter is set to record all recordables of the provided neuron model.
    The neuron receives Poisson input. 
    """

    nest.ResetKernel()

    nrn = nest.Create(model)
    pg = nest.Create('poisson_generator', params={'rate': 1e4})
    mm = nest.Create('multimeter', {'interval': 0.1,
                                    'record_from': nrn.recordables})
    nest.Connect(mm, nrn)
    nest.Connect(pg, nrn)

    return mm


@pytest.mark.parametrize('model', models)
def test_multimeter_stepping(model):
    """
    Test multimeter recording in stepwise simulation. 

    The test first simulates the network for `50 x nest.min_delay`. Then, we
    reset and build the network again and perform 50 subsequent simulations
    with `nest.min_delay` simulation time. Both cases should produce identical
    results.
    """

    mm = build_net(model)
    nest.Simulate(50 * nest.min_delay)
    df = pd.DataFrame.from_dict(mm.events)

    mm_stepwise = build_net(model)
    for _ in range(50):
        nest.Simulate(nest.min_delay)

    df_stepwise = pd.DataFrame.from_dict(mm_stepwise.events)

    pdtest.assert_frame_equal(df, df_stepwise)
