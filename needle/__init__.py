from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from types import FunctionType, MethodType
from colorama import Fore, init

import concurrent.futures as confutures
import threading
import time

init(autoreset=True)
LOGGER   = 1
ERROR    = 1
WARNING  = 2
INFO     = 3

printlock = threading.Lock()

def log(tag, msg):
    with printlock:
        if tag == ERROR and LOGGER >= ERROR:
            print(f'[{Fore.RED}ERROR{Fore.RESET}]: {msg}\n', end='')
        elif tag == WARNING and LOGGER >= WARNING:
            print(f'[{Fore.YELLOW}WARNING{Fore.RESET}]: {msg}\n', end='')
        elif tag == INFO and LOGGER >= INFO:
            print(f'[{Fore.LIGHTBLACK_EX}INFO{Fore.RESET}]: {msg}\n', end='')

class Channel:
    def __init__(self, name='default'):
        self.name = name
        self.stop = False
        self.threads = []
        self.items = []
        self.jobs = 0
        self.__lock = threading.Lock()

    def append(self, *items):
        with self.__lock:
            self.jobs += 1
        self.items.append(items)
        log(INFO, f'Channel<{self.name}-{hex(id(self)).upper()}> appended with {items}')

    def pop(self):
        try:
            return True, self.items.pop(0)
        except IndexError:
            return False, None

    def isopen(self):
        return not self.stop

    def wait_and_close(self):
        self.wait()
        self.close()

    def wait(self):
        log(INFO, f'Channel<{self.name}-{hex(id(self)).upper()}> is waiting for threads to done')
        while self.jobs > 0:
            time.sleep(0.2)

    def close(self):
        self.stop = True
        log(INFO, f'Channel<{self.name}-{hex(id(self)).upper()}> is closed')


class ThreadResult:
    def __init__(self, function=None, arguments=None, channel=None, worker_id=None, function_return=None):
        self.function   = function
        self.arguments  = arguments
        self.channel    = channel
        self.worker_id  = worker_id
        self._return    = function_return
        self.exception  = None


def bootstrap_task(target, arguments, worker_id=None, channel=None):
    result = ThreadResult()
    result.function  = target
    result.arguments = arguments
    result.channel   = channel
    result.worker_id = worker_id
    
    try:
        result._return   = target(*arguments)
    except Exception as e:
        result.exception = e
        result._return = "RUNTIME_ERROR"

    return result


def GroupWorkers(target: FunctionType, arguments: list, concurrent: int, kernel=None):
    """
    Used to start a number concurrent threads of a target function and predefined arguments list
    :param target: function or method pointer
    :param arguments: list of predefined sorted tuples that will be passed to the target function/method
    :param concurrent: number of concurrent threads running at any given time
    :param kernel: parallelism/concurrency technique {ThreadPoolExecutor, ProcessPoolExecutor, NeedlePY}

    Example:
        >>> import time
        >>> import random
        >>> import needle
        >>>
        >>> def myfunction(a, b):
        >>>     time.sleep(random.randint(1,10))
        >>>     return a + b
        >>>
        >>> for result in needle.GroupWorkers(target=myfunction, arguments=[(1,2), (3,4)], concurrent=2 ):
        >>>     print(result.arguments, result._return)
    """

    if 'poolexecutor' in kernel.lower():
        futures  = []
        
        if 'thread' in kernel.lower():
            executor = ThreadPoolExecutor(max_workers=concurrent)
            log(INFO, "using python ThreadPoolExecutor API")

        elif 'process' in kernel.lower():
            executor = ProcessPoolExecutor(max_workers=concurrent)
            log(INFO, "using python ProcessPoolExecutor API")
        
        else:
            raise Exception(f"Unknown PoolExecutor sub-kernel :: {kernel}")

        for task_arguments in arguments:
            task_arguments = tuple(task_arguments)
            future = executor.submit(bootstrap_task, target, task_arguments)
            futures.append(future)
        
        for result in confutures.as_completed(futures):
            result = result.result()
            
            if result.exception != None:
                log(ERROR, result.exception)

            yield result

        executor.shutdown()
        return


    log(INFO, "using needlepy API")
        
    results = []

    def _callback(ret):
        results.append(ret)

    channel = Channel()
    for arg in arguments:
        channel.append(*arg)

    ChannelWorkers(target=target, channel=channel, concurrent=concurrent, callback=_callback, autoclose=False,
                   blocking=False)

    while 1:
        for _ in range(len(results)):
            yield results.pop()

        if channel.jobs == 0:
            break
        time.sleep(0.2)
    channel.close()


def ChannelWorkers(target: FunctionType, channel: Channel, concurrent: int = 5, callback=None,
                   blocking: bool = False, autoclose: bool = False):
    """
    Used to start a group of concurrent workers receiving sorted arguments from a specific channel.
    workers will not exit unless the channel request so by calling ``channel.close()`` or setting autoclose=true
    :param target:  function or method pointer
    :param channel: instance of Channel class
    :param concurrent: number of concurrent threads running at any given time
    :param callback: function to call when thread finishes 'callback(result)'
    :param blocking: set true to block execution
    :param autoclose: set to true to auto close the channel when it's empty
    Example:
        >>> import time
        >>> import random
        >>> import needle
        >>>
        >>> def mycallback(result):
        >>>     print("%i + %i = %i" % (result.arguments[0], result.arguments[1], result._return))
        >>>
        >>> def myfunction(a, b):
        >>>     time.sleep(random.randint(1,10))
        >>>     return a + b
        >>>
        >>> mychannel = needle.Channel('mychannel_name')
        >>> needle.ChannelWorkers(target=myfunction, channel=mychannel,callback=mycallback, concurrent=2, blocking=False, autoclose=False)
        >>>
        >>> for i in range(10):
        >>>     mychannel.append(i, 10) # a, b
        >>>
        >>> mychannel.wait() # wait for all threads to complete
        >>>
        >>> for i in range(10):
        >>>     mychannel.append(i, 20) # a, b
        >>>
        >>> mychannel.wait_and_close() # wait for all threads to complete and close the channel
    """

    for worker_id in range(1, concurrent + 1):
        thread = threading.Thread(target=__worker, name=channel.name,
                                  args=(worker_id, target, channel, threading.Lock(), callback,))
        channel.threads.append(thread)
        thread.start()

    if blocking:
        channel.wait()

    if autoclose:
        channel.close()


def __worker(wid, target, channel, lock, callback=None):
    log(INFO, f'Worker<{wid}> is running on target=<{target.__name__}> channel={channel.name} callback={callback}')
    while channel.isopen():
        ok, args = channel.pop()

        if not ok:
            time.sleep(0.2)
            continue

        log(INFO, f'Worker<{wid}> started <{target.__name__}> with arguments {args}')
        result = bootstrap_task(target=target, arguments=args, channel=channel, worker_id=wid)

        if result.exception != None:
            log(ERROR, result.exception)
        
        log(INFO, f'Worker<{wid}> finished {target.__name__}{args} -> {result._return}')

        if  isinstance(callback, FunctionType) or  isinstance(callback, MethodType):
            callback(result)

        with lock:
            channel.jobs -= 1

    log(INFO, f'Worker<{wid}> exited')