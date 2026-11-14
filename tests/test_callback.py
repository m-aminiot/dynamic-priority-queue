"""Callback validation, wake-up contract, and threaded consumer checks."""

import threading
import time
import unittest

from dynamic_queue import DynamicPriorityQueue, QueueEmptyEror


class TestCallback(unittest.TestCase):
    def mark_empty(self, queue):
        with self.assertRaises(QueueEmptyEror):
            queue.dequeue()

    def test_none_payload_is_not_an_empty_queue(self):
        queue = DynamicPriorityQueue()
        queue.enqueue(None)
        queue.enqueue("next")
        self.assertIsNone(queue.dequeue())
        self.assertEqual(queue.dequeue(), "next")
        self.mark_empty(queue)

    def test_callback_once_per_wakeup(self):
        queue = DynamicPriorityQueue()
        calls = []
        queue.callback(lambda: calls.append("wake"))
        self.mark_empty(queue)
        queue.enqueue("first")
        queue.enqueue("second")
        self.assertEqual(calls, ["wake"])
        queue.dequeue()
        queue.dequeue()
        self.mark_empty(queue)
        queue.enqueue("third")
        self.assertEqual(calls, ["wake", "wake"])

    def test_full_queue_does_not_trigger_callback(self):
        queue = DynamicPriorityQueue({priority: 0 for priority in range(1, 6)})
        calls = []
        queue.callback(lambda: calls.append("wake"))
        self.mark_empty(queue)
        self.assertIs(queue.enqueue("data"), False)
        self.assertEqual(calls, [])
        self.assertTrue(queue.is_empty)

    def test_callback_wrapper_can_dequeue(self):
        queue = DynamicPriorityQueue()
        received = []
        queue.callback(lambda: received.append(queue.dequeue()))
        self.mark_empty(queue)
        worker = threading.Thread(target=lambda: queue.enqueue("data"), daemon=True)
        worker.start()
        worker.join(1)
        self.assertFalse(worker.is_alive(), "Callback deadlocked")
        self.assertEqual(received, ["data"])

    def test_callback_rejects_queue_methods(self):
        queue = DynamicPriorityQueue()
        other_queue = DynamicPriorityQueue()
        original = lambda: None
        queue.callback(original)
        for func in (queue.enqueue, queue.dequeue, other_queue.enqueue,
                     other_queue.dequeue, DynamicPriorityQueue.enqueue,
                     DynamicPriorityQueue.dequeue):
            with self.subTest(callback=func):
                with self.assertRaises(ValueError):
                    queue.callback(func)
                self.assertIs(queue.callback_func, original)

    def test_callback_rejects_non_callable(self):
        queue = DynamicPriorityQueue()
        for value in (None, 42, "callback"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    queue.callback(value)

    def test_callback_accepts_event_set(self):
        queue = DynamicPriorityQueue()
        event = threading.Event()
        queue.callback(event.set)
        self.mark_empty(queue)
        self.assertIs(queue.enqueue("data"), True)
        self.assertTrue(event.is_set())

    def test_callback_runs_outside_queue_lock(self):
        queue = DynamicPriorityQueue()
        lock_available = []

        def callback():
            acquired = queue.lock.acquire(blocking=False)
            lock_available.append(acquired)
            if acquired:
                queue.lock.release()

        queue.callback(callback)
        self.mark_empty(queue)
        queue.enqueue("data")
        self.assertEqual(lock_available, [True], "Callback still runs inside enqueue's lock")

    def test_enqueue_without_callback_returns_true(self):
        queue = DynamicPriorityQueue()
        self.mark_empty(queue)
        self.assertIs(queue.enqueue("data"), True)

    def test_threaded_producer_consumer_without_polling(self):
        queue = DynamicPriorityQueue()
        wake = threading.Event()
        stop = threading.Event()
        initially_idle = threading.Event()
        first_received = [threading.Event() for _ in range(3)]
        drained = [threading.Event() for _ in range(3)]
        received = []
        failures = []
        dequeue_calls = []
        queue.callback(wake.set)

        def consume():
            try:
                # Perform one initial drain, then wait exclusively for callbacks.
                while not stop.is_set():
                    wake.clear()  # Clear BEFORE draining to avoid losing a wake-up.
                    while not stop.is_set():
                        dequeue_calls.append(1)
                        try:
                            item = queue.dequeue()
                        except QueueEmptyEror:
                            if not received:
                                initially_idle.set()
                            for batch in range(3):
                                if len(received) == (batch + 1) * 40:
                                    drained[batch].set()
                            break
                        received.append(item)
                        if item[1] == 0:
                            first_received[item[0]].set()
                    wake.wait()  # No timer and no repeated dequeue while idle.
            except BaseException as error:
                failures.append(error)

        def produce():
            try:
                if not initially_idle.wait(2):
                    raise AssertionError("Consumer did not enter its initial wait")
                for batch in range(3):
                    before = len(dequeue_calls)
                    time.sleep(0.05)
                    if len(dequeue_calls) != before:
                        raise AssertionError("Consumer polled the empty queue")
                    queue.enqueue((batch, 0))
                    if not first_received[batch].wait(2):
                        raise AssertionError("Callback failed to wake the consumer")
                    for index in range(1, 40):
                        queue.enqueue((batch, index), priority=index % 5 + 1)
                    if not drained[batch].wait(2):
                        raise AssertionError("Consumer did not finish draining the batch")
            except BaseException as error:
                failures.append(error)

        consumer = threading.Thread(target=consume, daemon=True)
        producer = threading.Thread(target=produce, daemon=True)
        consumer.start()
        producer.start()
        try:
            producer.join(8)
            self.assertFalse(producer.is_alive(), "Producer timed out")
            self.assertEqual(failures, [])
            self.assertCountEqual(received, [(b, i) for b in range(3) for i in range(40)])
            self.assertEqual(len(queue), 0)
            self.assertTrue(all(event.is_set() for event in drained))
        finally:
            stop.set()
            wake.set()
            consumer.join(2)
        self.assertFalse(consumer.is_alive(), "Consumer failed to stop")


if __name__ == "__main__":
    unittest.main()
