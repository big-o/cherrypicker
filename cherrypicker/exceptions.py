class CherryPickerError(object):
    """
    A generic cherrypicker error.
    """

class LeafError(CherryPickerError):
    """
    Raised when attempting a node traversal operation on a leaf.
    """


class MissingNodeError(CherryPickerError):
    """
    Raised when a node is unexpectedly missing.
    """
