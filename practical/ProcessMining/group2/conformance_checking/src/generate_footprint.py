from sortedcontainers import SortedSet, SortedDict
from itertools import chain
import numpy as np
from enum import Enum


class Relations(Enum):
    BEFORE = '<-'
    SEQUENCE = '->'
    NOT_FOLLOWED = '#'
    PARALLEL = '||'


class FootPrintMatrix:
    def __init__(self, traces=None, relations=None):
        self.traces = traces if traces is not None else []  # Traces from an event log
        self.transitions = SortedSet()

        if relations is None:
            self.relations = SortedDict()  # Default to an empty SortedDict
        else:
            self.relations = SortedDict(relations)

        self.places = []

    @classmethod
    def from_relations(cls, relations):
        return cls(relations=relations)

    def get_transitions(self):
        # Sets all transitions for the current petri net
        self.transitions = set(chain.from_iterable(self.traces.values()))

    def get_footprint_regular_alpha_miner(self) -> np.ndarray:
        # Step 1: remove duplicate traces
        traces_without_duplicates = SortedSet()

        for trace in self.traces.values():
            traces_without_duplicates.add("".join(trace))

        # Extract relations between each transitions
        # generate Footprint

        for transition_1 in self.transitions:
            self.relations[transition_1] = SortedDict()
            for transition_2 in self.transitions:
                two_element_transitions = transition_1 + transition_2

                all_relations = None
                for trace in traces_without_duplicates:

                    if trace.find(two_element_transitions) >= 0:
                        # print(two_element_transitions)
                        # all_relations = "->"
                        if all_relations == Relations.BEFORE.value:

                            all_relations = Relations.PARALLEL.value
                        else:
                            all_relations = Relations.SEQUENCE.value

                    if trace.find(two_element_transitions[::-1]) >= 0:

                        if all_relations == Relations.SEQUENCE.value:

                            all_relations = Relations.PARALLEL.value
                        else:
                            all_relations = Relations.BEFORE.value

                if all_relations == None:
                    all_relations = Relations.NOT_FOLLOWED.value
                self.relations[transition_1][transition_2] = all_relations


# TODO add comments