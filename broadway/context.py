__author__ = 'leonmax'

class ActorRefFactory():
    def actor_of(self, actor_class, actor_name=None, *args, **kwargs):
        raise NotImplementedError()


class ActorContext(ActorRefFactory):
    def __init__(self, system):
        super().__init__()
        self.system = system
        self.this = None
        self.sender = None
        self.receive_timeout = None

    def actor_of(self, actor_class, actor_name=None, *args, **kwargs):
        return self.system.actor_of(actor_class, actor_name, *args, **kwargs)


# TODO: eventually want to have actorRef expose instead of actor itself
class ActorRef():
    def __init__(self, name, actor, task):
        self.name = name
        self.actor = actor
        self.task = task