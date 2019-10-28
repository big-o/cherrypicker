from __future__ import division

from .exceptions import LeafError
from .picker import CherryPicker


__all__ = ("CherryPickerLeaf",)


class CherryPickerLeaf(CherryPicker):
    """
    A non-traversable node (an end-point).

    This class cannot perform filter or extract operations; it only exists to
    return a result (with :meth:`.get`).
    """

    def __new__(cls, obj, **kwargs):
        picker = super(CherryPicker, cls).__new__(cls)
        return picker

    @property
    def is_leaf(self):
        return True

    def __getitem__(self, item):
        if self._opts["on_leaf"] == "raise":
            raise LeafError()
        return self._obj.__getitem__(item)

    def __repr__(self):
        if self._repr is not None:
            return self._repr

        self._repr = "<{}({})>".format(self.__class__.__name__, repr(self._obj))

        return self._repr


CherryPicker.register_cherry_type("leaf", CherryPickerLeaf)
