from collections import deque
import math
import logging

# تنظیم لاگر استاندارد
logger = logging.getLogger("DynamicPriorityQueue")
logger.addHandler(logging.NullHandler())  




class DynamicPriorityQueue:
    def __init__(self, max_capacities=None):
        self.capacities = max_capacities or {1: 400, 2: 350, 3: 300, 4: 200, 5: 150}
        self.queues = {i: deque() for i in range(1, 6)}
        self.processed_counters = {i: 0 for i in range(1, 6)}

    def enqueue(self, item, priority=5) -> bool:
        """
        Pushes an item into the queue. Demotes to lower priority on overflow.
        """
        curr_prio = priority
        while curr_prio >= 1:
            if len(self.queues[curr_prio]) < self.capacities[curr_prio]:
                self.queues[curr_prio].append(item)
                logger.debug(f"[ENQUEUE] Item placed in C{curr_prio} (Requested: C{priority})")
                return True
            else:
                logger.warning(f"[OVERFLOW] C{curr_prio} is full. Demoting to C{curr_prio - 1}")
                curr_prio -= 1
        
        logger.error(f"[DROP] All tiers full. Dropped item: {item}")
        return False

    def dequeue(self):
        """
        Pops the highest priority item according to dynamic scheduling.
        """
        active_prio = None
        for p in range(5, 0, -1):
            if len(self.queues[p]) > 0:
                active_prio = p
                break
        
        if active_prio is None:
            return None

        # Calculate dynamic threshold
        q_len = len(self.queues[active_prio])
        threshold = max(1, math.ceil(q_len / 3))

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


    def __len__(self):
        return sum(len(q) for q in self.queues.values())
