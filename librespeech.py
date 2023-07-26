#!/usr/bin/python3

"""
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE
FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import miniirc, sys
import time
from miniirc import *
from miniirc_extras import *

expire = [0]
assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

# Variables
nick = "lbsp"
haxxorname = "qeeg"
badwords = ["balls", "cunt", "wordington", "kill yourself"]
ident = nick
realname = "Censorship"
identity = None
# identity = '<username> <password>'
identity = open("ident").read().strip()
debug = True
channels = ["#librespeech"]
owner = ["Lareina", "f_", "leah", "Noisytoot", "Cindy", "ggoes"]
defcon = [0]

raiding = [False]

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

topic = ["Librespeech | bot testing"]

def trans(s):
    if s == "+": return "-"
    if s == "-": return "+"
    return s
@irc.Handler("KICK", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    text = args[-1]
    t = text.lower()
    if args[1] != irc.current_nick:
        return
    irc.msg(
            "ChanServ",
            "UNBAN",
            channel
    )
    irc.send("JOIN", channel)
    if not defcon[0]: return
    if hostmask[0] != haxxorname:
        return
    irc.msg("ChanServ", "DEOP", channel, haxxorname)
    irc.send("KICK", channel, haxxorname, "retaliation")
@irc.Handler("JOIN", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    if hostmask[0] == irc.current_nick:
        if defcon[0]: irc.msg("ChanServ", "DEOP", channel, haxxorname)
        irc.msg("ChanServ", "OP", channel)
    elif not defcon[0]: return
    elif hostmask[0] == haxxorname:
        if defcon[0] == 1:
            irc.notice(haxxorname, f"[{channel}] You are not allowed to op up, change the topic, set modes, or do any similar thing in this channel.")
        if defcon[0] == 3:
            irc.send("MODE", channel, "+q", "$a:%s" % haxxorname)
        if defcon[0] >= 4:
            irc.send("MODE", channel, "+b", "$a:%s" % haxxorname)
            irc.send("KICK", channel, haxxorname, "You're banned!")
    else:
        irc.notice(hostmask[0], f"[{channel}] Welcome to the channel! Please keep an eye on {haxxorname} to make sure they don't do anything evil.")
@irc.Handler("PRIVMSG", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    if hostmask[0] == "LitBot" and "・゜゜・。。・゜゜\_o< QUACK!" == args[-1].strip():
        irc.msg(channel, "LitBot: bef")
        return
    elif hostmask[0] == haxxorname and defcon[0] == 2:
        text = args[-1].lower().strip()
        for each in badwords:
            if ' ' + each + ' ' in text or text.startswith(each + " ") or text.endswith(" " + each) or text == each:
                irc.send("MODE", channel, "+q", "$a:%s" % haxxorname)
                time.sleep(60)
                irc.send("MODE", channel, "-q", "$a:%s" % haxxorname)
                return
    if hostmask[0] in owner and args[-1] == f"{irc.current_nick}: quit":
        exit(0)
    elif hostmask[0] in owner and args[-1] == f"{irc.current_nick}: off":
        defcon[0] = 0
        irc.send("MODE", channel, "-bq", "$a:%s" % haxxorname, "$a:%s" % haxxorname)
        irc.msg(channel, f"{hostmask[0]}: defcon 0 set: relax")
    elif hostmask[0] in owner and args[-1] == f"{irc.current_nick}: noop":
        defcon[0] = 1
        irc.send("MODE", channel, "-bq", "$a:%s" % haxxorname, "$a:%s" % haxxorname)
        irc.msg(channel, f"{hostmask[0]}: defcon 1 set: deny channel operator privileges")
    elif hostmask[0] in owner and args[-1] == f"{irc.current_nick}: censor":
        defcon[0] = 2
        irc.send("MODE", channel, "-bq", "$a:%s" % haxxorname, "$a:%s" % haxxorname)
        irc.msg(channel, f"{hostmask[0]}: defcon 2 set: temporary quiet on badwords")
    elif hostmask[0] in owner and args[-1] == f"{irc.current_nick}: quiet":
        defcon[0] = 3
        irc.send("MODE", channel, "-b+q", "$a:%s" % haxxorname, "$a:%s" % haxxorname)
        irc.msg(channel, f"{hostmask[0]}: defcon 3 set: quiet")
    elif hostmask[0] in owner and args[-1] == f"{irc.current_nick}: ban":
        defcon[0] = 4
        irc.send("MODE", channel, "+bq", "$a:%s" % haxxorname, "$a:%s" % haxxorname)
        irc.msg(channel, f"{hostmask[0]}: defcon 4 set: automatic kickban")
    elif hostmask[0] in owner and args[-1].startswith(f"{irc.current_nick}:"):
        irc.msg(channel, f"{hostmask[0]}: usage: {irc.current_nick} (off | noop | censor | quiet | ban)")
    elif args[-1].startswith(f"{irc.current_nick}:") and hostmask[0] == haxxorname:
        irc.msg(channel, f"{hostmask[0]}: lmao u serious?")
    elif args[-1].startswith(f"{irc.current_nick}:"):
        irc.msg(channel, f"{hostmask[0]}: unauthorized")


@irc.Handler("MODE", colon=False)
def yay(irc, hostmask, args):
    if not defcon[0]: return
    channel = args[0]
    if args[1] == "-o" and args[2] == irc.current_nick:
        irc.msg("ChanServ", "OP", channel)
    if args[1] == "+o" and args[2] == haxxorname:
        irc.msg("ChanServ", "DEOP", channel, haxxorname)
    if hostmask[0] != haxxorname:
        return
    irc.msg("ChanServ", "OP", channel)
    irc.msg("ChanServ", "DEOP", channel, haxxorname)
    irc.send("MODE", channel, ''.join([trans(s) for s in args[1]]), *(args[2:]))
@irc.Handler("TOPIC", colon=False)
def yay(irc, hostmask, args):
    if not defcon[0]: return
    channel = args[0]
    text = args[-1]
    t = text.lower()
    if hostmask[0] != haxxorname:
        topic[0] = text
        return
    irc.msg("ChanServ", "DEOP", channel, haxxorname)
    irc.send(
            "TOPIC",
            channel,
            topic[0]
    )
@irc.Handler("474", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    if defcon[0]:
        irc.msg("ChanServ", "DEOP", channel, haxxorname)
    irc.msg(
            "ChanServ",
            "UNBAN",
            channel
    )
    irc.send("JOIN", channel)


if __name__ == "__main__":
    irc.require("users")
    irc.require("chans")
    irc.connect()
