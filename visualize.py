from __future__ import print_function

import copy
import warnings

import graphviz
import matplotlib.pyplot as plt
import numpy as np


def PlotStats(Statistics, YLog=False, View=False, Filename='avg_fitness.svg'):
    """ Plots the population's average and best fitness. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    Generation = range(len(Statistics.most_fit_genomes))
    BestFitness = [c.fitness for c in Statistics.most_fit_genomes]
    AvgFitness = np.array(Statistics.get_fitness_mean())
    StdevFitness = np.array(Statistics.get_fitness_stdev())

    plt.plot(Generation, AvgFitness, 'b-', label="average")
    plt.plot(Generation, AvgFitness - StdevFitness, 'g-.', label="-1 sd")
    plt.plot(Generation, AvgFitness + StdevFitness, 'g-.', label="+1 sd")
    plt.plot(Generation, BestFitness, 'r-', label="best")

    plt.title("Population's average and best fitness")
    plt.xlabel("Generations")
    plt.ylabel("Fitness")
    plt.grid()
    plt.legend(loc="best")
    if YLog:
        plt.gca().set_yscale('symlog')

    plt.savefig(Filename)
    if View:
        plt.show()

    plt.close()


def PlotSpikes(Spikes, View=False, Filename=None, Title=None):
    """ Plots the trains for a single spiking neuron. """
    TValues = [t for t, I, v, u, f in Spikes]
    VValues = [v for t, I, v, u, f in Spikes]
    UValues = [u for t, I, v, u, f in Spikes]
    IValues = [I for t, I, v, u, f in Spikes]
    FValues = [f for t, I, v, u, f in Spikes]

    Fig = plt.figure()
    plt.subplot(4, 1, 1)
    plt.ylabel("Potential (mv)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(TValues, VValues, "g-")

    if Title is None:
        plt.title("Izhikevich's spiking neuron model")
    else:
        plt.title("Izhikevich's spiking neuron model ({0!s})".format(Title))

    plt.subplot(4, 1, 2)
    plt.ylabel("Fired")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(TValues, FValues, "r-")

    plt.subplot(4, 1, 3)
    plt.ylabel("Recovery (u)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(TValues, UValues, "r-")

    plt.subplot(4, 1, 4)
    plt.ylabel("Current (I)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(TValues, IValues, "r-o")

    if Filename is not None:
        plt.savefig(Filename)

    if View:
        plt.show()
        plt.close()
        Fig = None

    return Fig


def PlotSpecies(Statistics, View=False, Filename='speciation.svg'):
    """ Visualizes speciation throughout evolution. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    SpeciesSizes = Statistics.get_species_sizes()
    NumGenerations = len(SpeciesSizes)
    Curves = np.array(SpeciesSizes).T

    Fig, Ax = plt.subplots()
    Ax.stackplot(range(NumGenerations), *Curves)

    plt.title("Speciation")
    plt.ylabel("Size per Species")
    plt.xlabel("Generations")

    plt.savefig(Filename)

    if View:
        plt.show()

    plt.close()


def DrawNet(Config, Genome, View=False, Filename=None, NodeNames=None, ShowDisabled=True, PruneUnused=False,
             NodeColors=None, Fmt='svg'):
    """ Receives a genome and draws a neural network with arbitrary topology. """
    # Attributes for network nodes.
    if graphviz is None:
        warnings.warn("This display is not available due to a missing optional dependency (graphviz)")
        return

    if NodeNames is None:
        NodeNames = {}

    assert type(NodeNames) is dict

    if NodeColors is None:
        NodeColors = {}

    assert type(NodeColors) is dict

    NodeAttrs = {
        'shape': 'circle',
        'fontsize': '9',
        'height': '0.2',
        'width': '0.2'}

    Dot = graphviz.Digraph(format=Fmt, node_attr=NodeAttrs)

    Inputs = set()
    for k in Config.genome_config.input_keys:
        Inputs.add(k)
        Name = NodeNames.get(k, str(k))
        InputAttrs = {'style': 'filled', 'shape': 'box', 'fillcolor': NodeColors.get(k, 'lightgray')}
        Dot.node(Name, _attributes=InputAttrs)

    Outputs = set()
    for k in Config.genome_config.output_keys:
        Outputs.add(k)
        Name = NodeNames.get(k, str(k))
        NodeAttrs = {'style': 'filled', 'fillcolor': NodeColors.get(k, 'lightblue')}

        Dot.node(Name, _attributes=NodeAttrs)

    if PruneUnused:
        Connections = set()
        for cg in Genome.connections.values():
            if cg.enabled or ShowDisabled:
                Connections.add((cg.in_node_id, cg.out_node_id))

        UsedNodes = copy.copy(Outputs)
        Pending = copy.copy(Outputs)
        while Pending:
            NewPending = set()
            for a, b in Connections:
                if b in Pending and a not in UsedNodes:
                    NewPending.add(a)
                    UsedNodes.add(a)
            Pending = NewPending
    else:
        UsedNodes = set(Genome.nodes.keys())

    for n in UsedNodes:
        if n in Inputs or n in Outputs:
            continue

        Attrs = {'style': 'filled',
                 'fillcolor': NodeColors.get(n, 'white')}
        Dot.node(str(n), _attributes=Attrs)

    for cg in Genome.connections.values():
        if cg.enabled or ShowDisabled:
            #if cg.input not in used_nodes or cg.output not in used_nodes:
            #    continue
            Input, Output = cg.key
            A = NodeNames.get(Input, str(Input))
            B = NodeNames.get(Output, str(Output))
            Style = 'solid' if cg.enabled else 'dotted'
            Color = 'green' if cg.weight > 0 else 'red'
            Width = str(0.1 + abs(cg.weight / 5.0))
            Dot.edge(A, B, _attributes={'style': Style, 'color': Color, 'penwidth': Width})

    Dot.render(Filename, view=View)

    return Dot