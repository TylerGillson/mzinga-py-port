import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(dirname(os.getcwd()))))  # Add root directory to PYTHONPATH

from MzingaShared.Core.FixedCache import FixedCache


class TranspositionTableEntryType:
    Exact = 0
    LowerBound = None
    UpperBound = None


class TranspositionTableEntry:
    Type = None
    Value = None
    Depth = None
    BestMove = None
    SizeInBytes = 256


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
