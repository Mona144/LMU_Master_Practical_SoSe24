# from pm4py.visualization.petri_net import visualize
from graphviz import Digraph
from sortedcontainers import SortedSet
from pm4py.objects.petri_net.utils.petri_utils import add_arc_from_to
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.visualization.petri_net import visualizer


# from pm4py.visualization.petrinet import visualizer as pn_vis


def visualize_graphviz(alpha_miner_plus, F_L1L, file_name):
    # we need to add both transition directions for the loops
    # Iterate through the set
    for item in list(F_L1L):
        # Create the palindrome (reverse tuple)
        palindrome = (item[1], item[0])

        # Check if the palindrome is in the set
        if palindrome not in F_L1L:
            # Add the palindrome to the set if it's not already present
            F_L1L.add(palindrome)  # TODO - test this

    dot = Digraph()

    for i in F_L1L:
        alpha_miner_plus.places.append(i)

    dot.graph_attr['ratio'] = '0.3'
    dot.graph_attr['rankdir'] = 'LR'

    input_transitions = []
    output_transitions = []

    for element in alpha_miner_plus.places:

        if len(element) == 3:

            input_transitions, place_name, output_transitions = (
                element[0],
                element[1],
                element[2],
            )

            for input_transition in input_transitions:
                dot.node(
                    str(input_transition),
                    shape='square',
                    width='1.0',
                    height='1.0',
                    fontname='bold',
                )
                dot.edge(str(input_transition), str(place_name))

            dot.node(
                str(place_name),
                shape='circle',
                width='0.5',
                height='0.5',
                fontname='bold',
            )

            for output_transition in output_transitions:
                dot.node(
                    str(output_transition),
                    shape='square',
                    width='1.0',
                    height='1.0',
                    fontname='bold',
                )
                dot.edge(str(place_name), str(output_transition))

        elif len(element) == 2:

            source, target = element

            # first off handle first and last place
            if type(source) == SortedSet or type(target) == SortedSet:
                # non loops

                if type(target) == SortedSet:
                    dot.node(
                        source,
                        shape='circle',
                        width='0.5',
                        height='0.5',
                        fontname='bold',
                    )
                    for transition in target:
                        dot.edge(source, transition)

                if type(source) == SortedSet:
                    dot.node(
                        target,
                        shape='doublecircle',
                        width='0.5',
                        height='0.5',
                        fontname='bold',
                    )
                    for transition in source:
                        dot.edge(transition, target)

            elif len(source) < 2:  # to remove place_i
                dot.node(
                    source, shape='square', width='1.0', height='1.0', fontname='bold'
                )

                dot.edge(source, target)
                # catch the loops here
                # check if inverse tuple is in the list
                if (target, source) in list(F_L1L):

                    dot.edge(target, source)

    dot.render(
        './graphs/petri_net_graphviz_{}'.format(file_name), format='png', view=False
    )


def visualize_pm4py(alpha_miner_plus, F_L1L, file_name):
    net = PetriNet("Petri Net")
    places = {}
    transitions = {}
    for element in alpha_miner_plus.places:

        if len(element) == 3:

            input_transitions, place_name, output_transitions = (
                element[0],
                element[1],
                element[2],
            )
            if place_name not in places:
                place = PetriNet.Place(place_name)
                net.places.add(place)
                places[place_name] = place

            for input_transition in input_transitions:
                if input_transition not in transitions:
                    transition = PetriNet.Transition(input_transition, input_transition)
                    net.transitions.add(transition)
                    transitions[input_transition] = transition
                add_arc_from_to(transitions[input_transition], places[place_name], net)

            for output_transition in output_transitions:
                if output_transition not in transitions:
                    transition = PetriNet.Transition(
                        output_transition, output_transition
                    )
                    net.transitions.add(transition)
                    transitions[output_transition] = transition
                add_arc_from_to(places[place_name], transitions[output_transition], net)

        elif len(element) == 2:

            source, target = element

            # first off handle first and last place
            if type(source) == SortedSet or type(target) == SortedSet:
                # non loops

                if type(target) == SortedSet:
                    if source not in places:
                        place = PetriNet.Place(source)
                        net.places.add(place)
                        places[source] = place

                    for target_transition in target:
                        if target_transition not in transitions:
                            transition = PetriNet.Transition(
                                target_transition, target_transition
                            )
                            net.transitions.add(transition)
                            transitions[target_transition] = transition
                        add_arc_from_to(
                            places[source], transitions[target_transition], net
                        )

                if type(source) == SortedSet:

                    if target not in places:
                        place = PetriNet.Place(target)
                        net.places.add(place)
                        places[target] = place

                    for source_transition in source:
                        if source_transition not in transitions:
                            transition = PetriNet.Transition(
                                source_transition, source_transition
                            )
                            net.transitions.add(transition)
                            transitions[source_transition] = transition

                        add_arc_from_to(
                            transitions[source_transition], places[target], net
                        )
    for L1L in F_L1L:
        L1L_left, L1L_right = L1L
        if L1L_left.startswith("Place"):
            L1L_place, L1L_transition = L1L
        else:
            L1L_transition, L1L_place = L1L
        if L1L_place not in places:
            place = PetriNet.Place(L1L_place)
            net.places.add(place)
            places[L1L_place] = place

        if L1L_transition not in transitions:
            transition = PetriNet.Transition(L1L_transition, L1L_transition)
            net.transitions.add(transition)
            transitions[L1L_transition] = transition
        if L1L_left.startswith("Place"):
            add_arc_from_to(places[L1L_place], transitions[L1L_transition], net)
        else:
            add_arc_from_to(transitions[L1L_transition], places[L1L_place], net)

    m_in = Marking()
    m_in[places['input']] = 1
    m_out = Marking()
    m_out[places['output']] = 1
    gviz = visualizer.apply(net, m_in, m_out)
    # visualizer.view(gviz)
    visualizer.save(gviz, './graphs/petri_net_pm4py_{}.png'.format(file_name))
