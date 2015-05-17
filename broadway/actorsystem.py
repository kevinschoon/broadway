import asyncio
from asyncio import coroutine as coro
import logging
import time
import sys
from broadway.context import ActorRef, ActorContext, Props
from broadway.exception import ActorCreationFailureException

__author__ = 'leonmax'

class ActorSystem():
    def __init__(self, loop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._registry = {}
        self._terminated = None
        self._other_tasks = set()
        self.settings = {}  # TODO: settings
        self.startTime = time.time() * 1000
        # TODO: address / actor hierarchy

    @property
    def uptime(self):
        return time.time() - self.startTime/1000

    def _make_actor_name(self, actor_class, actor_name):
        if actor_name in self._registry:
            raise ActorCreationFailureException("actor_name already exists")
        elif not actor_name:
            actor_name = actor_class.__name__
            # this is inefficient...
            count = 0
            while actor_name in self._registry:
                actor_name = "{0}${1}".format(actor_class.__name__, count)
                count += 1
        return actor_name

    def actor_of(self, props: Props, actor_name: str=None):
        actor_name = self._make_actor_name(props.actor_class, actor_name)
        props.kwargs['loop'] = self._loop
        props.kwargs['context'] = ActorContext(self)
        actor = props.actor_class(*props.args, **props.kwargs)
        running_task = self._loop.create_task(actor.start())
        self._registry[actor_name] = ActorRef(actor_name, actor, running_task)
        # TODO: eventually want to have actorRef expose instead of actor itself
        return actor

    @coro
    def stop(self):
        if self._terminated:
            self._terminated.set_result(True)
        else:
            raise Exception("system has never started")

    @coro
    def _start(self):
        self._terminated = asyncio.Future()
        yield from self._terminated

    @coro
    def cancel_actor(self, name):
        actor_ref = self._registry.pop(name)
        actor_ref.task.cancel()
        yield from asyncio.wait_for(actor_ref.task)

    @coro
    def cancel_all(self):
        futures = list(self._other_tasks)
        while futures:
            task = futures.pop()
            task.cancel()
        while self._registry:
            name, actor_ref = self._registry.popitem()
            futures.append(actor_ref.task)
            actor_ref.task.cancel()

        yield from asyncio.wait(futures)

    def run_until_stop(self, coros, exit_after=False):
        try:
            for c in coros:
                task = self._loop.create_task(c)
                self._other_tasks.add(task)
            self._loop.run_until_complete(self._start())
            if exit_after:
                self._loop.run_until_complete(self.cancel_all())
                self._loop.stop()
                self._loop.close()
                sys.exit(0)
        except Exception as e:
            logging.error(e)
            self._loop.stop()
            self._loop.close()
            sys.exit(1)