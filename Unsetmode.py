#!/usr/bin/env python3


import miniirc, miniirc_extras, random, re, threading, time
from ast import literal_eval

assert miniirc.ver >= (1, 5, 0), "miniirc v1.5.0+ required!"
from miniirc_extras import utils

# Add their hostmask here
trusted = {
    "andrewyu.org",
    "user/Lareina",
}
banned = {"fases/developer/funderscore"}

trusted = set([i.lower() for i in trusted])
banned = set([i.lower() for i in banned])

igotban = []

hg = utils.HandlerGroup()


@hg.Handler("PART", colon=False)
def _handle_part(irc, hostmask, args):
    if hostmask[0] == irc.current_nick:
        irc.send("JOIN", args[0])
    else:
        irc.send("INVITE", args[0], hostmask[0])


@hg.Handler("JOIN", colon=False)
def _handle_join(irc, hostmask, args):
    if hostmask[0] == irc.current_nick:
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick not in chan.modes.getset("o"):
            irc.msg("ChanServ", "OP", chan.name)
    else:
        irc.send("KICK", args[0], hostmask[0], "Channel is locked")


lock = threading.Lock()


@hg.Handler("MODE", colon=False)
def _handle_mode(irc, hostmask, args):
    if not args[0][0] == "#":
        return
    if args[2] == irc.current_nick or hostmask[0] == irc.current_nick:
        return
    if args[1][0] == "-":
        f = "+"
    else:
        f = "-"
    irc.send("MODE", args[0], f + args[1][1:], *args[2:])


@hg.Handler("KICK", colon=False)
def _handle_kick(irc, hostmask, args):
    if args[1] == irc.current_nick:
        irc.send("JOIN", args[0])
        ops = irc.chans[args[0]].modes.getset("o")
        print("@@@", ops)
        for op in ops:
            if op == irc.current_nick:
                continue
            irc.send("MODE", args[0], "-o", op)
    else:
        irc.msg(args[0], "YAYKICK!")


def make_many_ircs(amount, ip, port, nick, *args, start_from=0, **kwargs):
    start_from = start_from or 1
    res = []
    kwargs["auto_connect"] = False
    for i in range(amount):
        if i == 0:
            irc = miniirc.IRC(ip, port, nick, *args, **kwargs)
        else:
            irc = miniirc.IRC(ip, port, nick + str(i + start_from), *args, **kwargs)
        hg.add_to(irc)
        res.append(irc)
        irc.require("users")
        irc.require("chans")
        irc.connect()
        time.sleep(1)
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
        args.amount or 1,
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
