from collections import namedtuple
from enum import unique, Enum

Envelop = namedtuple("Envelop", ["sender", "message", "timestamp"])

@unique
class SystemMessage(Enum):
    stop = 1
    poison_pill = 2
