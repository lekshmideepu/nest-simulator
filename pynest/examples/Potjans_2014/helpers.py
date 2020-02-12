# -*- coding: utf-8 -*-
#
# helpers.py
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

"""PyNEST Microcircuit Example: Helpers
------------------------------------------

Helper functions for the simulation and evaluation of the microcircuit.

"""

import os
import sys
import numpy as np
if 'DISPLAY' not in os.environ:
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


def compute_DC(net_dict, w_ext):
    """ Computes DC input if no Poisson input is provided to the microcircuit.

    Parameters
    ----------
    net_dict
        Parameters of the microcircuit.
    w_ext
        Weight of external connections.

    Returns
    -------
    DC
        DC input, which compensates lacking Poisson input.
    """
    DC = (
        net_dict['bg_rate'] * net_dict['K_ext'] *
        w_ext * net_dict['neuron_params']['tau_syn_E'] * 0.001
        )
    return DC


def get_weight(PSP_val, net_dict):
    """ Computes weight to elicit a change in the membrane potential.

    The weight is calculated as a postsynaptic current that is large enough to
    elicit a change in the membrane potential of size ``PSP_val``.

    Parameters
    ----------
    PSP_val
        Evoked postsynaptic potential.
    net_dict
        Dictionary containing parameters of the microcircuit.

    Returns
    -------
    PSC_e
        Weight value(s).

    """
    C_m = net_dict['neuron_params']['C_m']
    tau_m = net_dict['neuron_params']['tau_m']
    tau_syn_ex = net_dict['neuron_params']['tau_syn_ex']

    PSC_e_over_PSP_e = (((C_m) ** (-1) * tau_m * tau_syn_ex / (
        tau_syn_ex - tau_m) * ((tau_m / tau_syn_ex) ** (
            - tau_m / (tau_m - tau_syn_ex)) - (tau_m / tau_syn_ex) ** (
                - tau_syn_ex / (tau_m - tau_syn_ex)))) ** (-1))
    PSC_e = (PSC_e_over_PSP_e * PSP_val)
    return PSC_e


def get_total_number_of_synapses(net_dict):
    """ Returns the total number of synapses between all populations.

    The first index (rows) of the output matrix is the target population
    and the second (columns) the source population.

    This function accounts for potentially scaled population sizes
    (``N_scaling``) but a scaling of the synapse numbers is not included.
    Instead, the main script ``network.py`` applies the corresponding
    ``K_scaling`` to the result of this function.

    Parameters
    ----------
    net_dict
        Dictionary containing parameters of the microcircuit.

    Returns
    -------
    K
        Total number of synapses with
        dimensions [len(populations), len(populations)].

    """
    N_full = net_dict['N_full']
    number_N = len(N_full)
    conn_probs = net_dict['conn_probs']
    scaling = net_dict['N_scaling']
    prod = np.outer(N_full, N_full)
    n_syn_temp = np.log(1. - conn_probs)/np.log((prod - 1.) / prod)
    N_full_matrix = np.tile(N_full, (number_N, 1)).T
    K = (((n_syn_temp * (
        N_full_matrix * scaling).astype(int)) / N_full_matrix).astype(int))
    return K


def synapses_th_matrix(net_dict, stim_dict):
    """ Computes number of synapses between thalamus and microcircuit.

    The first index (rows) of the output matrix is the target population
    and the second (columns) is the thalamus.

    This function accounts for potentially scaled population sizes
    (``N_scaling``) but a scaling of the synapse numbers is not included.
    Instead, the main script ``network.py`` applies the corresponding
    ``K_scaling`` to the result of this function.

    Parameters
    ----------
    net_dict
        Dictionary containing parameters of the microcircuit.
    stim_dict
        Dictionary containing stimulation parameters.

    Returns
    -------
    K
        Total number of synapses from the thalamus to the populations with
        dimensions[len(populations), 1]

    """
    N_full = net_dict['N_full']
    scaling = net_dict['N_scaling']
    conn_probs = stim_dict['conn_probs_th']
    T_full = stim_dict['n_thal']
    prod = (T_full * N_full).astype(float)
    n_syn_temp = np.log(1. - conn_probs)/np.log((prod - 1.)/prod)
    K = ((n_syn_temp * (N_full * scaling).astype(int))/N_full).astype(int)
    return K


def adj_w_ext_to_K(K_full, K_scaling, w, w_from_PSP, DC, net_dict, stim_dict):
    """ Adjusts weights and external input to scaling of synapse numbers.

    The recurrent and external weights are adjusted to the scaling
    of the synapse numbers. Extra DC input is added to compensate for the
    scaling in order to preserve the mean and variance of the input.

    Parameters
    ----------
    K_full
        Total number of connections between the eight populations.
    K_scaling
        Scaling factor for the connections.
    w
        Weight matrix of the connections of the eight populations.
    w_from_PSP
        Weight of the external connections.
    DC
        DC input to the eight populations.
    net_dict
        Dictionary containing parameters of the microcircuit.
    stim_dict
        Dictionary containing stimulation parameters.

    Returns
    -------
    w_new
        Adjusted weight matrix.
    w_ext_new
        Adjusted external weight.
    I_ext
        Extra DC input.

    """
    tau_syn_E = net_dict['neuron_params']['tau_syn_E']
    full_mean_rates = net_dict['full_mean_rates']
    w_mean = w_from_PSP
    K_ext = net_dict['K_ext']
    bg_rate = net_dict['bg_rate']
    w_new = w / np.sqrt(K_scaling)
    I_ext = np.zeros(len(net_dict['populations']))
    x1_all = w * K_full * full_mean_rates
    x1_sum = np.sum(x1_all, axis=1)
    if net_dict['poisson_input']:
        x1_ext = w_mean * K_ext * bg_rate
        w_ext_new = w_mean / np.sqrt(K_scaling)
        I_ext = 0.001 * tau_syn_E * (
            (1. - np.sqrt(K_scaling)) * x1_sum + (
                1. - np.sqrt(K_scaling)) * x1_ext) + DC
    else:
        w_ext_new = w_from_PSP / np.sqrt(K_scaling)
        I_ext = 0.001 * tau_syn_E * (
            (1. - np.sqrt(K_scaling)) * x1_sum) + DC
    return w_new, w_ext_new, I_ext


def read_name(path, name):
    """ Reads names and ids of spike detector.

    The names of the spike detectors are gathered and the lowest and
    highest id of each spike detector is computed. If the simulation was
    run on several threads or mpi-processes, one name per spike detector
    per mpi-process/thread is extracted.

    Parameters
    ------------
    path
        Path where the spike detector files are stored.
    name
        Name of the spike detector.

    Returns
    -------
    files
        Names of all spike detectors, which are located in the path.
    node_ids
        Lowest and highest ids of the spike detectors.

    """
    # load filenames
    files = []
    for file in os.listdir(path):
        if file.endswith('.gdf') and file.startswith(name):
            temp = file.split('-')[0] + '-' + file.split('-')[1]
            if temp not in files:
                files.append(temp)

    # load node IDs
    node_idfile = open(path + 'population_nodeids.dat', 'r')
    node_ids = []
    for l in node_idfile:
        a = l.split()
        node_ids.append([int(a[0]), int(a[1])])
    files = sorted(files)
    return files, node_ids


def load_spike_times(path, name, begin, end):
    """ Loads spike times of each spike detector.

    Parameters
    -----------
    path
        Path where the files with the spike times are stored.
    name
        Name of the spike detector.
    begin
        Time point to start loading spike times (excluded).
    end
        Time point to stop loading spike times (excluded).

    Returns
    -------
    data
        Dictionary containing spike times in the interval from ``begin``
        to ``end``.

    """
    files, node_ids = read_name(path, name)
    data = {}
    for i in list(range(len(files))):
        all_names = os.listdir(path)
        temp3 = [
            all_names[x] for x in list(range(len(all_names)))
            if all_names[x].endswith('gdf') and
            all_names[x].startswith('spike') and
            (all_names[x].split('-')[0] + '-' + all_names[x].split('-')[1]) in
            files[i]
            ]
        data_temp = [np.loadtxt(os.path.join(path, f)) for f in temp3]
        data_concatenated = np.concatenate(data_temp)
        data_raw = data_concatenated[np.argsort(data_concatenated[:, 1])]
        idx = ((data_raw[:, 1] > begin) * (data_raw[:, 1] < end))
        data[i] = data_raw[idx]
    return data


def plot_raster(path, name, begin, end):
    """ Creates a spike raster plot of the network activity.

    Parameters
    -----------
    path
        Path where the spike times are stored.
    name
        Name of the spike detector.
    begin
        Time point to start plotting spikes (exluded).
    end
        Time point to stop plotting spikes (excluded).

    Returns
    -------
    None

    """
    files, node_ids = read_name(path, name)
    data_all = load_spike_times(path, name, begin, end)
    highest_node_id = node_ids[-1][-1]
    node_ids_numpy = np.asarray(node_ids)
    node_ids_numpy_changed = abs(node_ids_numpy - highest_node_id) + 1
    L23_label_pos = (node_ids_numpy_changed[0][0] + node_ids_numpy_changed[1][1])/2
    L4_label_pos = (node_ids_numpy_changed[2][0] + node_ids_numpy_changed[3][1])/2
    L5_label_pos = (node_ids_numpy_changed[4][0] + node_ids_numpy_changed[5][1])/2
    L6_label_pos = (node_ids_numpy_changed[6][0] + node_ids_numpy_changed[7][1])/2
    ylabels = ['L23', 'L4', 'L5', 'L6']
    color_list = [
        '#000000', '#888888', '#000000', '#888888',
        '#000000', '#888888', '#000000', '#888888'
        ]
    Fig1 = plt.figure(1, figsize=(8, 6))
    for i in list(range(len(files))):
        times = data_all[i][:, 1]
        neurons = np.abs(data_all[i][:, 0] - highest_node_id) + 1
        plt.plot(times, neurons, '.', color=color_list[i])
    plt.xlabel('time [ms]', fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(
        [L23_label_pos, L4_label_pos, L5_label_pos, L6_label_pos],
        ylabels, rotation=10, fontsize=18
        )
    plt.savefig(os.path.join(path, 'raster_plot.png'), dpi=300)
    plt.show()


def fire_rate(path, name, begin, end):
    """ Computes firing rates and standard deviation of it.

    The firing rate of each neuron in each population is computed and stored
    in a numpy file in the directory of the spike detectors. The mean firing
    rate and its standard deviation are plotted for each population.

    Parameters
    -----------
    path
        Path where the spike times are stored.
    name
        Name of the spike detector.
    begin
        Time point to start calculating the firing rates (excluded).
    end
        Time point to stop calculating the firing rates (excluded).

    Returns
    -------
    None

    """
    files, node_ids = read_name(path, name)
    data_all = load_spike_times(path, name, begin, end)
    rates_averaged_all = []
    rates_std_all = []
    for h in list(range(len(files))):
        n_fil = data_all[h][:, 0]
        n_fil = n_fil.astype(int)
        count_of_n = np.bincount(n_fil)
        count_of_n_fil = count_of_n[node_ids[h][0]-1:node_ids[h][1]]
        rate_each_n = count_of_n_fil * 1000. / (end - begin)
        rate_averaged = np.mean(rate_each_n)
        rate_std = np.std(rate_each_n)
        rates_averaged_all.append(float('%.3f' % rate_averaged))
        rates_std_all.append(float('%.3f' % rate_std))
        np.save(os.path.join(path, ('rate' + str(h) + '.npy')), rate_each_n)
    print('Mean rates: %r Hz' % rates_averaged_all)
    print('Standard deviation of rates: %r Hz' % rates_std_all)


def boxplot(net_dict, path):
    """ Creates a boxblot of the firing rates of all populations.

    To create the boxplot, the firing rates of each neuron in each population
    need to be computed with the function ``fire_rate()``.

    Parameters
    -----------
    net_dict
        Dictionary containing parameters of the microcircuit.
    path
        Path were the firing rates are stored.

    Returns
    -------
    None

    """
    pops = net_dict['N_full']
    reversed_order_list = list(range(len(pops) - 1, -1, -1))
    list_rates_rev = []
    for h in reversed_order_list:
        list_rates_rev.append(
            np.load(os.path.join(path, ('rate' + str(h) + '.npy')))
            )
    pop_names = net_dict['populations']
    label_pos = list(range(len(pops), 0, -1))
    color_list = ['#888888', '#000000']
    medianprops = dict(linestyle='-', linewidth=2.5, color='firebrick')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    bp = plt.boxplot(list_rates_rev, 0, 'rs', 0, medianprops=medianprops)
    plt.setp(bp['boxes'], color='black')
    plt.setp(bp['whiskers'], color='black')
    plt.setp(bp['fliers'], color='red', marker='+')
    for h in list(range(len(pops))):
        boxX = []
        boxY = []
        box = bp['boxes'][h]
        for j in list(range(5)):
            boxX.append(box.get_xdata()[j])
            boxY.append(box.get_ydata()[j])
        boxCoords = list(zip(boxX, boxY))
        k = h % 2
        boxPolygon = Polygon(boxCoords, facecolor=color_list[k])
        ax1.add_patch(boxPolygon)
    plt.xlabel('firing rate [Hz]', fontsize=18)
    plt.yticks(label_pos, pop_names, fontsize=18)
    plt.xticks(fontsize=18)
    plt.savefig(os.path.join(path, 'box_plot.png'), dpi=300)
    plt.show()
