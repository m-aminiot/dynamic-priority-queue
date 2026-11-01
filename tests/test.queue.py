from dynamic_queue import DynamicPriorityQueue
import unittest


class TestPriorityQueue(unittest.TestCase):

    def setUp(self):
        self.pq = DynamicPriorityQueue()

    def test_enqueue_and_len(self):
        self.pq.enqueue("Data 1", priority=5)
        self.pq.enqueue("Data 2", priority=4)
        self.pq.enqueue("Data 2", priority=3)
        self.pq.enqueue("Data 2", priority=2)
        self.pq.enqueue("Data 2", priority=1)
        self.pq.enqueue("Data 2", priority=5)


        
        self.assertEqual(len(self.pq), 6)

    def test_dequeue_priority(self):
        
        self.pq.enqueue("no important", priority=1)
        self.pq.enqueue("important", priority=5)

  
        item = self.pq.dequeue()
        self.assertEqual(item, "important")

    def test_empty_dequeue(self):

        result = self.pq.dequeue()
        self.assertIsNone(result)

    def test_overflow_demotion_from_c5_to_c4(self):
  
        for i in range(1, 151):
            self.pq.enqueue(f"C5_Item_{i}", priority=5)

        self.assertEqual(len(self.pq.queues[5]), 150)
        self.assertEqual(len(self.pq.queues[4]), 0)

 
        overflow_packet = "C5_Item_151_OVERFLOW"
        self.pq.enqueue(overflow_packet, priority=5)


        self.assertEqual(len(self.pq.queues[5]), 150)
        self.assertEqual(len(self.pq.queues[4]), 1)


        item_in_c4 = self.pq.queues[4][0]
        self.assertEqual(item_in_c4, overflow_packet)



if __name__ == "__main__":
    unittest.main()
