from collections import deque
import threading

class ThreadSafeQueue:
    def __init__(self, max_size=1000):
        self.queue = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def put(self, item):
        with self.lock:
            self.queue.append(item)

    def get(self):
        with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None

    def is_empty(self):
        with self.lock:
            return len(self.queue) == 0

    def size(self):
        with self.lock:
            return len(self.queue)