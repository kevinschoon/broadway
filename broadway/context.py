class Props():
    def __init__(self, actor_class: type, *args, **kwargs):
        self.actor_class = actor_class
        self.args = args
        self.kwargs = kwargs


class ActorRefFactory():
    def actor_of(self, props: Props, actor_name=None):
        raise NotImplementedError()


class ActorContext(ActorRefFactory):
    def __init__(self, system):
        super().__init__()
        self.system = system
        self.this = None
        self.sender = None
        self.receive_timeout = None

    def actor_of(self, props: Props, actor_name=None):
        return self.system.actor_of(props, actor_name)


# TODO: eventually want to have actorRef expose instead of actor itself
class ActorRef():
    def __init__(self, name, actor, task):
        self.name = name
        self.actor = actor
        self.task = task