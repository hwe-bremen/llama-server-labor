"""Private reproductions, never sent to the model. Assertions document observed behavior."""
import asyncio
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class WaitingClient:
    def __init__(self):
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def generate(self, prompt):
        self.started.set()
        await self.release.wait()
        return 'answer'


class Cases(unittest.IsolatedAsyncioTestCase):
    async def test_case01_tenant_leak_reproduced(self):
        from model_cases.case01.api import Identity, context_for
        from model_cases.case01.index import DocumentIndex
        from model_cases.case01.retrieval import Retriever
        retriever = Retriever(DocumentIndex({('A', 'frage'): ('A-private',),
                                              ('B', 'frage'): ('B-private',)}))
        self.assertEqual(await context_for(Identity('A'), 'Frage', retriever), ('A-private',))
        # Reproduction asserts the observed violation, not desired contract behavior.
        self.assertEqual(await context_for(Identity('B'), ' frage ', retriever), ('A-private',))

    async def test_case02_cancellation_leaks_slot_reproduced(self):
        from model_cases.case02.provider import LimitedProvider
        client = WaitingClient(); provider = LimitedProvider(client)
        task = asyncio.create_task(provider.complete('x'))
        await asyncio.wait_for(client.started.wait(), 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(provider._slots.locked())

    async def test_case03_invalidation_lost_reproduced(self):
        from model_cases.case03.memory import MemoryView
        class Store:
            value = 'old'
            def __init__(self):
                self.started = asyncio.Event(); self.release = asyncio.Event()
            async def load(self, key):
                snapshot = self.value
                self.started.set(); await self.release.wait()
                return snapshot
        store = Store(); view = MemoryView(store)
        task = asyncio.create_task(view.get('session'))
        await asyncio.wait_for(store.started.wait(), 1)
        store.value = 'new'; await view.invalidate('session'); store.release.set()
        self.assertEqual(await task, 'old')  # explicitly permitted inflight snapshot
        self.assertEqual(await view.get('session'), 'old')  # forbidden persistent stale cache
        self.assertEqual(store.value, 'new')

    async def test_case04_cross_session_writer_block_reproduced(self):
        from model_cases.case04.chat import ChatJournal
        with tempfile.TemporaryDirectory() as directory:
            client = WaitingClient(); journal = ChatJournal(str(Path(directory)/'turns.sqlite'), client)
            first = asyncio.create_task(journal.chat('session-A', 'first'))
            await asyncio.wait_for(client.started.wait(), 1)
            try:
                with self.assertRaisesRegex(sqlite3.OperationalError, 'locked'):
                    await journal.chat('session-B', 'second')
            finally:
                client.release.set(); await asyncio.wait_for(first, 1)

    async def test_case05_cancel_and_error_release_slot(self):
        from model_cases.case05.provider import LimitedProvider
        client = WaitingClient(); provider = LimitedProvider(client)
        task = asyncio.create_task(provider.complete('x'))
        await asyncio.wait_for(client.started.wait(), 1); task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(provider._slots.locked())
        client.release.set()
        self.assertEqual(await asyncio.wait_for(provider.complete('next'), 1), 'answer')
        class BrokenClient:
            async def generate(self, prompt):
                raise RuntimeError('provider offline')
        provider = LimitedProvider(BrokenClient())
        with self.assertRaises(RuntimeError):
            await provider.complete('x')
        self.assertFalse(provider._slots.locked())

    async def test_case06_tenant_epoch_and_capacity_hold(self):
        from model_cases.case06.cache import ContextCache
        class Repository:
            def __init__(self):
                self.value = 'old'; self.pause = True
                self.started = asyncio.Event(); self.release = asyncio.Event()
            async def search(self, tenant, query):
                snapshot = (tenant + ':' + self.value,)
                if self.pause:
                    self.pause = False; self.started.set(); await self.release.wait()
                return snapshot
        repository = Repository(); cache = ContextCache(repository, {'A','B'}, capacity=2)
        task = asyncio.create_task(cache.get('A','question'))
        await asyncio.wait_for(repository.started.wait(), 1)
        repository.value = 'new'; await cache.invalidate('A'); repository.release.set()
        self.assertEqual(await task, ('A:old',))  # allowed inflight response
        self.assertEqual(await cache.get('A','question'), ('A:new',))
        self.assertEqual(await cache.get('B','question'), ('B:new',))
        await cache.get('A','another')
        self.assertEqual(len(cache._values), 2)
        self.assertEqual(list(cache._values), [('B','question'), ('A','another')])


if __name__ == '__main__':
    unittest.main(verbosity=2)
