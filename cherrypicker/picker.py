from .exceptions import *

from collections.abc import Callable, Iterable, Mapping
from fnmatch import fnmatchcase
import re


class CherryPicker(object):
    """
    A utility for drilling down into complex data structures and reducing them
    down to flat tables of data.
    """

    def __init__(self, obj, on_missing='ignore', on_leaf='raise',
                 on_error='ignore'):
        self._mapping = False
        self._leaf = False
        if isinstance(obj, Mapping):
            self._mapping = True
        elif isinstance(obj, str) or not isinstance(obj, Iterable):
            # Treat strings as leaves too for convenience.
            self._leaf = True

        self._opts = {
            'on_missing': on_missing,
            'on_leaf': on_leaf,
            'on_error': on_error
        }
        self._repr = None

        self._obj = obj

    def get(self):
        return self._obj

    def __call__(self, how='all', allow_wildcards=True, case_sensitive=True,
                 regex=False, **predicates):
        return self.__class__(
            self._filter(self._obj, how, allow_wildcards, case_sensitive,
                         regex, **predicates), **self._opts
        )

    def __getitem__(self, args):
        if self._mapping:
            if isinstance(args, tuple):
                # Use lists rather than tuples for better panadas compatibility.
                return self.__class__([self._obj.__getitem__(arg)
                                       for arg in args], **self._opts)
            else:
                return self.__class__(self._obj.__getitem__(args),
                                      **self._opts)
        elif self._leaf:
            return self._obj.__getitem__(args)
        else:
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
                    return self.__class__([[obj.__getitem__(arg) for arg in args]
                                           for obj in self._obj], **self._opts)
                else:
                    return self.__class__([obj.__getitem__(args)
                                           for obj in self._obj],
                                          **self._opts)
            else:
                if isinstance(args, tuple):
                    raise ValueError(
                        'Can only apply a single index or slice to an iterable'
                    )

                return self.__class__(self._obj.__getitem__(args), **self._opts)

    def __iter__(self):
        return self._obj.__iter__()

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        if self._leaf:
            strng = repr(self._obj)
        elif self._mapping:
            strng = 'Mapping{}'.format(type(self._obj))
        else:
            strng = 'Iterable{}, len={}'.format(type(self._obj),
                                                  len(self._obj))

        self._repr = '<{}({})>'.format(self.__class__.__name__, strng)

        return self._repr

    def _filter(self, obj, how, allow_wildcards, case_sensitive, regex,
                **predicates):
        if self._mapping:
            if self._filter_item(obj, how, allow_wildcards, case_sensitive,
                                 regex, **predicates):
                return obj
            else:
                return {}
        elif self._leaf:
            raise LeafError('Cannot filter on a leaf node.')
        else:
            return [item for item in obj if self._filter_item(item, how,
                    allow_wildcards, case_sensitive, regex, **predicates)]

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
                if isinstance(pred, Callable):
                    try:
                        res = pred(val)
                    except:
                        if self._opts['on_error'] == 'raise':
                            raise
                elif hasattr(pred, 'fullmatch'):
                    try:
                        res = pre.fullmatch(val) is not None
                    except:
                        if self._opts['on_error'] == 'raise':
                            raise
                elif isinstance(pred, (str, bytes)):
                    if not isinstance(val, (str, bytes)):
                        if self._opts['on_error'] == 'raise':
                            raise ValueError("{} = '{}'".format(pred, val))
                        res = False

                    if not case_sensitive:
                        pred = pred.lower()
                        val = val.lower()

                    try:
                        if regex:
                            res = re.fullmatch(pred, val) is not None
                        elif allow_wildcards:
                            res = fnmatchcase(val, pred)
                        else:
                            res = pred == val
                    except:
                        if self._opts['on_error'] == 'raise':
                            raise
                else:
                    try:
                        res = pred == val
                    except:
                        if self._opts['on_error'] == 'raise':
                            raise

            if res and how == 'any':
                return True
            elif not res and how == 'all':
                return False

        if how == 'any':
            return False
        elif how == 'all':
            return True
