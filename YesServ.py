#!/usr/bin/env python3
#
# Channel Services
#

import miniirc, miniirc_extras, random, re, threading, time
from ast import literal_eval

assert miniirc.ver >= (1, 5, 0), "miniirc v1.5.0+ required!"
from miniirc_extras import utils

# Add their hostmask here
trusted = {
    "andrewyu.org",
    "services.libera.chat",
    "user/Lareina",
}
banned = {"fases/developer/funderscore"}

trusted = set([i.lower() for i in trusted])
banned = set([i.lower() for i in banned])

igotban = []

hg = utils.HandlerGroup()


@hg.Handler("JOIN", colon=False)
def _handle_join(irc, hostmask, args):
    if hostmask[0] == irc.current_nick:
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick not in chan.modes.getset("o"):
            irc.msg("ChanServ", "OP", chan.name)
    elif hostmask[2].lower() in trusted:
        # Give ops ops if possible
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick in chan.modes.getset("o"):
            if hostmask[0] not in chan.modes.getset("o"):
                irc.send("MODE", args[0], "+o", hostmask[0])
            else:
                irc.msg(
                    chan.name,
                    "Hi " + hostmask[0]
                )
    elif hostmask[2] in banned:
        # lets kickban them
        try:
            chan = irc.chans[args[0]]
        except KeyError:
            return
        if irc.current_nick in chan.modes.getset("o"):
            irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
            irc.send("KICK", args[0], hostmask[0], "User is banned")
            irc.msg(
                hostmask[0],
                "Heya, you're banned from "
                + chan.name
                + ".  Tell the ops for any questions, I guess.",
            )


# Poll a channel and ensure everyone has the right modes
def sync(irc, channel):
    if channel not in irc.chans:
        return
    chan = irc.chans[channel]
    ops = chan.modes.getset("o")

    if irc.current_nick not in ops:
        irc.msg(chan.name, "Something happened to my ops!")
        return

    # Get users that need to be opped
    to_op = []
    to_deop = []
    for user in chan.users:
        if user.nick not in ops and (user.host.lower() in trusted):
            to_op.append(user.nick)
        elif (user.host.lower() not in trusted) and user.nick in ops:
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
    if (
        args[1] == "+b" and hostmask[2].lower() not in trusted
    ):  # unauthorized banning people
        irc.send("MODE", args[0], "-o", hostmask[0])
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send(
            "KICK",
            hostmask[0],
            "You are not allowed to set bans but you banned someone, therefore you are now banned.",
        )
        # irc.send('MODE', args[0], '-b', args[2])
    elif (
        args[1].startswith("+o") and hostmask[2].lower() not in trusted
    ):  # unauthorized opping people
        irc.send("MODE", args[0], "-o", hostmask[0])
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send(
            "KICK",
            args[0],
            hostmask[0],
            "You are not allowed to op people but you did so, therefore you are now banned.",
        )
        if args[2] != irc.nick:
            irc.send("MODE", args[0], "-oooo", args[2])
    elif (
        args[1].startswith("-o") and hostmask[2].lower() not in trusted
    ):  # unauthorized deoping people
        irc.send("MODE", args[0], "-o", hostmask[0])
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send(
            "KICK",
            args[0],
            hostmask[0],
            "You are not allowed to op people but you did so, therefore you are now banned.",
        )
        irc.send("MODE", args[0], "+oooo", args[2])
    elif args[1] == "-o" and args[2] == irc.current_nick:  # deoping the bot
        irc.msg(
            args[0],
            f"Hey {' '.join(irc.chans[args[0]].modes.getset('o'))}, {hostmask[0]} deoped me!",
        )
        irc.msg(
            "ChanServ",
            f"OP {args[0]}",
        )
    elif (
        args[1] == "-o" and irc.users[args[2]].host.lower() in trusted
    ):  # deoping authorized people
        if hostmask[2].lower() not in trusted:
            irc.send("MODE", args[0], "-o", hostmask[0])
            irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
            irc.send(
                "KICK",
                args[0],
                hostmask[0],
                "You are not allowed to deop trusted people but you did so, therefore you are now banned.",
            )
    #        irc.send('MODE', args[0], '+o', args[2])
    elif args[1] == "+b":
        for each in trusted:
            if each.lower() in args[2].lower():
                irc.send("MODE", args[0], "-b", args[2])
                break
    elif args[1] == "+o":
        # and args[2] not in trusted: # opping unauthorized people
        if irc.users[args[2]].host.lower() not in trusted:
            irc.send("MODE", args[0], "-o", args[2])


@hg.Handler("KICK", colon=False)
def _handle_kick(irc, hostmask, args):
    if args[1] == irc.current_nick:
        print("Awwwww!")
        irc.send("JOIN", args[0])
        time.sleep(0.4)
        irc.msg("LibreBot", "OP " + args[0] + " " + irc.current_nick)
        irc.msg(
            args[0],
            hostmask[0]+ f": HOW DARE YOU",
        )
        irc.send("MODE", args[0], "-o", hostmask[0])
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send(
            "KICK",
            args[0],
            hostmask[0],
            "Eat jet engines!"
        )
        # ops = irc.chans[args[0]].modes.getset("o")

#         print("@@@", ops)
#         for op in ops:
#             if op == irc.current_nick:
#                 continue
#             irc.send("MODE", args[0], "-o", op)

        return
    user = irc.users[args[1]]
    if (
        user.host.lower() in trusted and hostmask[2].lower() not in trusted
    ):  # unauthorized kicking people
        irc.send("MODE", args[0], "+b", "*!*@" + hostmask[2])
        irc.send(
            "KICK",
            args[0],
            hostmask[0],
            "You are not authorized to kick people, therefore you are now banned.",
        )


@hg.Handler("PRIVMSG", colon=False)
def _handle_privmsg(irc, hostmask, args):
    if "fuck" in args[-1].lower():
        irc.msg(args[0], f"{hostmask[0]} fuck you instead")
        return

    msg = args[-1]
    if not msg.startswith(f"{irc.current_nick}: "):
        return

    print(hostmask)
    if hostmask[2].lower() not in trusted:
        print("stranger")
        irc.msg(args[0], "stranger I don't know ya")
        return

    cmdargs = msg[len(irc.current_nick) + 2 :].split(" ")
    cmd = cmdargs.pop(0).lower()
    if cmd == "join":
        for chan in cmdargs:
            irc.send("JOIN", chan)
    elif cmd == "sync":
        sync(irc, args[0])
    #        try:
    #            chan = irc.chans[args[0]]
    #        except:
    #            return
    #        for mode in 'ov':
    #            swines = []
    #            for op in chan.modes.getset(mode):
    #                trust = False
    #                try:
    #                    trust = irc.users[op].host in trusted
    #                except:
    #                    pass
    #                if not trust:
    #                    swines.append(op)
    #            random.shuffle(swines)
    #            if swines:
    #                irc.send('MODE', args[0], '-' + mode * len(swines), *swines)
    #                time.sleep(0.5)
    elif cmd == "kick":
        irc.send("KICK", args[0], cmdargs[0], " ".join(cmdargs[1:]))
    elif cmd == "eval":
        try:
            irc.msg(args[0], str(literal_eval(" ".join(cmdargs))))
        except Exception as e:
            irc.msg(args[0], str(e))
    elif cmd == "quote":
        irc.quote(" ".join(cmdargs))
    elif cmd == "echo":
        irc.msg(args[0], " ".join(cmdargs))
    elif cmd == "op":
        irc.send("MODE", args[0], "+o", cmdargs[0])
    elif cmd == "trust":
        trusted.add(irc.users[cmdargs[0]].host.lower())
        irc.send("MODE", args[0], "+o", cmdargs[0])
    elif cmd == "untrust":
        print(cmdargs)
        print(irc.users[cmdargs[0]].host.lower())
        print(trusted)
        trusted.discard(irc.users[cmdargs[0]].host.lower())
        irc.send("MODE", args[0], "-o", cmdargs[0])
        print(trusted)
    elif cmd == "ban":
        print(cmdargs)
        print(irc.users[cmdargs[0]].host.lower())
        print(trusted)
        trusted.discard(irc.users[cmdargs[0]].host.lower())
        irc.send("MODE", args[0], "-o", cmdargs[0])
        print(trusted)
        banned.add(irc.users[cmdargs[0]].host.lower())
        irc.send("MODE", args[0], "+b", "*!*@" + irc.users[cmdargs[0]].host.lower())
        irc.send("KICK", args[0], cmdargs[0], " ".join(cmdargs[1:]))
    elif cmd == "unban":
        try:
            banned.remove(irc.users[cmdargs[0]].host.lower())
            irc.send("MODE", args[0], "-b", "*!*@" + irc.users[cmdargs[0]].host.lower())
        except KeyError:
            irc.msg(
                args[0],
                "I don't know who that is, maybe let them message me?  Or is this a permban in the database?",
            )
    else:
        irc.msg(args[0], f"Invalid command: {cmd}.")


@hg.Handler("PART", colon=False)
def _handle_part(irc, hostmask, args):
    if hostmask[0] == irc.current_nick:
        irc.send("JOIN", args[0])


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
