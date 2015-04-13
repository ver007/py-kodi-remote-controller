py-kodi-remote-controller
=========================

Kodi remote controller written in Python

Just a fun small project to explore JSON, TCP requests, and play with my favorite HTPC, Kodi.

Well, sometimes I feel bored to seek the TV remote or to launch [Yatse][yatse] on my phone when coding. With this Python script I can now control the audio player of Kodi directly from a terminal. Life is good.

## Quick start

First step, clone this repository localy. Kodi needs to be configured to accept remote controls. This is done differently based on the transport that you want to use.

### HTTP

This type of transport is the default value. Have a look at the official [documentation][http] to activate the HTTP server on your Kodi server. Here is how to launch the script:

```
$ python pykodi.py 192.168.1.251 -p 8080 -u web_user -pw web_password
```

### TCP

Here is the link to the [official documentation][tcp]. Launch the script with the IP of your Kodi server as a parameter and the ``--tcp`` switch:

```
$ python pykodi.py 192.168.1.251 --tcp
```

### First launch

On the first launch, the program will **sync the Kodi audio library** to local files. This may take some times, but will make further requests in the library very very fast.

If everything runs well, you will now see a prompt with the name of your Kodi server.

From the prompt, use the ``help`` command to have the list of available methods, and help + command to display a usage message. Most of the time, parameters are optional and a random value is used. To play a random album, try:

```
(Kodi (OpenELEC)) play_album
```

## Usage

### Start arguments

The program uses the ``argparse`` module, so all arguments can be displayed using the ``-h`` option. The verbosity has two levels, try ``-v`` or ``-vv``. The default port for TCP calls is used. If you changed it to something else, try ``-p``.

### User interface

Everything is managed using command line with the ``cmd`` module. This module is really powerful and provides a lot of features to make your user life easier, like auto-completion or online usage. Read the [official documentation][cmd-docs] to learn more. 

This [tutorial][cmd-tutorial] is also of a very good value.

### Let's play something

The full list of methods are displayed with the ``help`` command from the prompt. The first part of name of the methods are meaningful:

+ ``albums_`` various request in the albums library to find something to listen to
+ ``play_`` start or stop the player
+ ``playlist_`` manage your audio playlist

### Local library update

This will be developed in a next version. Just delete the pickle files and start again the program.

## Contributions

Contributions are welcome and easy.

The code is far from stable, if you face any trouble, post an issue in the GitHub tracking tool. New features can be requested in the bug tracker either. If you want to provide new features by yourself, submit a pull request.

The program can be started in a highly verbose mode with the ``-vv`` argument. All API commands and returns will then be displayed. Use the methods ``call_api`` and ``display_result`` for wrapping new command.

## Useful links

+ Kodi wiki, ["JSON-RPC API"][api-gen], some general explanations about the API
+ Kodi wiki, ["JSON-RPC API/v6"][api-v6], the full methods list and description
+ Kodi wiki, ["JSON-RPC API/Examples"][api-example], json-rpc examples
+ Python docs, ["18.2. json — JSON encoder and decoder"][python-json], using json in Python

[yatse]: http://yatse.leetzone.org/redmine
[http]: http://kodi.wiki/?title=JSON-RPC_API#HTTP
[tcp]: http://kodi.wiki/?title=JSON-RPC_API#TCP
[api-gen]: http://kodi.wiki/?title=JSON-RPC_API
[api-v6]: http://kodi.wiki/index.php?title=JSON-RPC_API/v6
[api-example]: http://kodi.wiki.org/index.php?title=JSON-RPC_API/Examples
[python-json]: http://docs.python.org/2/library/json.html
[cmd-docs]: https://docs.python.org/2/library/cmd.html
[cmd-tuto]: http://pymotw.com/2/cmd/
