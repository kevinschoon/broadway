import asyncio
from actress.exception import ActorCreationFailureException
from actress.message import Envelop


class Actor():
    def __init__(self, loop, max_inbox_size=0):
        self._loop = loop
        self._max_inbox_size = max_inbox_size
        self._inbox = asyncio.Queue(maxsize=self._max_inbox_size,
                                    loop=self._loop)
        self._keep_running = False
        self._run_complete = asyncio.Future()
        self.context = ActorContext(self)
        self._resume = None

    @asyncio.coroutine
    def receive(self, message: 'Any'):
        pass

    @asyncio.coroutine
    def tell(self, target: 'Actor', message: 'Any'):
        try:
            yield from target._deliver(Envelop(self, message))
        except AttributeError as e:
            print('Target does not have a _deliver method. Is it an actor?')
            raise

    @asyncio.coroutine
    def ask(self, target: 'Actor', message: 'Any') -> asyncio.Future:
        promise_actor = PromiseActor()
        promise_actor.run()
        yield from self.tell(target, Envelop(promise_actor, message))
        return promise_actor.result

    @asyncio.coroutine
    def _deliver(self, envelop: Envelop):
        yield from self._inbox.put(envelop)

    @asyncio.coroutine
    def pre_start(self):
        pass

    def run(self):
        self._loop.create_task(self.start())

    @asyncio.coroutine
    def suspend(self):
        self._resume = asyncio.Future()

    @asyncio.coroutine
    def resume(self):
        if self._resume:
            self._resume.set_result(True)

    @asyncio.coroutine
    def start(self):
        self._keep_running = True
        yield from self.pre_start()
        while self._keep_running:
            if self._resume:
                yield from self._resume
            envelop = yield from self._inbox.get()
            yield from self._invoke(envelop)

        # Signal that the loop has finished.
        self._run_complete.set_result(True)

    @asyncio.coroutine
    def _invoke(self, envelop):
        try:
            self.context.sender = envelop.sender
            yield from self.receive(envelop.message)
        except Exception as e:
            self._handleInvokeFailure(e)

    def _handleInvokeFailure(self, e):
        print(e)  # TODO: might change to log, might handle better

    @asyncio.coroutine
    def stop(self):
        self._keep_running = False
        yield from self.post_stop()
        yield from self._run_complete

    @asyncio.coroutine
    def post_stop(self):
        pass

class PromiseActor(Actor):
    def __init__(self):
        super().__init__()
        self.result = asyncio.Future()

    @asyncio.coroutine
    def receive(self, message):
        self.result.set_result(message)
        yield from self.stop()


class ActorContext():
    def __init__(self, this):
        self.this = this
        self.sender = None


# TODO: eventually want to have actorRef expose instead of actor itself
class ActorRef():
    def __init__(self, name):
        self.name = name


class ActorSystem():
    def __init__(self, loop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._registry = {}
        self._terminated = asyncio.Future()

    def act_of(self, actor_name, actor_class, *args, **kwargs):
        if actor_name in self._registry:
            raise ActorCreationFailureException("actor_name already exists")
        kwargs['loop'] = self._loop
        actor = actor_class(*args, **kwargs)
        self._registry[actor_name] = actor
        actor.run()
        return actor

    @asyncio.coroutine
    def tell(self, target: Actor, message):
        try:
            # use special object no_sender instead of None
            yield from target._deliver(Envelop(None, message))
        except AttributeError as e:
            print('Target does not have a _deliver method. Is it an actor?')
            raise

    @asyncio.coroutine
    def ask(self, target: Actor, message):
        promise_actor = PromiseActor()
        promise_actor.run()
        yield from self.tell(target, Envelop(promise_actor, message))
        return promise_actor.result

    @asyncio.coroutine
    def stop(self):
        self._terminated.set_result(True)

    def init(self, coro_task):
        self._loop.create_task(coro_task)
        return self

    @asyncio.coroutine
    def start(self):
        yield from self._terminated

    def run(self):
        try:
            self._loop.run_until_complete(self.start())
        finally:
            self._loop.close()






