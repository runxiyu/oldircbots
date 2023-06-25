#!/usr/bin/python3

"""
No tourettes triggering allowed.

The original base of this program is available at
https://github.com/luk3yx/stdinbot, under the Expat license.  However,
more than 95% has been written differently.  All changes are under
the following waiver:

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

import miniirc, sys
import time
from miniirc import *
from miniirc_extras import *

assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

# Variables
nick = "tourettes"
ident = nick
realname = "just a bot for qeeg"
identity = None
# identity = '<username> <password>'
debug = True
channels = ["#librespeech", "#libreqeeg"]
owner = "Andrew/AndrewYu <andrew@andrewyu.org>"

raiding = [False]

why = {}
for c in channels:
    why[c] = owner

ip = "irc.libera.chat"
port = 6697

# Welcome!
print("Welcome to {}!".format(nick), file=sys.stderr)
irc = IRC(
    ip,
    port,
    nick,
    channels,
    ident=ident,
    realname=realname,
    ns_identity=identity,
    debug=debug,
    auto_connect=False,
)



@irc.Handler("PRIVMSG", colon=False)
def handle_privmsg(irc, hostmask, args):
    channel = args[0]
    if channel.startswith("#"):
        ops = irc.chans[channel].modes.getset("o")
        c = True

    text = args[-1]
    words = args[-1].split(" ")
    t = text.lower()
    w = [x.lower() for x in words]
    print(channel, hostmask, text, words, t, w)
    bad = "\x68\x6D\x6D"
    if (t.startswith(bad) or " " + bad in t):
        print(f"trying to kick {hostmask[0]} from {channel}")
        irc.msg(
            hostmask[0],
            f"[{channel}] Do not use this word (\"hmm\").  A user in this channel has Tourette Syndrome.",
        )
if __name__ == "__main__":
    irc.require("users")
    irc.require("chans")
    irc.connect()
