from sortedcontainers import SortedDict, SortedSet
from practical.ProcessMining.group2.conformance_checking.src.generate_footprint import (
    FootPrintMatrix,
)


class ConformanceChecking:
    # Initialize ConformanceChecking Object
    def __init__(self, fpm_1, fpm_2):
        self.fpm_1 = fpm_1
        self.fpm_2 = fpm_2

    # Checks two dictionaries (footprint)
    # TODO only works if keys of dicts are the same
    def get_conformance_matrix(self):
        dict_out = SortedDict()
        for (outer_k1, outer_v1), (outer_k2, outer_v2) in zip(
            self.fpm_1.relations.items(), self.fpm_2.relations.items()
        ):
            inner_dict_out = SortedDict()
            for (inner_k1, inner_v1), (inner_k2, inner_v2) in zip(
                outer_v1.items(), outer_v2.items()
            ):
                if inner_v1 == inner_v2:
                    inner_dict_out[inner_k1] = ''
                else:
                    inner_dict_out[inner_k1] = '{}:{}'.format(inner_v1, inner_v2)

            dict_out[outer_k1] = inner_dict_out

        return FootPrintMatrix.from_relations(dict_out)

    def get_conformance_value(self):
        different_cells = 0
        total_cells = len(self.fpm_1.relations) ** 2
        for (outer_k1, outer_v1), (outer_k2, outer_v2) in zip(
            self.fpm_1.relations.items(), self.fpm_2.relations.items()
        ):
            inner_dict_out = SortedDict()
            for (inner_k1, inner_v1), (inner_k2, inner_v2) in zip(
                outer_v1.items(), outer_v2.items()
            ):
                if inner_v1 != inner_v2:
                    different_cells += 1

        return 1 - different_cells / total_cells