import collections.abc


__all__ = ("OrderedSet",)


class OrderedSet(collections.abc.MutableSet):
    """
    Set that remembers original insertion order.

    Implementation based on a doubly linked link and an internal dictionary.
    This design gives OrderedSet the same big-Oh running times as regular sets
    including :math:`O(1)` adds, removes, and lookups as well as :math:`O(n)`
    iteration.

    Adapted from: https://code.activestate.com/recipes/576694/
    """

    def __init__(self, iterable=None, key=None):
        self._end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self._map = {}  # key --> [key, prev, next]
        self._key = key
        if iterable is not None:
            self |= iterable

    def _get_key(self, item):
        if self._key is not None:
            return self._key(item)
        else:
            return item

    def __len__(self):
        return len(self._map)

    def __contains__(self, item):
        return self._get_key(item) in self._map

    def add(self, item):
        key = self._get_key(item)
        if key not in self._map:
            end = self._end
            curr = end[1]
            curr[2] = end[1] = self._map[key] = [item, curr, end]

    def discard(self, item):
        key = self._get_key(item)
        if key in self._map:
            item, prev, next = self._map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self._end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self._end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError("set is empty")
        item = self._end[1][0] if last else self._end[2][0]
        self.discard(item)
        return item

    def __repr__(self):
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
