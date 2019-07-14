class CherryPickerError(Exception):
    """
    A generic cherrypicker error.
    """


class MissingNodeError(CherryPickerError):
    """
    Raised when a node is unexpectedly missing.
    """
