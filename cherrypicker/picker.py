from __future__ import division

from collections.abc import Iterable, Mapping
from joblib import effective_n_jobs


__all__ = ("CherryPicker",)


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

    :param obj: The data to operate on.
    :type obj: object.
    :param on_missing: Action to perform when trying to get an attribute that
            doesn't exist from an object with a Mapping interface. ``ignore``
            will do nothing, ``raise`` will raise an :class:`AttributeError`.
    :type on_missing: str, default = ``ignore``.
    :param on_error: Action to perform if an error occurs during filtering.
            ``ignore`` will just mean the filter operation returns False, and
            ``raise`` will mean the error is raised.
    :type on_error: str, default = ``ignore``
    :param on_leaf: Action to perform when calling :meth:`__getitem__` on a
            leaf node. ``raise`` will cause a
            :class:`cherrypicker.exceptions.LeafError`` to be raised. ``get``
            will return the result of :meth:`__getitem__` on the wrapped item.
    :type on_leaf: str, default = ``raise``.
    :param leaf_types:  By default, anything doesn't have an Iterable or
            Mapping interface will be treated as a leaf. Any classes specifed
            in this parameter will also be treated as leaves regardless of any
            interfaces they conform to. ``leaf_types`` may be a class, a method
            that resolves to True if an object passed to it should be treated
            as a leaf, or a tuple of classes/methods.
    :param default: The item to return when extracting an attribute that does
            not exist from an object.
    :type default: object, default = None
    :param n_jobs: The maximum number of parallel processes to run when
            performing operations on iterable objects. If n_jobs > 1 then the
            iterable will be processed in parallel batches. If n_jobs = -1, all
            the CPUs are used. For n_jobs below -1, (n_cpus + 1 + n_jobs) are
            used. Thus for n_jobs = -2, all CPUs but one are used. See
            :class:`joblib.Parallel` for more details on this parameter.
    :type n_jobs: int, default = None

    :Examples:

    Data extraction may be done with the getitem interface. Let's say we have a
    list of objects and we want to get a flat list of the ``name`` attributes
    for each item in the list:

    >>> data = [ { 'name': 'Alice', 'age': 20}, { 'name': 'Bob', 'age': 30 } ]
    >>> picker = CherryPicker(data)
    >>> picker['name'].get()
    ['Alice', 'Bob']

    We can also request multiple attributes for each item to produce a flat
    table:

    >>> data = [ { 'name': 'Alice', 'age': 20}, { 'name': 'Bob', 'age': 30 } ]
    >>> picker = CherryPicker(data)
    >>> picker['name', 'age'].get()
    [['Alice', 20], ['Bob', 30]]

    Filter operations are applied with parentheses. For example, to get every
    ``name`` attribute from each item in a list called ``data``:

    >>> data = [ { 'name': 'Alice', 'age': 20}, { 'name': 'Bob', 'age': 30 } ]
    >>> picker = CherryPicker(data)
    >>> picker(name='Alice')['age'].get()
    [30]

    Multiple filters may be provided:

    >>> data = [ { 'name': 'Alice', 'age': 20}, { 'name': 'Bob', 'age': 30 } ]
    >>> picker = CherryPicker(data)
    >>> picker(name='Alice' age=lambda x: x>10, how='any').get()
    [{'name': 'Alice', 'age': 20}, {'name': 'Bob', 'age': 30}]

    Filters can also be chained:

    >>> data = [ { 'name': 'Alice', 'age': 20}, { 'name': 'Bob', 'age': 30 } ]
    >>> picker = CherryPicker(data)
    >>> picker(age=lambda x: x>10)(name='B*')['name'].get()
    ['Bob']


    See :meth:`CherryPicker.filter` for more filtering options.
    """

    _PRED_RULES = "all", "any"

    _leaf_types = (str, bytes)
    _leaf_funcs = tuple()
    _opts = {
        "on_missing": "ignore",
        "on_error": "ignore",
        "on_leaf": "raise",
        "leaf_types": _leaf_types + _leaf_funcs,
        "default": None,
        "n_jobs": None,
    }
    _cherry_types = {}

    def __new__(cls, obj, **kwargs):
        ccls = cls._get_cherry_class(obj)
        picker = super(CherryPicker, cls).__new__(ccls)
        return picker

    def __eq__(self, other):
        return self._obj == other._obj

    def __init__(
        self,
        obj,
        on_missing=_opts["on_missing"],
        on_error=_opts["on_error"],
        on_leaf=_opts["on_leaf"],
        leaf_types=_opts["leaf_types"],
        default=_opts["default"],
        n_jobs=_opts["n_jobs"],
    ):

        # Anything that gets shared with children goes in here.
        self._opts = {
            "on_missing": on_missing,
            "on_error": on_error,
            "on_leaf": on_leaf,
            "default": default,
            "leaf_types": leaf_types,
            "n_jobs": n_jobs,
        }

        # Properties that are unique to this instance.
        self._repr = None

        self._leaf_types, self._leaf_funcs = self._parse_leaf_types(leaf_types)

        self._effective_n_jobs = effective_n_jobs(n_jobs)

        self._parent = None
        self._obj = obj

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, attr
                )
            ) from None

    def _parse_leaf_types(self, leaf_types):
        if leaf_types is None:
            _leaf_types = tuple()
            _leaf_funcs = tuple()
        else:
            try:
                _leaf_types = tuple(
                    leaf for leaf in leaf_types if isinstance(leaf, type)
                )

                _leaf_funcs = tuple(
                    leaf for leaf in leaf_types if leaf not in _leaf_types
                )

                if any([not hasattr(func, "__call__") for func in _leaf_funcs]):
                    raise ValueError(
                        "leaf_types must only contain types and Callables."
                    )

            except TypeError:
                if isinstance(leaf_types, type):
                    _leaf_types = (leaf_types,)
                    _leaf_funcs = tuple()
                elif hasattr(leaf_types, "__call__"):
                    _leaf_types = tuple()
                    _leaf_funcs = (leaf_types,)
                else:
                    raise ValueError(
                        "leaf_types must only contain types and Callables."
                    )

        return _leaf_types, _leaf_funcs

    @classmethod
    def _get_cherry_class(cls, obj, parent=None):
        ccls = None
        if parent is None:
            leaf_types = cls._leaf_types
            leaf_funcs = cls._leaf_funcs
        else:
            leaf_types = parent._leaf_types
            leaf_funcs = parent._leaf_funcs

        if isinstance(obj, leaf_types):
            ccls = cls._cherry_types["leaf"]
        elif len(leaf_funcs) > 0:
            for func in leaf_funcs:
                try:
                    if func(obj):
                        ccls = cls._cherry_types["leaf"]
                        break
                except:
                    # TODO: Should we warn, or have a user-defined action?
                    pass

        if ccls is None:
            if isinstance(obj, Mapping):
                ccls = cls._cherry_types["mapping"]
            elif isinstance(obj, Iterable):
                ccls = cls._cherry_types["iterable"]
            else:
                ccls = cls._cherry_types["leaf"]

        return ccls

    @classmethod
    def register_cherry_type(cls, cherry, typ):
        cls._cherry_types[cherry] = typ

    @property
    def is_leaf(self):
        return False

    @property
    def parents(self):
        """
        Alias for :meth:`.parent`.
        """
        return self.parent

    @property
    def parent(self):
        """
        Get the parent or iterable of parents.
        """
        if self._parent is not None:
            return self._parent
        raise AttributeError("Root node has no parent.")

    def get(self):
        """
        Obtain the original data that this object wraps.
        """
        return self._obj

    def keys(self, peek=5):
        raise NotImplementedError()

    def __getitem__(self, args):
        raise NotImplementedError()
