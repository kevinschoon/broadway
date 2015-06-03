from collections import namedtuple
from enum import unique, Enum

class Envelop(namedtuple("Envelop", ["sender", "message", "timestamp"])):
    pass

@unique
class SystemMessage(Enum):
    stop = 1
    poison_pill = 2
