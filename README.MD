# Dynamic Priority Queue

[🇮🇷 راهنمای فارسی](README.FA.MD)

A small Python priority queue with five capacity-limited tiers, overflow demotion, and dynamic promotion between adjacent tiers. Built entirely with the Python standard library.

## Project files

| File | Purpose |
| --- | --- |
| `dynamic_queue.py` | The `DynamicPriorityQueue` implementation. |
| `example.py` | A runnable usage example, including 100 items with random priorities. |
| `tests/test_queue.py` | Unit tests for insertion, queue length, priority selection, empty queues, and overflow demotion. |

## Requirements

Python 3.6 or newer. No third-party packages are required. Run the commands below from the project directory.

## Quick start

```python
from dynamic_queue import DynamicPriorityQueue

queue = DynamicPriorityQueue()

queue.enqueue("Background task", priority=1)
queue.enqueue("Urgent task", priority=5)

print(len(queue))       # 2
print(queue.dequeue()) # Urgent task
print(queue.dequeue()) # Background task
queue.dequeue()        # raises QueueEmptyEror when the queue is empty
```

## How it works

Priority **5 is the highest** and **1 is the lowest**. Items within each tier are processed in FIFO order.

### Default capacities

| Priority | Maximum items |
| --- | --- |
| 5 | 150 |
| 4 | 200 |
| 3 | 300 |
| 2 | 350 |
| 1 | 400 |

### Enqueue and overflow

`enqueue(item, priority=5)` tries the requested tier first. If it is full, the method tries each lower tier in turn. It returns `True` when the item is stored, or `False` when the requested tier and all lower tiers are full. It does not try higher tiers.

### Dequeue and promotion

`dequeue()` removes the oldest item from the highest nonempty tier. If the queue is empty, it raises `QueueEmptyEror`.

Before each removal, it calculates a threshold using that tier's current length:

```python
threshold = max(1, math.ceil(queue_length / 5))
```

Each tier has its own removal counter. When the active tier's counter reaches the threshold, the counter resets. If the immediately lower tier contains an item, its oldest item moves to the back of the active tier. The threshold is recalculated on every dequeue; it is not a fixed batch size. Dequeue always selects the highest nonempty tier first. Promotion only moves an item up one tier, so a lower-priority item may wait indefinitely while higher-priority work continues; service fairness across all tiers is not guaranteed.

`len(queue)` returns the total number of stored items across all tiers.

## Custom capacities

Pass a dictionary containing all five priority levels:

```python
queue = DynamicPriorityQueue(
    max_capacities={1: 50, 2: 50, 3: 50, 4: 50, 5: 50}
)
```

Use integer priorities from 1 through 5 and nonnegative integer capacities. The implementation does not validate these inputs. An omitted or empty capacity dictionary uses the defaults.

## Run the example

`example.py` is the executable example:

```bash
python3 example.py
```

It demonstrates enqueueing and dequeueing, then adds and removes 100 items with random priorities using custom capacities. Status messages are printed inside the loops, once per operation; dequeued values are not printed.

## Run the tests

`tests/test_queue.py` contains four tests using Python's built-in `unittest` module. Run them from the project root:

```bash
python3 -m tests.test_queue
```

On Windows PowerShell:

```powershell
python -m tests.test_queue
```

The module name matches the test file's underscore naming, and the command works from the project root. A successful run reports `Ran 4 tests` and `OK`.

## Logging

Configure Python logging to see queue events:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
```

The `DynamicPriorityQueue` logger emits insertion and removal details at `DEBUG`, promotions at `INFO`, overflow at `WARNING`, and dropped items at `ERROR`. It includes a `NullHandler` and does not configure application logging itself.

## Usage notes

- Queue operations use a lock, so individual enqueue and dequeue calls are synchronized across threads.
- An empty `dequeue()` raises `QueueEmptyEror`; `None` can still be stored as an item and is returned as that payload.
- The bundled tests cover basic behavior; they do not cover every input or scheduling scenario.
