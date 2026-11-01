from dynamic_queue import DynamicPriorityQueue
from random import randint
import logging



queue = DynamicPriorityQueue()
# if you want to custom max capacities return this dict into function => {1: 400, 2: 350, 3: 300, 4: 200, 5: 150}

#add data in queue 
queue.enqueue(item="data1", priority=2 )# priority should be between 1 , 5

#read data from queue
queue.dequeue()


#example
queue_example = DynamicPriorityQueue({1: 50, 2: 50, 3: 50, 4: 50, 5: 50})

for i in range(100):
    queue_example.enqueue(item=f"data {i}", priority=randint(1,5))
    print("All data added!")

for i in range(100):
    queue_example.dequeue()
    print("All data recieved!")

# you can also use logging library
# like this => logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s",)
