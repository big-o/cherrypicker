class CherryPickerError(Exception):
    """
    A generic cherrypicker error.
    """


class LeafError(CherryPickerError):
    """
    Raised when attempting to perform node actions on a leaf.
    """
