from heap import *

class PriorityQueue:
    
    def __init__(self, elts, compare):
        self.array = [x for x in elts]
        i = 0
        self.index_of = {}
        for x in self.array:
            self.index_of[x] = i
            i += 1
        self.array_size = len(elts)
        self.compare = compare
        build_heap(self.array, self.array_size, self.index_of, self.compare)

    def push(self, x):
        self.array = self.array + [x]
        self.index_of[x] = self.array_size
        self.array_size += 1
        up_heap(self.array, self.index_of, self.compare)

    def pop(self):
        mx = self.array[0]
        last = self.array[self.array_size - 1]
        self.array[0] = last
        self.index_of[last] = 0
        self.array_size -= 1
        down_heap(self.array, self.array_size, self.index_of, 0, self.compare)
        return mx

    def update(self, x):
        if x in self.index_of:
            heap_update(self.array, self.array_size, self.index_of,
                        self.index_of[x], self.compare)

    def front(self):
        if self.array_size < 1:
            raise Exception('PriorityQueue.front: empty')
        return self.array[0]

    def empty(self):
        return self.array_size == 0
        
