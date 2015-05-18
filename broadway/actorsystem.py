import asyncio
from asyncio import coroutine, iscoroutine, iscoroutinefunction
from inspect import isfunction, isbuiltin
import logging
import time
import sys
from broadway.actorref import Props, ActorRefFactory
from broadway.cell import ActorCell
from broadway.exception import ActorCreationFailureException


class ActorSystem(ActorRefFactory):
    def __init__(self, loop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._registry = {}
        self._terminated = None
        self._other_tasks = set()
        self.settings = {}  # TODO: settings
        self.start_time = time.time() * 1000
        self.dead_letters = self.new_mailbox()
        # TODO: address / actor hierarchy

    @property
    def uptime(self):
        return time.time() - self.start_time/1000

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

    def new_mailbox(self, max_inbox_size=0):
        return asyncio.Queue(maxsize=max_inbox_size,
                             loop=self._loop)

    def actor_of(self, props: Props, actor_name: str=None):
        actor_name = self._make_actor_name(props.actor_class, actor_name)
        actor_cell = ActorCell(self, actor_name, props, self.new_mailbox())
        self._registry[actor_name] = actor_cell.run(self._loop)
        return actor_cell.this

    @coroutine
    def stop(self):
        if self._terminated:
            self._terminated.set_result(True)
        else:
            raise Exception("system has never started")

    @coroutine
    def _start(self):
        self._terminated = asyncio.Future()
        yield from self._terminated

    @coroutine
    def cancel_actor(self, name):
        actor_ref = self._registry.pop(name)
        actor_ref.task.cancel()
        yield from asyncio.wait_for(actor_ref.task)

    @coroutine
    def cancel_all(self):
        futures = list(self._other_tasks)
        while futures:
            task = futures.pop()
            task.cancel()
        while self._registry:
            name, cell = self._registry.popitem()
            futures.append(cell.task)
            cell.task.cancel()

        yield from asyncio.wait(futures)

    def exec(self, obj, *args):
        if iscoroutine(obj):
            future = self._loop.create_task(obj)
        elif iscoroutinefunction(obj):
            future = self._loop.create_task(obj(*args))
        elif isfunction(obj) or isbuiltin(obj):
            # TODO: ability to use executor defined in settings
            future = self.exec_in_executor(obj, None, *args)
        return future

    def exec_in_executor(self, non_coro_func, executor=None, *args):
        return self._loop.create_task(self._loop.run_in_executor(executor, non_coro_func, *args))

    def run_until_stop(self, coros, exit_after=False):
        try:
            try:
                _it = iter(coros)
            except TypeError:
                _it = iter([coros])
            for c in _it:
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