import threading

from MzingaShared.Core.CacheMetrics import CacheMetrics

DefaultCapacity = 1024


class FixedCacheEntry(object):
    def __init__(self, list_node, new_entry):
        self.list_node = list_node
        self.entry = new_entry


class FixedCache:
    capacity = None
    replace_entry_predicate = None  # comp. func to be implemented by inheriting classes, i.e., Transposition Table
    metrics = CacheMetrics()

    _dict = {}
    _list = []
    _store_lock = threading.Lock()

    @property
    def count(self):
        """count"""
        return len(self._dict)

    @property
    def usage(self):
        """usage"""
        return self.count / self.capacity

    def __init__(self, capacity=DefaultCapacity, replace_entry_predicate=None):
        if capacity <= 0:
            raise ValueError("Invalid capacity.")

        self.capacity = capacity
        self.replace_entry_predicate = replace_entry_predicate
        self._dict = {}
        self._list = []

    def __repr__(self):
        return "U: %d/%d (%2f) %s" % (self.count, self.capacity, self.usage, self.metrics)

    def store(self, key, new_entry):
        if key not in self._dict.keys():
            # New entry
            self._store_lock.acquire()

            if self.count == self.capacity:
                # Make space
                first = self._list[0]
                self._dict.pop(first)
                self._list.pop(0)

            # Add
            self.store_internal(key, new_entry)
            self.metrics.store()
            self._store_lock.release()
        else:
            # Existing entry
            existing_entry = self._dict[key]

            if self.replace_entry_predicate is None or self.replace_entry_predicate(existing_entry.entry, new_entry):
                # Replace
                if existing_entry.list_node in self._list:
                    self._list.remove(existing_entry.list_node)
                self.store_internal(key, new_entry)
                self.metrics.update()

    def store_internal(self, key, new_entry):
        self._list.append(key)
        list_node = self._list[-1]
        wrapped_entry = FixedCacheEntry(list_node, new_entry)
        self._dict[key] = wrapped_entry

    def try_lookup(self, key):
        try:
            wrapped_entry = self._dict[key]
            entry = wrapped_entry.entry
            self.metrics.hit()
            return True, entry
        except KeyError:
            self.metrics.miss()
            return False, None

    def clear(self):
        self._dict = {}
        self._list = []
        self.metrics.reset()
