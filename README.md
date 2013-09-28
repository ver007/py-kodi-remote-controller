py-xbmc-remote-controller
=========================

XBMC remote controller written in Python

Just a fun small project to explore JSON, TCP requests, and play with my favorite HTPC, XBMC.

Well, sometimes I feel bored to seek the TV remote or to launch [Yatse][4] on my phone when coding. With this Python script I can now control XBMC directly from a terminal. Life is good.

Note: a couple of methods are currently covered (see Contributions)

## Quick start

Clone this repo and from the folder, launch the script:

```
python pycontroller.py
```

Use the help command to have the list of available methods, and help + command to display a usage message.

## Contributions

Contributions are welcome and easy. Every methods of the API can be included, only a few are done today. The structure of the program makes this method by method implementation obvious.

In any doubt, I will be pleased to discuss with you.

## Useful links

+ XBMC wiki, ["JSON-RPC API"][1], some general explanations about the API
+ XBMC wiki, ["JSON-RPC API/Examples"][2], the full methods list and description
+ XBMC wiki, ["JSON-RPC API/Examples"][5], json-rpc examples
+ Python docs, ["18.2. json — JSON encoder and decoder"][3], using json in Python

[1]: http://wiki.xbmc.org/?title=JSON-RPC_API
[2]: http://wiki.xbmc.org/index.php?title=JSON-RPC_API/Examples
[3]: http://docs.python.org/2/library/json.html
[4]: http://yatse.leetzone.org/redmine
[5]: http://wiki.xbmc.org/index.php?title=JSON-RPC_API/Examples
