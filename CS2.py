#!/usr/bin/python3

import miniirc
import miniirc_extras
import sys
import time

assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

exec("from " + sys.argv[1] + " import *")


def flags(channel, user):
    try:
        return chandata[channel.name][user.raw_hostmask]
    except KeyError:
        return set()


def grant(channel, user, flag):
    try:
        chandata[channel.name][user.raw_hostmask].add(flag)
        return chandata[channel.name][user.raw_hostmask]
    except KeyError:
        chandata[channel.name][user.raw_hostmask] = {flag}
        return chandata[channel.name][user.raw_hostmask]


def revoke(channel, user, flag):
    try:
        chandata[channel.name][user.raw_hostmask].remove(flag)
        return chandata[channel.name][user.raw_hostmask]
    except KeyError:
        return False


def hammer(channel, user, poop):
    try:
        chaneww[channel.name][user.raw_hostmask].add(poop)
        return chaneww[channel.name][user.raw_hostmask]
    except KeyError:
        chaneww[channel.name][user.raw_hostmask] = {poop}
        return chaneww[channel.name][user.raw_hostmask]


def lift(channel, user, poop):
    try:
        chaneww[channel.name][user.raw_hostmask].remove(poop)
        return chaneww[channel.name][user.raw_hostmask]
    except KeyError:
        return False


def devoice(irc, channel, target):
    if target.nick in channel.modes.getset("+v"):
        irc.send("MODE", channel.name, "-v", target.nick)
        return True
    return False


def voice(irc, channel, target):
    if not target.nick in channel.modes.getset("+v"):
        irc.send("MODE", channel.name, "+v", target.nick)
        return True
    return False


def deop(irc, channel, target):
    print(72 * "-")
    print(channel.modes.getset("o"))
    if target.nick in channel.modes.getset("o"):
        irc.send("MODE", channel.name, "-o", target.nick)
        return True
    return False


def op(irc, channel, target):
    if not target.nick in channel.modes.getset("o"):
        irc.send("MODE", channel.name, "+o", target.nick)
        return True
    return False


def quiet(irc, channel, target, seconds, reason):
    deop(irc, channel, target)
    hammer(channel, target, "quiet")
    irc.send("MODE", channel.name, "+q", f"*!{target.ident}@{target.host}")
    if int(seconds) > 0:
        time.sleep(int(seconds))
        irc.send("MODE", channel.name, "-q", f"*!{target.ident}@{target.host}")
        lift(channel, target, "quiet")


def kick(irc, channel, target, reason):
    irc.send("KICK", channel.name, target.nick, reason)


def ban(irc, channel, target, seconds, reason):
    deop(irc, channel, target)
    hammer(channel, target, "ban")
    irc.send("MODE", channel.name, "+b", f"*!{target.ident}@{target.host}")
    kick(irc, channel, target, reason)
    if int(seconds) > 0:
        time.sleep(int(seconds))
        irc.send("MODE", channel.name, "-b", f"*!{target.ident}@{target.host}")
        lift(channel, target, "ban")


print("Welcome to {}!".format(nick), file=sys.stderr)
irc = miniirc.IRC(
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
    channame = args[0]
    try:
        channel = irc.chans[channame]
    except AssertionError:
        pass
    text = args[-1].split(" ")
    cmd = text[0].lower()
    if cmd.startswith(prefix) and channame.startswith("#"):
        cmd = cmd[len(prefix) :]
        p = False
    elif channame == irc.nick:
        p = True
    else:
        return
    try:
        if cmd == "help":
            irc.notice(
                hostmask[0],
                f"\x02Guard\x02 is a client-bot channel management utility.  Documentation is in the source code at git://git.andrewyu.org/ircbots.  The prefix charactar is '{prefix}'.",
            )
        # the below are channel-only
        elif p:
            return
        elif cmd == "ban":
            if "ban" in flags(channel, irc.users[hostmask[0]]):
                ban(irc, channel, irc.users[text[1]], text[2], " ".join(text[3:]))
            else:
                irc.notice(hostmask[0], f"[{channame}] Permission denied.")
        elif cmd == "op":
            if "op" in flags(channel, irc.users[hostmask[0]]):
                if len(text) < 2:
                    irc.send("MODE", channame, "+o", hostmask[0])
                elif text[1] == "":
                    irc.send("MODE", channame, "+o", hostmask[0])
                else:
                    irc.send("MODE", channame, "+o", text[1])
            else:
                irc.notice(hostmask[0], f"[{channame}] Permission denied.")
        elif cmd == "grant":
            if "flags" in flags(channel, irc.users[hostmask[0]]):
                grant(channel, irc.users[text[1]], text[2])
            else:
                irc.notice(hostmask[0], f"[{channame}] Permission denied.")
        elif cmd == "revoke":
            if "flags" in flags(channel, irc.users[hostmask[0]]):
                revoke(channel, irc.users[text[1]], text[2])
            else:
                irc.notice(hostmask[0], f"[{channame}] Permission denied.")
        elif cmd == "quiet":
            if "ban" in flags(channel, irc.users[hostmask[0]]):
                quiet(irc, channel, irc.users[text[1]], text[2], " ".join(text[3:]))
            else:
                irc.notice(hostmask[0], f"[{channame}] Permission denied.")
        elif cmd == "flags":
            _ = flags(channel, irc.users[text[1]])
            if _:
                irc.notice(
                    hostmask[0],
                    f"[{channame}] Flags of {text[1]}: " + ", ".join(_) + ".",
                )
            else:
                irc.notice(hostmask[0], f"[{channame}] {text[1]} has no flags.")
        else:
            irc.notice(hostmask[0], f"[{channame}] Invalid command.")
    except (KeyError, IndexError) as e:
        irc.notice(hostmask[0], f"[{channame}] {str(type(e))}: {str(e)}.")


# @irc.Handler("JOIN", colon=False)
# def handle_privmsg(irc, hostmask, args):

if __name__ == "__main__":
    # make sure you have miniirc_extras
    irc.require("chans")
    irc.require("users")
    irc.connect()
