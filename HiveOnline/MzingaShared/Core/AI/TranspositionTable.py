import sys

from MzingaShared.Core.FixedCache import FixedCache

default_size_in_bytes = 32 * 1024 * 1024
default_transposition_table_entry_size = 128


def transposition_table_replace_entry_predicate(existing_entry, new_entry):
    return new_entry.depth > existing_entry.depth


class TranspositionTableEntryType:
    exact = 0
    lower_bound = 1
    upper_bound = 2


class TranspositionTableEntry(object):
    __slots__ = "type", "value", "depth", "best_move", "size_in_bytes"

    def __init__(self):
        self.type = None       # 24
        self.value = None      # 24
        self.depth = None      # 24
        self.best_move = None  # 56
        self.size_in_bytes = 128


class TranspositionTable(FixedCache):
    __slots__ = "fill_factor", "entry_size_in_bytes"

    def __init__(self, size_in_bytes=default_size_in_bytes, rep=transposition_table_replace_entry_predicate):
        super().__init__(size_in_bytes, rep)
        self.fill_factor = 0.92  # To leave room for unaccounted for overhead and unused dictionary capacity
        self.entry_size_in_bytes = (12 * sys.getsizeof(float)) + default_transposition_table_entry_size

    def get_capacity(self, size_in_bytes):
        if size_in_bytes < self.entry_size_in_bytes:
            raise ValueError("size_in_bytes")

        return 1 + round(self.fill_factor * size_in_bytes / self.entry_size_in_bytes)
