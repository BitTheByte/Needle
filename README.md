# Needle
<p align="center">
    <a href="https://twitter.com/BitTheByte">
      <img src="https://i.ibb.co/fHY6xPc/Untitled-1.png" width="500">
    </a>
</p>

# Why?
Implementing threading certainly is a headache when it comes to small projects. this library aims to minimize the time wasted implementing threading using predefined techniques that suites most of the common cases allowing software developers to focus on what is important
# Installation 

To install the latest github release 
```
$ git clone https://github.com/BitTheByte/Needle
$ cd Needle
$ python setup.py install
```

Using pip
```
$ pip install needlepy
```

# Examples 
```python
import needle
import requests

needle.LOGGER = 3 # 0 = DISABLE LOGGING, 1 = ERROR, 2 = WARNING, 3 = INFO 

hosts = [
    ("https://indeed.com",),
    ("https://google.com",),
    ("https://facebook.com",),
    ("https://yahoo.com",)
]

for i in needle.GroupWorkers(target=requests.get, arguments=hosts, concurrent=2):
    print(i.arguments, i._return )
```
Needle supports muliple threading techniques other than shown at the example for more examples and techniques see [/examples](examples)

# Issues
if you have a suggestion or encountered any errors please open a new issue under https://github.com/bitthebyte/needle/issues