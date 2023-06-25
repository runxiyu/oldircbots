#!/usr/bin/python3

import miniirc
import sys
from miniirc import *

assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

nick = "Guard"
ident = nick
realname = "Simple Channel Services Bot: https://git.andrewyu.org/ircbots"
identity = "LibreBot redacted"
debug = True

channels = {
    "##gnuhackers": {
        "flags": {
            ("Andrew", "user/AndrewYu"): [
                "ban",
                "kick",
                "op",
                "autoop",
                "invite",
                "masskick",
                "voice",
                "set",
                "spam",
            ]
        }
    },
    "#librespeech": {
        "flags": {
            ("~leah", "libreboot/developer/leah"): [
                "ban",
                "kick",
                "op",
                "autoop",
                "invite",
                "masskick",
                "voice",
                "set",
                "spam",
            ],
            ("Andrew", "user/AndrewYu"): [
                "ban",
                "kick",
                "op",
                "autoop",
                "invite",
                "masskick",
                "voice",
                "set",
                "spam",
            ],
        }
    },
}
cnames = channels.keys()


def flags(channel, hostmask):
    return channels[channel]["flags"][(hostmask[1], hostmask[2])]


prefix = "/"

ip = "irc.libera.chat"
port = 6697

# Welcome!
print("Welcome to {}!".format(nick), file=sys.stderr)
irc = IRC(
    ip,
    port,
    nick,
    cnames,
    ident=ident,
    realname=realname,
    ns_identity=identity,
    debug=debug,
    auto_connect=False,
)


@irc.Handler("JOIN", colon=False)
def handle_join(irc, hostmask, args):
    channel = args[0]

    @irc.Handler("PRIVMSG", colon=False)
    def handle_privmsg(irc, hostmask, args):
        channel = args[0]
        text = args[-1].split(" ")
        cmd = text[0].lower()
        cmdargs = text[1:]
        if cmd.startswith(prefix):
            cmd = cmd[len(prefix) :]
            if len(flags(channel, hostmask)) < 1:
                irc.msg(
                    channel,
                    f"{hostmask[0]}: You are not authorized to use {irc.nick}.",
                )
                if cmd == "help":
                    irc.msg(
                        channel,
                        "I am {}, a simple channel services implementation.  This is not a replacement for ChanServ yet.".format(
                            irc.nick
                        ),
                    )
        elif cmd == "ban":
            if "!" in cmdargs[0] and "@" in cmdargs[0]:
                irc.send("MODE", channel, "+b", cmdargs[0])
                irc.send("KICK", channel, hostmask[0], cmdargs[2:])
        else:
            irc.msg(channel, f"{hostmask[0]}: Invalid command.")


if __name__ == "__main__":
    irc.connect()
