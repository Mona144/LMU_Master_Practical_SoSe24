from collections import defaultdict
import random
import pm4py


class TokenReplay:
    """
    Token Replay algorithm implementation to check conformance of an event log with a Petri net model.

    Attributes:
        net: Dictionary representing the Petri net with input and output places for each transition.
        initial_marking: Dictionary representing the initial marking of the Petri net.
        final_marking: Dictionary representing the final marking of the Petri net.
        marking: Dictionary representing the current marking of the Petri net during replay.
        produced_tokens: Counter for the total number of produced tokens during replay.
        consumed_tokens: Counter for the total number of consumed tokens during replay.
        missing_tokens: Counter for the total number of missing tokens during replay.
        remaining_tokens: Counter for the total number of remaining tokens after replay.
    """

    def __init__(self, log, net, initial_marking, final_marking, net_type):
        """
        Initialize the TokenReplay class with a Petri net, initial marking, and final marking.

        Parameters:
            log: Base event log used for conformance checking with given net as model.
            net: Dictionary representing the Petri net with input and output places for each transition.
            initial_marking: Dictionary representing the initial marking of the Petri net.
            final_marking: Dictionary representing the final marking of the Petri net.
            net_type: Descriptions which Discovery method has been used.
        """
        self.log = log
        self.net = net
        self.net_type = net_type
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.marking = initial_marking.copy()

        self.produced_buffer = 0
        self.produced_tokens = 0
        self.consumed_buffer = 0
        self.consumed_tokens = 0

        self.missing_tokens = defaultdict(int)
        self.remaining_tokens = defaultdict(int)

        self.fitness, self.simplicity, self.precision, self.generalization = self._calculate_pm4py_dimensions(
            log, net, initial_marking, final_marking)
        # Override / add dimension values of own implementation
        # self.fitness = self.calculate_fitness()

    def run(self, log=None):
        """
        Run the Token Replay algorithm on an entire event log.

        Parameters:
            log: List of traces, where each trace is a list of events.

        Returns:
            list: A list of results for each trace.
        """
        if not log:  # To test with alternative logs
            log = self.log

        for trace in log:
            self.marking = self.initial_marking.copy()
            self.produced_buffer = 0
            self.consumed_buffer = 0

            for i, event in enumerate(trace):
                if not isinstance(event, str):  # To handle pm4py converted logs
                    event = event['concept:name']
                if event == 'tau':
                    self._handle_tau(trace, i)
                elif self._can_fire(event):
                    self._fire(event)
                else:
                    self._handle_unconformity(event)

            self.produced_tokens += self.produced_buffer
            self.consumed_tokens += self.consumed_buffer
            self.remaining_tokens = self._calculate_remaining_tokens()

    def _can_fire(self, event):
        """
        Check if the transition corresponding to the event can be fired.

        Parameters:
            event: The event to be checked.

        Returns:
            bool: True if the transition can be fired, False otherwise.
        """
        transition = next((t for t in self.net.transitions if t.label == event), None)
        if transition is None:
            return False
        for arc in transition.in_arcs:
            if self.marking[arc.source] <= 0:
                return False
        return True

    def _fire(self, event):
        """
        Fire the transition corresponding to the event, updating the marking.

        Parameters:
            event: The event to be fired.
        """
        if event == "tau":
            self.consumed_buffer += 1
            self.produced_buffer += 1
            return
        transition = next((t for t in self.net.transitions if t.label == event), None)
        if transition is None:
            return
        for arc in transition.in_arcs:
            self.marking[arc.source] -= 1
            self.consumed_buffer += 1
        for arc in transition.out_arcs:
            self.marking[arc.target] += 1
            self.produced_buffer += 1

    def _handle_tau(self, trace, pointer):
        """
        Handle the tau event by producing and consuming a token and then
        check if the next event in the trace can be fired.

        Parameters:
            trace: The trace being replayed.
            pointer: The current position in the trace.
        """

        # Check if there is a next event in the trace
        if pointer + 1 < len(trace):
            next_event = trace[pointer + 1]
            if isinstance(next_event, dict):
                next_event = next_event['activity']

            # Check if the next event can be fired after handling tau
            if self._can_fire(next_event):
                # Increment buffers for tau only, when next event can be fired
                self._fire('tau')
                self._fire(next_event)
            else:
                self._handle_unconformity(next_event)

    def _handle_unconformity(self, event):
        transition = next((t for t in self.net.transitions if t.label == event), None)
        if transition:
            for arc in transition.in_arcs:
                if self.marking[arc.source] < 1:
                    self.missing_tokens[arc.source] += 1

    def _calculate_remaining_tokens(self):
        """
        Calculate the total number of remaining tokens in the Petri net after replay.
        """
        remaining = defaultdict(int)
        for place, tokens in self.marking.items():
            final_tokens = self.final_marking.get(place, 0)
            if tokens > final_tokens:
                remaining[place] += tokens - final_tokens
        return remaining

    def get_unconformity_tokens(self):
        return {
            "missing": self.missing_tokens,
            "remaining": self.remaining_tokens
        }

    def get_discovery_type(self):
        return self.net_type

    def get_fitness(self):
        return self.fitness

    def get_simplicity(self):
        return self.simplicity

    def get_precision(self):
        return self.precision

    def get_generalization(self):
        return self.generalization

    def get_dimension_value(self, dimension: str):
        if dimension in ('f', 'fitness'):
            return self.get_fitness()
        elif dimension in ('s', 'simplicity'):
            return self.get_simplicity()
        elif dimension in ('p', 'precision'):
            return self.get_precision()
        elif dimension in ('g', 'generalization'):
            return self.get_generalization()
        else:
            return ValueError

    def calculate_fitness(self) -> float:
        total_missing = sum(val for val in self.missing_tokens.values())
        total_remaining = sum(val for val in self.remaining_tokens.values())

        fitness = (0.5 * (1 - (total_missing / self.consumed_tokens)) +
                   0.5 * (1 - (total_remaining / self.produced_tokens)))
        return fitness

    def _calculate_pm4py_dimensions(self, log, net, im, fm):
        fitness = pm4py.conformance.fitness_token_based_replay(log, net, im, fm)
        simplicity = pm4py.analysis.simplicity_petri_net(net, im, fm)
        precision = pm4py.conformance.precision_token_based_replay(log, net, im, fm)
        generalization = pm4py.conformance.generalization_tbr(log, net, im, fm)

        return fitness.get("log_fitness"), simplicity, precision, generalization

    def shuffle_activities(self):
        """
        Shuffle the activities in each trace of the event log.

        Returns:
            list: A new event log with shuffled activities in each trace.
        """
        shuffled_log = []
        for trace in self.log:
            shuffled_trace = list(trace)  # Create a copy of the trace
            random.shuffle(shuffled_trace)  # Shuffle the activities in the trace
            shuffled_log.append(shuffled_trace)
        return shuffled_log

