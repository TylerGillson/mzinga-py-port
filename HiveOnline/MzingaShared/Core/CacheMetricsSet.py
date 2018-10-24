from HiveOnline.MzingaShared.Core.CacheMetrics import CacheMetrics


class CacheMetricsSet:
    _cache_metrics = {}

    def __init__(self):
        self.reset()

    def __getitem__(self, name):
        return self._get_cache_metrics(name)

    def reset(self):
        self._cache_metrics = {}

    def _get_cache_metrics(self, name):
        try:
            cm = self._cache_metrics[name]
            return cm
        except KeyError:
            cm = CacheMetrics()
            self._cache_metrics.update({name: cm})
            return self._cache_metrics[name]
