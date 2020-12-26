import time
import random
import needle

needle.LOGGER = 3


def myfunction(a, b):
    time.sleep(random.randint(1, 10))
    return a + b


for result in needle.GroupWorkers(target=myfunction, arguments=[(1, 2), (3, 4)], concurrent=2):
    print(result.arguments, result._return)
