from __future__ import division

from .picker import CherryPicker

from collections.abc import Callable
from fnmatch import fnmatchcase
from functools import partial
from itertools import chain
from joblib import Parallel, delayed
import re


__all__ = ("CherryPickerIterable", "CherryPickerMapping", "CherryPickerTraversable")


class CherryPickerTraversable(CherryPicker):
    """
    Abstract class for traversable (mappable and/or iterable) nodes.
    """

    _RE_ERR = type(re.error(""))

    def __call__(self, *args, opts=None, **kwargs):
        """
        Shortcut to :meth:`.filter`.
        """
        if opts is None:
            opts = self._opts
        return self.filter(*args, opts=opts, **kwargs)

    def __iter__(self):
        return self._obj.__iter__()

    def __len__(self):
        return len(self._obj)

    @classmethod
    def _make_child(cls, obj, parent):
        ccls = cls._get_cherry_class(obj, parent)
        if parent is not None:
            child = ccls(obj, **parent._opts)
        else:
            child = ccls(obj, **cls._opts)
        child._parent = parent
        return child

    def filter(
        self,
        how="all",
        allow_wildcards=True,
        case_sensitive=True,
        regex=False,
        opts=None,
        **predicates
    ):
        """
        Return a filtered view of the child nodes. This method is usually
        accessed via :meth:`CherryPicker.__call__`

        For an object with a mappable interface, this will return the object
        itself if it matches the predicates according to the rules specified.

        For an object with an iterable but not a mappable interface, a
        collection of child objects matching the predicates according to the
        rules specified will be returned.

        This method is not implemented for leaf nodes and will cause an error
        to be raised.

        :Example:

        Find any items with a name of ``Alice``:

        >>> picker(name='Alice')

        Find any items with a name of ``Alice`` and an age of 20:

        >>> picker(name='Alice', age=20)

        Find any items with a name of ``Alice`` `or` an age of 20:

        >>> picker(name='Alice', age=20, how='any')

        Find any items with a name of ``Alice`` and an age of 20 or more:

        >>> picker(name='Alice', age=lambda a: a >= 20)

        Find any items with a name beginning with ``Al``:

        >>> picker(name='Al*')

        Find any items with a name beginning with ``Al`` or ``al``:

        >>> picker(name='Al*', case_sensitive=False)

        Find any items with a name of ``Al*``:

        >>> picker(name='Al*', allow_wildcards=False)

        Find any items with a name matching a particular pattern (these two
        lines are equivalent):

        >>> picker(name=r'^(?:Alice|Bob)$', regex=True, case_sensitive=False)
        >>> picker(name=re.compile(r'^(?:Alice|Bob)$', re.I))

        :param how: The rule to be applied to predicate matching. May be one
                of ('all', 'any').
        :type how: str.
        :param allow_wildcards: If True, special characters
                (``*``, ``?``, ``[]``) in any string predicate values will be
                treated as wildcards according to :meth:`fnmatch.fnmatchcase`.
        :type allow_wildcards: bool, default = True.
        :param case_sensitive: If True, any comparisons to strings or
                uncompiled regular expressions will be case sensitive.
        :type case_sensitive: bool, default = True.
        :param regex: If True, any string comparisons will be reinterpreted as
                regular expressions. If ``case_sensitive`` is False, they will
                be case-insensitive patterns. For more complex regex options,
                omit this parameter and provide pre-compiled regular expression
                patterns in your predicates instead. All regular expressions
                will be compared to string values using a full match.
        :type regex: bool, default = False.
        :param predicates: Keyword arguments where the keys are the object keys
                used to get the comparison value, and the values are either a
                value to compare, a regular expression to perform a full match
                against, or a callable function that takes a single value as
                input and returns something that evaluates to True if the value
                passes the predicate, or False if it does not.
        :type predicates: str, regular expression or Callable.

        :return: If this is a mappable object, the object itself if it passes
                the predicates. If not and this is an iterable object, a
                collection of children that pass the predicates.
        :rtype: :class:`CherryPicker`.
        """

        if opts is None:
            opts = self._opts

        if how not in self._PRED_RULES:
            raise ValueError(
                "`how` parameter must be one of {}".format(self._PRED_RULES)
            )

        if len(predicates) == 0:
            return self

        return self._make_child(
            self._filter(
                how, allow_wildcards, case_sensitive, regex, opts=opts, **predicates
            ),
            self,
        )

    def _filter(
        self, how, allow_wildcards, case_sensitive, regex, opts=None, **predicates
    ):
        raise NotImplementedError()

    # Needs to be a class method so we can parallelise it.
    @classmethod
    def _filter_item(
        cls, obj, how, allow_wildcards, case_sensitive, regex, opts=None, **predicates
    ):
        if opts is None:
            opts = cls._opts

        for attr, pred in predicates.items():
            if attr not in obj:
                if opts["on_missing"] == "raise":
                    raise AttributeError("`{}` attribute does not exist".format(attr))
                res = False

            else:
                val = obj[attr]
                res = False
                try:
                    if isinstance(pred, Callable):
                        res = pred(val)
                    elif hasattr(pred, "fullmatch"):
                        res = pred.fullmatch(val) is not None
                    elif isinstance(pred, (str, bytes)):
                        if not case_sensitive:
                            pred = pred.lower()
                            val = val.lower()

                        if regex:
                            flags = 0 if case_sensitive else re.I
                            res = re.fullmatch(pred, val, flags) is not None
                        elif allow_wildcards:
                            res = fnmatchcase(val, pred)
                        else:
                            res = pred == val
                    else:
                        res = pred == val

                except cls._RE_ERR as e:
                    # Invalid regex. Always raise.
                    raise

                except Exception as e:
                    if opts["on_error"] == "raise":
                        raise
                    res = False

            if res and how == "any":
                return True
            elif not res and how == "all":
                return False

        if how == "any":
            return False
        elif how == "all":
            return True

    def keys(self):
        raise NotImplementedError()


class CherryPickerMapping(CherryPickerTraversable):
    """
    A mappable (key->value pairs) object to be cherry picked from.
    """

    def __new__(cls, obj, **kwargs):
        picker = super(CherryPicker, cls).__new__(cls)
        return picker

    def __contains__(self, key):
        try:
            if isinstance(key, tuple):
                for k in key:
                    self._obj[k]
            else:
                self._obj[key]
            return True
        except KeyError:
            return False

    def keys(self, peek=None):
        """
        :param peek: Not used.
        :type peek: object, optional

        :return: A view of the object's keys.
        :rtype: list
        """
        return self._obj.keys()

    def values(self, peek=None):
        """
        :param peek: Not used.
        :type peek: object, optional

        :return: A view of the object's values.
        :rtype: list
        """
        return self._obj.values()

    def items(self, peek=None):
        """
        :param peek: Not used.
        :type peek: object, optional

        :return: A view of the object's items.
        :rtype: list
        """
        return self._obj.items()

    @classmethod
    def _flatten(cls, obj, flat=None, prefix="", delim="_", maxdepth=100, depth=0):
        """
            Flatten json object with nested keys into a single level.
            Args:
                nested_json: A nested json object.
            Returns:
                The flattened json object if successful, None otherwise.
        """
        if flat is None:
            flat = {}

        if maxdepth is not None and depth > maxdepth:
            flat[prefix[:-1]] = obj
            return flat

        ccls = cls._get_cherry_class(obj)
        if ccls is CherryPickerMapping:
            for key in obj:
                cls._flatten(
                    obj[key],
                    flat,
                    prefix="{}{}{}".format(prefix, key, delim),
                    maxdepth=maxdepth,
                    depth=depth + 1,
                )

        elif ccls is CherryPickerIterable:
            for idx, val in enumerate(obj):
                cls._flatten(
                    val,
                    flat,
                    prefix="{}{}{}".format(prefix, idx, delim),
                    maxdepth=maxdepth,
                    depth=depth + 1,
                )

        else:
            flat[prefix[:-1]] = obj

        return flat

    @property
    def flatten(self, delim="_", maxdepth=100):
        """
        Flatten down the object so that all of its values are leaf nodes.
        """
        flat = self._flatten(self._obj, delim=delim, maxdepth=maxdepth)
        return self._make_child(flat, self._parent)

    def __getitem__(self, args):
        allow_missing = self._opts["on_missing"] == "ignore"
        default = self._opts["default"]
        obj = self._obj

        if isinstance(args, tuple):
            # Use lists rather than tuples for better panadas compatibility.
            if allow_missing:
                items = [
                    obj.__getitem__(arg) if arg in obj else default for arg in args
                ]
            else:
                items = [obj.__getitem__(arg) for arg in args]
        else:
            if allow_missing:
                items = obj.__getitem__(args) if args in obj else default
            else:
                items = obj.__getitem__(args)

        return self._make_child(items, self)

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        self._repr = "<{}({})>".format(
            self.__class__.__name__, self._obj.__class__.__name__
        )

        return self._repr

    def _filter(
        self, how, allow_wildcards, case_sensitive, regex, opts=None, **predicates
    ):
        if opts is None:
            opts = self._opts

        if CherryPickerMapping._filter_item(
            self._obj,
            how,
            allow_wildcards,
            case_sensitive,
            regex,
            opts=opts,
            **predicates
        ):
            return self._obj
        else:
            return self._opts["default"]


class CherryPickerIterable(CherryPickerTraversable):
    """
    A collection of objects to be cherry picked.
    """

    # If the children have different parents to self, e.g. if they are
    # grandchildren.
    _child_parents = None

    def __new__(cls, obj, **kwargs):
        picker = super(CherryPicker, cls).__new__(cls)
        return picker

    def __contains__(self, item):
        return item in self._obj

    @classmethod
    def _make_child(cls, obj, parent, child_parents=None):
        child = super(CherryPickerIterable, cls)._make_child(obj, parent)
        child._child_parents = child_parents
        return child

    @classmethod
    def _flatten(cls, chunk, delim="_", maxdepth=100):
        flats = []
        for item in chunk:
            ccls = cls._get_cherry_class(item)
            if ccls is CherryPickerMapping:
                flats.append(
                    CherryPickerMapping._flatten(item, delim="_", maxdepth=100)
                )
            else:
                flats.append(item)

        return flats

    @property
    def flatten(self, delim="_", maxdepth=100):
        with Parallel(self._effective_n_jobs) as parallel:
            flats = parallel(
                delayed(CherryPickerIterable._flatten)(
                    chunk, delim=delim, maxdepth=maxdepth
                )
                for chunk in self._chunks()
            )
            if self._effective_n_jobs == 1:
                flats = flats[0]
            else:
                flats = self._join_chunks(flats)

            return self._make_child(flats, self._parent)

    def keys(self, peek=5):
        """
        :param peek: The maximum number of items in the iterable to inspect in
                order to ascertain what all possible keys are. If None, all
                items are inspected.
        :type peek: int, optional

        :return: A view of the keys that exist in `all` items that were
                previewed. Individual items may have other keys, but they will
                not be returned unless all the other items inspected also have
                those keys.
        :rtype: list
        """
        preview = self._obj[slice(None, peek, None)]
        try:
            keys = set(preview[0].keys())
        except AttributeError:
            keys = set()

        for item in preview[1:]:
            try:
                keys = keys.intersection(item.keys())
            except AttributeError:
                pass

        return sorted(keys)

    # Needs to be a class method to allow parallelisation.
    @classmethod
    def _filter_chunk(
        cls, chunk, how, allow_wildcards, case_sensitive, regex, opts=None, **predicates
    ):
        if opts is None:
            opts = cls._opts

        items = [
            item
            for item in chunk
            if CherryPickerIterable._filter_item(
                item,
                how,
                allow_wildcards,
                case_sensitive,
                regex,
                opts=opts,
                **predicates
            )
        ]

        return items

    @classmethod
    def _get_child_items(cls, keys, batch):
        if isinstance(keys, tuple):
            items = [[obj.__getitem__(key) for key in keys] for obj in batch]
        else:
            items = [obj.__getitem__(keys) for obj in batch]
        return items

    @classmethod
    def _get_grandchild_items(cls, keys, batch):
        # Always create lists for better pandas/numpy integration
        items = []
        parents = []
        for obj in batch:
            parent = cls._make_child(obj, None)
            items.append(parent.__getitem__(keys).get())
            parents.append(obj)

        return items, parents

    def __getitem__(self, args):
        if len(self._obj) == 0:
            if self._opts["on_missing"] == "ignore":
                return self._make_child([], self)
            else:
                raise IndexError(args)

        propagate = None
        if isinstance(args, tuple):
            # Nasty hack because __getitem__ does not support kwargs
            if len(args) > 1 and args[-1] in (True, False):
                propagate = args[-1]
                args = args[:-1]

            if len(args) == 1:
                args = args[0]

        if propagate is None:
            # Default behaviour
            if isinstance(args, int):
                # Valid iterable index, get from this obj.
                item = self._obj.__getitem__(args)
                if self._child_parents:
                    return self._make_child(item, self._child_parents[args])
                else:
                    return self._make_child(item, self)

            elif isinstance(args, slice):
                items = self._obj.__getitem__(args)
                if self._child_parents:
                    return self._make_child(items, self, self._child_parents[args])
                else:
                    return self._make_child(items, self)

            else:
                # Get from each child
                with Parallel(self._effective_n_jobs) as parallel:
                    children = parallel(
                        delayed(CherryPickerIterable._get_child_items)(args, chunk)
                        for chunk in self._chunks()
                    )
                    if self._effective_n_jobs == 1:
                        children = children[0]
                    else:
                        children = self._join_chunks(children)

                return self._make_child(children, self, self._child_parents)

        elif propagate:
            with Parallel(self._effective_n_jobs) as parallel:
                tree = parallel(
                    delayed(CherryPickerIterable._get_grandchild_items)(args, chunk)
                    for chunk in self._chunks()
                )
                if self._effective_n_jobs == 1:
                    tree = tree[0]
                else:
                    tree = [
                        self._join_chunks([t[0] for t in tree]),
                        self._join_chunks([t[1] for t in tree]),
                    ]

            grandchildren = []
            all_parents = []
            for grandchild, child in zip(tree[0], tree[1]):
                grandchildren.append(grandchild)
                all_parents.append(self._make_child(child, self))

            grandchildren = self._make_child(grandchildren, self, all_parents)
            return grandchildren

        else:
            return self._make_child(
                self._obj.__getitem__(args), self, self._child_parents
            )

    def _chunks(self):
        if len(self._obj) == 0:
            return self._obj

        n_jobs = self._effective_n_jobs
        if not n_jobs:
            return self._obj

        len_obj = len(self._obj)
        chunksize = -(-len_obj // n_jobs)
        for pos in range(0, len_obj, chunksize):
            chunk = self._obj[pos : pos + chunksize]
            yield chunk

    def _join_chunks(self, chunks):
        return list(chain.from_iterable(chunks))

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        try:
            self._repr = "<{}({}, len={})>".format(
                self.__class__.__name__, self._obj.__class__.__name__, len(self._obj)
            )
        except AttributeError:
            self._repr = "<{}({})>".format(
                self.__class__.__name__, self._obj.__class__.__name__
            )

        return self._repr

    def _filter(
        self, how, allow_wildcards, case_sensitive, regex, opts=None, **predicates
    ):
        if opts is None:
            opts = self._opts

        with Parallel(n_jobs=self._effective_n_jobs) as parallel:
            items = parallel(
                delayed(CherryPickerIterable._filter_chunk)(
                    chunk,
                    how,
                    allow_wildcards,
                    case_sensitive,
                    regex,
                    opts,
                    **predicates
                )
                for chunk in self._chunks()
            )

        if self._effective_n_jobs == 1:
            items = items[0]
        else:
            items = self._join_chunks(items)

        return items


CherryPicker.register_cherry_type("iterable", CherryPickerIterable)
CherryPicker.register_cherry_type("mapping", CherryPickerMapping)
