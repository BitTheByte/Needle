import needle
import requests

needle.LOGGER = 3


hosts = [
    ("https://indeed.com",),
    ("https://google.com",),
    ("https://facebook.com",),
    ("https://yahoo.com",)
]


for i in needle.GroupWorkers(target=requests.get, arguments=hosts, concurrent=2):
    print(i.arguments, i._return )