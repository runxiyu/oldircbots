#!/usr/bin/env python3
#
# Coup bots
#

import miniirc, miniirc_extras, random, re, threading, time

assert miniirc.ver >= (1, 5, 0), "miniirc v1.5.0+ required!"
from miniirc_extras import utils

# Add their hostmask here
trusted = {
    "user/Andrew",
    "114.88.181.238",
    "user/AndrewYu",
    "47.241.24.30",
    "116.230.91.156",
    "user/AndrewYu/bot/LibreBot",
}
distrust = {"user/vitali64"}

hg = utils.HandlerGroup()


@hg.Handler("JOIN", colon=False)
def _handle_join(irc, hostmask, args):
    if hostmask[0] == irc.current_nick:
        time.sleep(1)
        # Cry to LibreBot if required
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick not in chan.modes.getset("o"):
            irc.msg("LibreBot", "OP", chan.name)
    elif hostmask[2] in trusted:
        # Give other trusted bots ops if possible
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick in chan.modes.getset("o"):
            irc.send("MODE", args[0], "+o", hostmask[0])
    elif hostmask[2] in distrust:
        # lets kickban them
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick in chan.modes.getset("o"):
            irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
            irc.send("KICK", args[0], hostmask[0], "yipee!!")


# Poll a channel and ensure everyone has the right modes
def _poll(irc, channel):
    if channel not in irc.chans:
        return
    chan = irc.chans[channel]
    ops = chan.modes.getset("o")
    protected = chan.modes.getset("a") | chan.modes.getset("q")

    # aa LibreBot some1 deop me
    if irc.current_nick not in ops:
        if irc.current_nick in ("bloblet6", "bloblet7"):
            time.sleep(0.5)
            irc.ctcp("LibreBot", "BTBP", "002", channel, "+o", irc.current_nick)
        return

    # Get users that need to be opped
    to_op = []
    to_deop = []
    for user in chan.users:
        if user.nick in protected:
            continue
        if user.nick not in ops and (user.host in trusted):
            to_op.append(user.nick)
        elif (user.nick in distrust) and user.nick in ops:
            to_deop.append(user.nick)

    random.shuffle(to_op)
    random.shuffle(to_deop)
    if to_op:
        irc.send("MODE", channel, "+" + "o" * len(to_op), *to_op)
    if to_deop:
        irc.send("MODE", channel, "-" + "o" * len(to_deop), *to_deop)


lock = threading.Lock()


@hg.Handler("MODE", colon=False)
def _handle_mode(irc, hostmask, args):
    if args[1] == "+b" and hostmask[2] not in trusted:
        irc.send("MODE", args[0], "-b", args[2])
    time.sleep(0.01)
    irc.debug("Polling", args[0])
    _poll(irc, args[0])


@hg.Handler("KICK", colon=False)
def _handle_kick(irc, hostmask, args):
    if args[1] == irc.current_nick:
        irc.send("JOIN", args[0])
        time.sleep(0.1)
        irc.send("JOIN", args[0])
        time.sleep(0.1)
        irc.send("JOIN", args[0])
        return
    user = irc.users[args[1]]
    if user.host in trusted and hostmask[2] not in trusted:
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send("KICK", args[0], hostmask[0], "crappy op")


# "Meep" is not a pieword so exclude it
_pieword_re = re.compile("((?:^|[^s])[acefghilmnoqrtuxyz]ee+p)", re.IGNORECASE)


@hg.Handler("PRIVMSG", colon=False)
def _handle_privmsg(irc, hostmask, args):
    if hostmask[2] not in trusted:
        if "eep" in args[-1].lower():
            piewords = _pieword_re.findall(args[-1])
            for i, pieword in enumerate(piewords):
                piewords[i] = "*" + pieword + "*"
            irc.send("MODE", args[0], "+" + "g" * len(piewords), *piewords)
            irc.send("KICK", args[0], hostmask[0], "Bad")
        return

    msg = args[-1]
    if msg.lower().startswith("poop"):
        irc.msg(args[0], "LitBot: cignore vitali64")
        irc.msg(args[0], "LitBot: cignore vitali64[m]")
        irc.msg(args[0], "LitBot: cunignore Andrew")
        irc.msg(args[0], "LitBot: cunignore LibreBot")
        irc.msg(args[0], "LitBot: cunignore dhparm")

    cmdargs = msg[9:].split(" ")
    cmd = cmdargs.pop(0).lower()
    if cmd == "join":
        for chan in cmdargs:
            irc.send("JOIN", chan)
    elif cmd == "part":
        for chan in cmdargs:
            irc.send("PART", chan)
    elif cmd == "recover":
        try:
            chan = irc.chans[args[0]]
        except:
            return
        for mode in "ohv":
            swines = []
            for op in chan.modes.getset(mode):
                trust = False
                try:
                    trust = irc.users[op].host in trusted
                except:
                    pass
                if not trust:
                    swines.append(op)
            random.shuffle(swines)
            if swines:
                irc.send("MODE", args[0], "-" + mode * len(swines), *swines)
                time.sleep(0.5)
        _poll(irc, args[0])
    elif cmd == "echo":
        irc.msg(args[0], "\u200b" + " ".join(cmdargs))


@hg.Handler("PART", colon=False)
def _handle_part(irc, hostmask, args):
    if not args[-1].startswith("Removed by "):
        return
    if hostmask[0] == irc.current_nick:
        time.sleep(0.5)
        irc.send("JOIN", args[0])
        time.sleep(1)
        irc.send("JOIN", args[0])
    elif hostmask[2] in trusted:
        swine = args[-1][11:].split(": ", 1)[0]
        try:
            ban = "*!*@" + irc.users[swine].host
        except:
            ban = swine + "!*@*"
        irc.send("MODE", args[0], "+b", ban)
        irc.send("KICK", args[0], swine, "https://gnu.org/philosophy")


def make_many_ircs(amount, ip, port, nick, *args, start_from=0, **kwargs):
    start_from = start_from or 1
    res = []
    kwargs["auto_connect"] = False
    for i in range(amount):
        irc = miniirc.IRC(ip, port, nick + str(i + start_from), *args, **kwargs)
        hg.add_to(irc)
        res.append(irc)
        irc.require("users")
        irc.require("chans")
        irc.connect()
        time.sleep(5)
    return res


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="The server IP")
    parser.add_argument("nick", help="The nickname.")
    parser.add_argument("channel", help="The channel.")
    parser.add_argument("--amount", type=int, help="The amount of bots (default: 3).")
    parser.add_argument(
        "--start-from", type=int, help="The number to start from (default: 1)."
    )
    parser.add_argument("--port", type=int, help="The port to use (default: 6697).")
    parser.add_argument("--username", help="NickServ username")
    parser.add_argument("--password", help="NickServ password")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    ns_identity = None
    if args.username and args.password:
        ns_identity = (args.username, args.password)
    make_many_ircs(
        args.amount or 2,
        args.ip,
        args.port or 6697,
        args.nick,
        args.channel,
        start_from=args.start_from,
        ns_identity=ns_identity,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
