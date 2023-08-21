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

import sys
print("warning: this is a joke. there are many vulnerabilities (account name != nickname, self-deop, etc).", file=sys.stderr)

import miniirc
import time
from miniirc import *
from miniirc_extras import *

expire = [0]
assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

# Variables
nick = "lbsp"
haxxorname = ["f_"]
ident = nick
realname = "Censorship"
identity = None
# identity = '<username> <password>'
identity = open("ident").read().strip()
debug = True
channels = ["#librespeech", "##adeban"]
owner = ["Adeline", "Noisytoot"]
defcon = [1]

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
def badword(action, badword):
    msg = "failed to add/remove"
    with open("bw.txt", mode='r+t') as bwfile:
        if action == 1 and badword not in bwfile.read(): # add
            print(badword, file=bwfile)
            msg = "successfully added"
        elif action == 0: # del
            lines = bwfile.readlines()
            bwfile.seek(0)
            for line in lines:
                if badword != line.strip("\n"):
                    bwfile.write(line)
            bwfile.truncate()
            msg = "successfully removed"
    bwfile.close() # needed?
    return msg + " badword \"" + badword + "\""

@irc.Handler("KICK", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    text = args[-1]
    t = text.lower()
    if args[1] != irc.current_nick:
        return
    irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    irc.msg(
            "ChanServ",
            "UNBAN",
            channel
    )
    irc.send("JOIN", channel)
    time.sleep(1)
    irc.send("JOIN", channel)
    if not defcon[0]: return
    if hostmask[0] != haxxorname[0]:
        return
    irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    irc.send("KICK", channel, haxxorname[0], "retaliation")
    irc.send("JOIN", channel)
@irc.Handler("JOIN", colon=False)
def yay(irc, hostmask, args):
    channel = args[0]
    if hostmask[0] == irc.current_nick:
        if defcon[0]: irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
        irc.msg("ChanServ", "OP", channel)
    elif not defcon[0]: return
    elif hostmask[0] == haxxorname[0]:
        if defcon[0] == 1:
            irc.notice(haxxorname[0], f"[{channel}] You are not allowed to op up, change the topic, set modes, or do any similar thing in this channel.")
        if defcon[0] == 3:
            irc.send("MODE", channel, "+qq", "$a:%s" % haxxorname[0], "$j:##adeban")
            irc.send("MODE", "##adeban", "+b", "$a:%s" % haxxorname[0])
        if defcon[0] >= 4:
            irc.send("MODE", channel, "+bb", "$a:%s" % haxxorname[0], "$j:##adeban")
            irc.send("MODE", "##adeban", "+b", "$a:%s" % haxxorname[0])
            irc.send("KICK", channel, haxxorname[0], "You're banned!")
    else:
        irc.notice(hostmask[0], f"[{channel}] Welcome to the channel! Please keep an eye on {haxxorname[0]} to make sure they don't do anything evil.")
@irc.Handler("PRIVMSG", colon=False)
def yay(irc, hostmask, args):
    badwords = open("bw.txt").read().strip().split("\n")
    channel = args[0]
    if hostmask[0] == haxxorname and defcon[0] == 2:
        text = args[-1].lower().strip()
        for each in badwords.lower():
            if each in text or ' ' + each + ' ' in text or text.startswith(each + " ") or text.endswith(" " + each) or text == each:
                irc.send("MODE", channel, "+q", "$a:%s" % haxxorname[0])
                time.sleep(60)
                irc.send("MODE", channel, "-q", "$a:%s" % haxxorname[0])
                return
    elif args[-1].startswith(f"{irc.current_nick}:") and hostmask[0] == haxxorname[0]:
        irc.msg(channel, f"{hostmask[0]}: no")
    elif hostmask[0] in owner and args[-1].startswith(f"{irc.current_nick}: "):
        lat = args[-1].split(" ")[1:]
        if lat[0] == f"quit":
            exit(0)
        elif lat[0] == f"target":
            if lat[1] == irc.current_nick:
                irc.msg(channel, f"{hostmask[0]}: no")
                return
            haxxorname[0] = lat[1]
            irc.msg(channel, f"{hostmask[0]}: set target to {haxxorname[0]}")
        elif lat[0] == f"off":
            defcon[0] = 0
            irc.send("MODE", channel, "-bq", "$a:%s" % haxxorname[0], "$a:%s" % haxxorname[0])
            irc.msg(channel, f"{hostmask[0]}: defcon 0 set: relax")
        elif lat[0] == f"noop":
            defcon[0] = 1
            irc.send("MODE", channel, "-bqo", "$a:%s" % haxxorname[0], "$a:%s" % haxxorname[0], haxxorname[0])
            irc.msg(channel, f"{hostmask[0]}: defcon 1 set: deny channel operator privileges")
        elif lat[0] == f"censor":
            defcon[0] = 2
            irc.send("MODE", channel, "-bq", "$a:%s" % haxxorname[0], "$a:%s" % haxxorname[0])
            irc.msg(channel, f"{hostmask[0]}: defcon 2 set: temporary quiet on badwords")
        elif lat[0] == f"quiet":
            defcon[0] = 3
            irc.send("MODE", channel, "-b+q", "$a:%s" % haxxorname[0], "$a:%s" % haxxorname[0])
            irc.msg(channel, f"{hostmask[0]}: defcon 3 set: quiet")
        elif lat[0] == f"ban":
            defcon[0] = 4
            irc.send("MODE", channel, "+bq", "$a:%s" % haxxorname[0], "$a:%s" % haxxorname[0])
            irc.msg(channel, f"{hostmask[0]}: defcon 4 set: automatic kickban")
        elif lat[0] == f"badword":
            if lat[1] != "list" and len(lat) < 3 or len(lat) > 3:
                irc.msg(channel, f"{hostmask[0]}: usage: badword (add | del | list) word")
            elif lat[1] == "add":
                action = 1
            elif lat[1] == "del":
                action = 0
            elif lat[1] == "list":
                badwords = open("bw.txt").read().strip().split("\n")
                irc.msg(channel, f"{hostmask[0]}: list of badwords is {badwords}")
            else:
                irc.msg(channel, f"{hostmask[0]}: usage: badword (add | del | list) word")
            if lat[1] == "add" or lat[1] == "del":
                irc.msg(channel, f"{hostmask[0]}: " + badword(action, lat[2]))
        else:
            irc.msg(channel, f"{hostmask[0]}: usage: {irc.current_nick} (off | noop | censor | quiet | ban | ducks | badword | target)")
    elif args[-1].startswith(f"{irc.current_nick}:"):
        irc.msg(channel, f"{hostmask[0]}: no")


@irc.Handler("MODE", colon=False)
def yay(irc, hostmask, args):
    if not defcon[0]: return
    channel = args[0]
    if args[1] == "-o" and args[2] == irc.current_nick:
        irc.msg("ChanServ", "OP", channel)
    if args[1] == "+o" and args[2] == haxxorname[0]:
        irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    if hostmask[0] != haxxorname[0]:
        return
    irc.msg("ChanServ", "OP", channel)
    irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    irc.send("MODE", channel, ''.join([trans(s) for s in args[1]]), *(args[2:]))
@irc.Handler("TOPIC", colon=False)
def yay(irc, hostmask, args):
    if not defcon[0]: return
    channel = args[0]
    text = args[-1]
    t = text.lower()
    if hostmask[0] != haxxorname[0]:
        topic[0] = text
        return
    irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    irc.send(
            "TOPIC",
            channel,
            topic[0]
    )
@irc.Handler("474", colon=False)
def yay(irc, hostmask, args):
    channel = args[1]
    if defcon[0]:
        irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    irc.msg(
            "ChanServ",
            "UNBAN",
            channel
    )
    irc.send("JOIN", channel)

@irc.Handler("475", colon=False)
def yay(irc, hostmask, args):
    channel = args[1]
    if defcon[0]:
        irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    time.sleep(3)
    irc.send("JOIN", channel)

@irc.Handler("471", colon=False)
def yay(irc, hostmask, args):
    channel = args[1]
    if defcon[0]:
        irc.msg("ChanServ", "DEOP", channel, haxxorname[0])
    time.sleep(3)
    irc.send("JOIN", channel)

if __name__ == "__main__":
    irc.require("users")
    irc.require("chans")
    irc.connect()
