import time
import random
import needle

needle.LOGGER = 3


def mycallback(result):
    print("%i + %i = %i" % (result.arguments[0], result.arguments[1], result._return))


def myfunction(a, b):
    time.sleep(random.randint(1, 10))
    return a + b


mychannel = needle.Channel('mychannel_name')
needle.ChannelWorkers(target=myfunction, channel=mychannel, callback=mycallback, concurrent=2, blocking=False,
                      autoclose=False)
for i in range(10):
    mychannel.append(i, 10)  # a, b
mychannel.wait()  # wait for all threads to complete
for i in range(10):
    mychannel.append(i, 20)  # a, b
mychannel.wait_and_close()  # wait for all threads to complete and close the channel
