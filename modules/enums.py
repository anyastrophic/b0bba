"""A module containing the Enums b0bba uses"""

from enum import Enum


class EmbedColors(Enum):
    """An Enum containing embed colors"""

    ERROR = 0xFF7070
    EXCEPTION = 0xFF0000
    SUCCESS = 0x85FF99
    WARNING = 0xFFC550
    INFO = 0xFFFFFF


class Roles(Enum):
    """An Enum containing role ids"""

    UB_ADMIN = 1054075583597903872
    UB_TRIAL_ADMIN = 1054076384328286259
    UB_SENIOR_ADMIN = 1056050823769104484
    UB_JUNIOR_ADMIN = 1056050831549550724
