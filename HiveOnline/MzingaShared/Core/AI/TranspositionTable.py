import sys

from MzingaShared.Core.FixedCache import FixedCache


class TranspositionTableEntryType:
    Exact = 0
    LowerBound = 1
    UpperBound = 2


class TranspositionTableEntry:
    Type = None      # 24
    Value = None     # 24
    Depth = None     # 24
    BestMove = None  # 56
    SizeInBytes = 128


def transposition_table_replace_entry_predicate(existing_entry, new_entry):
    return new_entry.Depth > existing_entry.Depth


class TranspositionTable(FixedCache):
    DefaultSizeInBytes = 32 * 1024 * 1024
    FillFactor = 0.92  # To leave room for unaccounted for overhead and unused dictionary capacity
    EntrySizeInBytes = (12 * sys.getsizeof(float)) + TranspositionTableEntry.SizeInBytes

    def __init__(self, size_in_bytes=DefaultSizeInBytes, rep=transposition_table_replace_entry_predicate):
        super().__init__(size_in_bytes, rep)

    def get_capacity(self, size_in_bytes):
        if size_in_bytes < self.EntrySizeInBytes:
            raise ValueError("size_in_bytes")

        return 1 + round(self.FillFactor * size_in_bytes / self.EntrySizeInBytes)
