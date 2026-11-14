from collections import deque
import math
import logging
import threading


# تنظیم لاگر استاندارد
logger = logging.getLogger("DynamicPriorityQueue")
logger.addHandler(logging.NullHandler())  


class QueueEmptyEror(Exception):
    pass

class DynamicPriorityQueue:
    def __init__(self, max_capacities=None):
        self.capacities = max_capacities or {1: 400, 2: 350, 3: 300, 4: 200, 5: 150}
        self.queues = {i: deque() for i in range(1, 6)}
        self.processed_counters = {i: 0 for i in range(1, 6)}
        self.lock = threading.Lock()
        self.is_empty = False
        self.callback_func = None

    def enqueue(self, item, priority=5) -> bool:
        """
        Pushes an item into the queue. Demotes to lower priority on overflow.
        """
        run_func = False
        callback_func = None
        enqueued = False

        curr_prio = priority
        with self.lock:
            while curr_prio >= 1:
                if len(self.queues[curr_prio]) < self.capacities[curr_prio]:
                    self.queues[curr_prio].append(item)
                    enqueued = True
                    if self.is_empty:
                        run_func = True
                        callback_func = self.callback_func
                        self.is_empty = False
                    logger.debug(f"[ENQUEUE] Item placed in C{curr_prio} (Requested: C{priority})")
                    break
                else:
                    logger.warning(f"[OVERFLOW] C{curr_prio} is full. Demoting to C{curr_prio - 1}")
                    curr_prio -= 1
            if not enqueued:
                logger.error(f"[DROP] All tiers full. Dropped item: {item}")

        if run_func and callback_func is not None:
            callback_func()
        return enqueued

    def dequeue(self):
        """
        Pops the highest priority item according to dynamic scheduling.
        """
        
        active_prio = None
        
        with self.lock:
            for p in range(5, 0, -1):
                if len(self.queues[p]) > 0:
                    active_prio = p
                    break
            
            if active_prio is None:
                self.is_empty = True
                logger.warning(f"[EMPTY] The queue is empty")
                raise QueueEmptyEror("The queue is empty")

            # Calculate dynamic threshold
            q_len = len(self.queues[active_prio])
            threshold = max(1, math.ceil(q_len / 5))

            item = self.queues[active_prio].popleft()
            self.processed_counters[active_prio] += 1
            
            logger.debug(f"[DEQUEUE] Pop from C{active_prio} | Counter: {self.processed_counters[active_prio]}/{threshold}")

            # Promotion logic
            if self.processed_counters[active_prio] >= threshold:
                self.processed_counters[active_prio] = 0
                lower_prio = active_prio - 1
                if lower_prio >= 1 and len(self.queues[lower_prio]) > 0:
                    promoted_item = self.queues[lower_prio].popleft()
                    self.queues[active_prio].append(promoted_item)
                    logger.info(f"[PROMOTE] Promoted item from C{lower_prio} to C{active_prio}")

            return item

    def callback(self, func):
        """Register a callable other than the queue's enqueue/dequeue methods."""
        if not callable(func):
            raise TypeError("callback must be callable")
        callback_method = getattr(func, "__func__", func)
        if callback_method in (DynamicPriorityQueue.enqueue, DynamicPriorityQueue.dequeue):
            raise ValueError("enqueue and dequeue cannot be registered as callbacks")
        self.callback_func = func



    def __len__(self):
        return sum(len(q) for q in self.queues.values())
