

class SnipsNLUError(Exception):
    """Base class for exceptions raised in the snips-nlu library"""


class DatasetFormatError(SnipsNLUError):
    """Raised when attempting to create a Snips NLU dataset using a wrong
    format"""


class EntityFormatError(DatasetFormatError):
    """Raised when attempting to create a Snips NLU entity using a wrong
    format"""


class IntentFormatError(DatasetFormatError):
    """Raised when attempting to create a Snips NLU intent using a wrong
    format"""
