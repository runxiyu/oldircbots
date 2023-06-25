#!/usr/bin/python3

"""
Simple python IRC bot to interject on bad vocabulary.  Might provide
simple channel management in the future.

In the free software community, reminding people of forgotten but
fundemental philosophies is important.

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
nick = "dhparam"
ident = nick
realname = "DefinitelyNotDiffieHellmanBot"
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


@irc.Handler("KICK", colon=False)
def handle_kick(irc, hostmask, args):
    channel = args[0]
    if args[1] == irc.current_nick:
        irc.send("JOIN", channel)
        irc.msg(
            channel,
            f"{hostmask[0]}: If you want me to leave, use #part instead of kicking me.  Otherwise I'd summon an army of GNUs.",
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
    if (
        "i use linux as my operating system" in t
        or "i use linux as my os" in t
        or "linux is my os" in t
        or "i run linux" in t
        or "use linux instead" in t
        or "switch to linux" in t
    ) and "kernel" not in t:
        irc.msg(
            channel,
            """Please don't call our operating system "Linux".  Linux is the name of the kernel that is usually used in the GNU operating system.  It also doesn't tell people about the ethical philosophy behind the operating system we use.  If it wasn't for RMS developing GNU, then the GNU GPL and presenting it to Linus Torvalds, Linux might not be free now.""",
        )
        irc.msg(
            channel,
            """Please refer to https://www.gnu.org/gnu/why-gnu-linux.en.html for more information.""",
        )
    if "i use gnu/linux" in t:
        irc.msg(channel, """Me too!""")
    if (
        (
            "like open source" in t
            or "love open source" in t
            or "like open-source" in t
            or "love open-source" in t
            or "open-source!" in t
            or "open source!" in t
            or "is open source" in t
            or "is open-source" in t
        )
        and "free" not in t
        and "libre" not in t
        and "gnu" not in t
        and "fsf" not in t
        and "stallman" not in t
        and "rms" not in t
    ):
        irc.msg(
            channel,
            """"Open Source" misses the point!  See https://www.gnu.org/philosophy/open-source-misses-the-point.en.html.""",
        )
    if "ethernet cable" in t:
        irc.msg(
            channel,
            """Ethernet is a protocol, not something physical.  Say cat5 or cat5e or cat6 cable depending on the setup.""",
        )
    if "quack" in t and hostmask[0] in {"LitBot", "tildebot"}:
        irc.msg(
            channel,
            f"""{hostmask[0]}: bef""",
        )
    bad = "\x68\x6D\x6D"
    if (t.startswith(bad) or " " + bad in t) and channel == "#librespeech":
        print(f"trying to kick {hostmask[0]} from {channel}")
        irc.send(
            "KICK",
            channel,
            hostmask[0],
            "Do not use this word.  A user in this channel has Tourette Syndrome.",
        )
    if ",open source" in t or ",opensource" in t or ",open-source" in t:
        irc.msg(
            channel,
            """"Open Source" misses the point!  See https://www.gnu.org/philosophy/open-source-misses-the-point.en.html.""",
        )
    if ",guix" in t:
        irc.msg(
            channel,
            """GNU Guix is the advanced distribution of GNU.  See https://guix.gnu.org.""",
        )
    if ",fsw" in t or ",free software" in t:
        irc.msg(
            channel,
            """Free software means that the users have the freedom to run, edit, contribute to, and share the software. Thus, free software is a matter of liberty, not price. We have been defending the rights of all software users for the past 35 years.""",
        )
    if ",fcm" in t:
        irc.msg(
            channel,
            """The Free Computing Movement is meant to be an extension of the Free Software Movement to everywhere in computing, not just in software.  See https://fcm.andrewyu.org.""",
        )
    if ",andrew" in t:
        irc.msg(
            channel,
            """Andrew is a random guy.  Per Website is https://www.andrewyu.org, email andrew@andrewyu.org.  Perse owns me and loves free software.""",
        )
    if ",MrArthegor" in t:
        irc.msg(
            channel,
            """MrArthegor is nobody at all!""",
        )
    if ",test_user" in t:
        irc.msg(
            channel,
            """Test_User is a professional haxxor from worldwide haxing industries.""",
        )
    if irc.current_nick in w[0]:
        if "are" in t and "you" in t and "bot" in t:
            irc.msg(
                channel,
                f"""Yes, I am a robot.  Say {irc.current_nick}: help  for more information.""",
            )
        else:
            try:
                irc.msg(
                    channel,
                    f"""Hi!  I'm a DefinitelyNotDiffieHellman bot.  I think {why[channel]} brought me here.  I remind people of forgotten but fundemental philosophies in free software and society, along with basic factoids.  My source code is at https://git.andrewyu.org/ircbots/.  Say "#part" to make me leave.  The documentation is in the source code.""",
                )
            except KeyError:
                irc.msg(
                    channel,
                    f"""Hi!  I'm a DefinitelyNotDiffieHellman bot.  I forgot who brought me here though.  My owner is {owner}.  I remind people of forgotten but fundemental philosophies in free software and society, along with basic factoids.  My source code is at https://git.andrewyu.org/ircbots/.  Say "#part" to make me leave.  The documentation is in the source code.""",
                )
    elif "#join" == w[0]:
        irc.send("JOIN", words[1])
        why[words[1]] = hostmask[0]
        print(hostmask[0], words[1])
    elif "#part" == w[0]:
        if not c:
            irc.msg(channel, "You must say this in the channel you want me to part.")
        elif len(w) <= 1:
            irc.send("PART", channel, f"Requested by {hostmask[0]}")
        else:
            irc.send("PART", w[1], f"Requested by {hostmask[0]}: {' '.join(w[2:])}")


# Connect
if __name__ == "__main__":
    irc.require("users")
    irc.require("chans")
    irc.connect()
