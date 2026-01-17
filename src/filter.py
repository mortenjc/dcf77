
class SampleFilter:
    def __init__(self, average=10):
        self.n = average
        self.data = [0 for x in range(average)]
        self.samples = 0


    def add(self, value):
        self.data[self.samples % self.n] = value
        self.samples += 1
        if self.samples < self.n:
            return
        return sum(self.data) // self.n