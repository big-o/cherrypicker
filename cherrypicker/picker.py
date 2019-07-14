from .exceptions import *

from collections.abc import Callable, Iterable, Mapping
from fnmatch import fnmatchcase
import re


class CherryPicker(object):
    """
    Reduces nestings of iterable and mappable objects into flat tables.

    The CherryPicker class allows you to apply chained filter and extract
    operations to an object with complex structure. All the cherry picker uses
    to navigate your object is iterable and mapping interfaces. Anything
    without either of those interfaces (or a string) is treated as a leaf node.

    Each chained operation will return a new :class:`CherryPicker` which
    wraps the resulting data from that operation. To get the wrapped data back,
    use the :meth:`CherryPicker.get` method.

    Filter operations are applied with parentheses.
    """

    _PRED_RULES = 'all', 'any'

    def __new__(cls, obj, **kwargs):
        ccls = cls._get_cherry_class(obj)
        picker = super(CherryPicker, cls).__new__(ccls)
        return picker

    def __init__(self, obj, on_missing='ignore', on_leaf='raise',
                 on_error='ignore', default=None):
        self._opts = {
            'on_missing': on_missing,
            'on_leaf': on_leaf,
            'on_error': on_error,
            'default': default
        }
        self._repr = None

        self._obj = obj

    @classmethod
    def _get_cherry_class(cls, obj):
        if isinstance(obj, Mapping):
            ccls = CherryPickerMapping
        elif isinstance(obj, str) or not isinstance(obj, Iterable):
            ccls = CherryPickerLeaf
        else:
            ccls = CherryPickerIterable
        return ccls

    @property
    def is_leaf(self):
        return False

    def get(self):
        """
        Obtain the original data that this object wraps.
        """
        return self._obj

    def keys(self, peek=5):
        raise NotImplementedError()

    def __getitem__(self, args):
        raise NotImplementedError()

    def _make_child(self, obj):
        cls = CherryPicker._get_cherry_class(obj)

        return cls(obj, **self._opts)


class CherryPickerTraversable(CherryPicker):
    """
    Abstract class for traversable (mappable and/or iterable) nodes.
    """

    _RE_ERR = type(re.error(''))

    def __call__(self, *args, **kwargs):
        """
        Shortcut to :meth:`.filter`.
        """
        return self.filter(*args, **kwargs)

    def __iter__(self):
        return self._obj.__iter__()

    def __len__(self):
        return len(self._obj)

    def filter(self, how='all', allow_wildcards=True, case_sensitive=True,
                 regex=False, **predicates):
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

        if how not in self._PRED_RULES:
            raise ValueError(
                    '`how` parameter must be one of {}'.format(self._PRED_RULES))

        return self._make_child(
            self._filter(self._obj, how, allow_wildcards, case_sensitive,
                         regex, **predicates)
        )

    def _filter(self, obj, how, allow_wildcards, case_sensitive, regex,
                **predicates):
        raise NotImplementedError()

    def _filter_item(self, obj, how, allow_wildcards, case_sensitive, regex,
                     **predicates):
        for node, pred in predicates.items():
            if node not in obj:
                if self._opts['on_missing'] == 'raise':
                    raise MissingNodeError(
                        '`{}` node does not exist'.format(node)
                    )
                res = False

            else:
                val = obj[node]
                res = False
                try:
                    if isinstance(pred, Callable):
                        res = pred(val)
                    elif hasattr(pred, 'fullmatch'):
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

                except self._RE_ERR as e:
                    # Invalid regex. Always raise.
                    raise

                except Exception as e:
                    if self._opts['on_error'] == 'raise':
                        raise
                    res = False

            if res and how == 'any':
                return True
            elif not res and how == 'all':
                return False

        if how == 'any':
            return False
        elif how == 'all':
            return True

    def keys(self):
        raise NotImplementedError()

    def _filter(self, obj, how, allow_wildcards, case_sensitive, regex,
                **predicates):
        raise NotImplementedError()


class CherryPickerLeaf(CherryPicker):
    """
    A non-traversable node (end-point).

    This class cannot perform filter or extract operations; it only exists to
    return a result (with :meth:`.get`).
    """

    @property
    def is_leaf(self):
        return True

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        self._repr = '<{}({})>'.format(self.__class__.__name__,
                                       repr(self._obj))

        return self._repr


class CherryPickerMapping(CherryPickerTraversable):
    """
    A mappable (key->value pairs) object to be cherry picked.
    """

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

    def __getitem__(self, args):
        if isinstance(args, tuple):
            # Use lists rather than tuples for better panadas compatibility.
            return self._make_child([self._obj.__getitem__(arg)
                                     for arg in args])
        else:
            return self._make_child(self._obj.__getitem__(args))

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        self._repr = '<{}({})>'.format(
            self.__class__.__name__,
            self._obj.__class__.__name__
        )

        return self._repr

    def _filter(self, obj, how, allow_wildcards, case_sensitive, regex,
                **predicates):
        if self._filter_item(obj, how, allow_wildcards, case_sensitive,
                             regex, **predicates):
            return obj
        else:
            return self._opts['default']


class CherryPickerIterable(CherryPickerTraversable):
    """
    A collection of objects to be cherry picked.
    """

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

    def __getitem__(self, args):
        propagate = None
        if isinstance(args, tuple):
            # Nasty hack because __getitem__ does not support kwargs
            if len(args) > 1 and args[-1] in (True, False):
                propagate = args[-1]
                args = args[:-1]

            if len(args) == 1:
                args = args[0]

        if propagate is None:
            propagate = not isinstance(args, (int, slice))

        if propagate:
            # Always create lists for better pandas/numpy integration
            if isinstance(args, tuple):
                return self._make_child([
                            [obj.__getitem__(arg)
                             if arg in obj else self._opts['default']
                             for arg in args]
                            for obj in self._obj])
            else:
                return self._make_child([obj.__getitem__(args)
                                         if args in obj
                                         else self._opts['default']
                                         for obj in self._obj])
        else:
            return self._make_child(self._obj.__getitem__(args))

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        self._repr = '<{}({}, len={})>'.format(self.__class__.__name__,
                self._obj.__class__.__name__, len(self._obj))

        return self._repr

    def _filter(self, obj, how, allow_wildcards, case_sensitive, regex,
                **predicates):
        return [item for item in obj if self._filter_item(item, how,
                allow_wildcards, case_sensitive, regex, **predicates)]
