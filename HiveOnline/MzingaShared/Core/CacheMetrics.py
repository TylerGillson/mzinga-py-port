class CacheMetrics:
    _hits = 0
    _misses = 0
    _stores = 0
    _updates = 0

    @property
    def hits(self):
        return self._hits

    @property
    def misses(self):
        return self._misses

    @property
    def stores(self):
        return self._stores

    @property
    def updates(self):
        return self._updates

    @property
    def hit_ratio(self):
        return self.hits / max(self.hits + self.misses, 1)

    def __init__(self):
        pass

    def __repr__(self):
        return "H: %d M: %d HR: %02f" % (self.hits, self.misses, self.hit_ratio)

    def hit(self):
        self._hits += 1

    def miss(self):
        self._misses += 1

    def store(self):
        self._stores += 1

    def update(self):
        self._updates += 1

    def reset(self):
        self._hits = 0
        self._misses = 0
        self._stores = 0
        self._updates = 0
