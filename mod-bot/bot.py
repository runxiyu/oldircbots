#!/usr/bin/env pythn3
#
# Single-connection IRC bot.
# Copyright (C) 2023       uhax
# Copyright (C) 2022-2023  Andrew Yu <https://www.andrewyu.org/>
# Copyright (C) 2022       luk3yx <https://luk3yx.github.io/>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file called LICENSE, under the heading "AGPLv3"
# until a single line with two dashes ("--") and no more.  If not, see
# <https://www.gnu.org/licenses/>.
#
# The function match_hostmask is under the license described from the heading
# "3BSD" until a single line two dashes and no more in the LICENSE file, with
# the following copyright notice:
#
#    Copyright (c) 2022  Andrew Yu <https://www.andrewyu.org/>
#    Copyright (c) 2002-2009  Jeremiah Fincher and others
#
#
# Random programming notes:
# Could add a callback system or a global delayed execution system somewhere
# Actually handle WHOIS replies
#
# Andrew rants:
# The awkward location left shift is on the UK keyboard layout is causing my left pinky to be in an awkward position, causing a lot of strain.


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable, Iterator
import socket
import sys
import base64
import re
import time


from config import (
    SERVER,
    PORT,
    NICK,
    IDENT,
    GECOS,
    CHANNELS,
    PREFIX,
    LOGIN,
    PASSWORD,
    ADMINS,
)

car = lambda l: l[0]
cdr = lambda l: l[1:]


@dataclass
class User:
    nick: bytes
    ident: Optional[bytes] = None
    host: Optional[bytes] = None
    on_server: Optional[bytes] = None
    in_channels: list[Channel] = field(default_factory=list)
    last_activity_time: Optional[float] = None
    last_activity: Optional[bytes] = None


@dataclass
class State:
    initiated: bool = False
    negotiated_caps: list[bytes] = field(default_factory=list)
    deal_with_these_caps_before_cap_end: list[bytes] = field(default_factory=list)


@dataclass
class Channel:
    name: bytes
    # joined = None: didn't even talk about this to the server, False: not joined, True: joined
    joined: Optional[bool] = None
    authorized: list[tuple[bytes, bytes, bytes]] = field(default_factory=list)
    users: list[User] = field(default_factory=list)
    ops: list[User] = field(default_factory=list)
    voices: list[User] = field(default_factory=list)
    actual_bans: list[tuple[bytes, bytes, bytes]] = field(default_factory=list)
    active_bans: list[tuple[bytes, bytes, bytes]] = field(default_factory=list)
    active_exceptions: list[tuple[bytes, bytes, bytes]] = field(default_factory=list)


@dataclass
class Message:
    cmd: bytes
    source: Optional[User]
    args: list[bytes]


class ProtocolViolation(Exception):
    pass

def match_hostmask(hostmask: bytes, pattern: bytes) -> bool:
    regexp = b""
    for i in list(pattern):
        c = i.to_bytes(1, "big")
        if c == b"*":
            regexp += b".*"
        elif c == b"?":
            regexp += b"."
        elif c in b"[{":
            regexp += b"[\\[{]"
        elif c in b"}]":
            regexp += b"[}\\]]"
        elif c in b"|\\":
            regexp += b"[|\\\\]"
        elif c in b"^~":
            regexp += b"[~^]"
        else:
            regexp += re.escape(c)
    regexp += b"$"
    return bool(re.compile(regexp, re.I).match(hostmask))

def ban_mask(s: socket.socket, channel: Channel, mask: bytes, protect: list[User] = []) -> Optional[list[User]]:
    nicks_to_kick: list[bytes] = []
    users_to_kick: list[User] = []
    for potential_target in channel.users:
        if not (potential_target.nick and potential_target.ident and potential_target.host): continue
        if match_hostmask(potential_target.nick + b"!" + potential_target.ident + b"@" + potential_target.host, mask):
            if potential_target in protect:
                return None
            nicks_to_kick.append(potential_target.nick)
            users_to_kick.append(potential_target)

    send(s, b"MODE", channel.name, b"+b", mask)
    for nick_to_kick in nicks_to_kick:
        send(s, b"KICK", channel.name, nick_to_kick)
    return users_to_kick


def is_admin(user: User) -> Optional[bool]:
    if not (user.nick and user.ident and user.host):
        return None
    for a in ADMINS:
        if match_hostmask((user.nick + b"!" + user.ident + b"@" + user.host), a):
            return True
    return False


def human_list_sep(l: list[bytes]) -> Optional[bytes]:
    if len(l) == 0:
        return None
    if len(l) == 1:
        return l[0]
    return b", ".join(l[:-1]) + b" and " + l[-1]


def parse_nih(nih: bytes) -> tuple[Optional[bytes], Optional[bytes], Optional[bytes]]:
    "Parse a nick!username@host into tuples"
    n_ih = nih.split(b"!", 1)
    if len(n_ih) < 2:
        return n_ih[0], None, None
    ih = n_ih[1].split(b"@", 1)
    if len(ih) < 2:
        return n_ih[0], ih[0], None
    return n_ih[0], ih[0], ih[1]


def parse_message(
    line: bytes,
) -> tuple[
    bytes, tuple[Optional[bytes], Optional[bytes], Optional[bytes]], list[bytes]
]:
    "Break a message into its command, source and list of arguments."
    split_line = line.split(b" ")
    del line

    if split_line[0].startswith(b":"):
        nih = split_line.pop(0)[1:]
        hostmask = parse_nih(nih)
        cmd = split_line.pop(0)
    else:
        cmd = split_line.pop(0)
        hostmask = (None, None, None)

    args = []
    c = 0
    for i in split_line:
        if i.startswith(b":"):
            args.append(b" ".join(split_line[c:]))
            args[-1] = args[-1][1:]
            break
        else:
            args.append(i)
        c += 1

    return cmd, hostmask, args


# def break_up(s: bytes, chunk_size: int) -> list[bytes]:
#     "Breaks some bytes up to smaller chunks, and return the chunks in a list."
#     if len(s) <= chunk_size:
#         return [s]
#     else:
#         return [s[0 : chunk_size + 1]] + break_up(s[chunk_size + 1 :], chunk_size)


def break_up(s: bytes, chunk_size: int) -> Iterator[bytes]:
    while len(s) > chunk_size:
        yield s[: chunk_size + 1]
        s = s[chunk_size + 1 :]
    yield s


def send(s: socket.socket, *args: bytes) -> bytes:
    if len(args) < 1:
        raise ValueError("No arguments to send")
    elif len(args) < 2:
        # When there's only one argument, i.e. the command, do not add a ":" before it, otherwise it would be treated as a message source, which is illegal.
        s.sendall(args[0] + b"\r\n")
        print("<", args[0].decode("utf-8", "surrogateescape"))
        return args[0]
    line: bytes = b""
    for arg in args[:-1]:
        if b" " in arg:
            raise ValueError("Illegal space in argument in %s to send()", repr(args))
        else:
            line += arg + b" "
    line += b":" + args[-1]
    s.sendall(line + b"\r\n")
    print("<", line.decode("utf-8", "surrogateescape"))
    return line


def reply(s: socket.socket, msg: Message, text: bytes) -> bytes:
    if msg.source is None:
        raise TypeError("Cannot reply to a message that doesn't have a source")
    if msg.cmd != b"PRIVMSG":
        raise TypeError(
            "reply() only accepts incoming PRIVMSG Message's as the msg argument"
        )
    if msg.args[0].startswith(b"#"):
        text = (b"%s: " % msg.source.nick) + text
        reply_to = msg.args[0]
    else:
        reply_to = msg.source.nick
    return send(s, b"PRIVMSG", reply_to, text)


IRC_CALLBACK_FUNCTION_TYPE = Callable[
    [socket.socket, State, User, dict[bytes, User], dict[bytes, Channel], Message], None
]
irc_callbacks: dict[bytes, list[tuple[IRC_CALLBACK_FUNCTION_TYPE, bool]]] = {}
# The bool here indicates if this callback is single-use.

def register_irc_callback(
    cmd: bytes,
) -> Callable[[IRC_CALLBACK_FUNCTION_TYPE], IRC_CALLBACK_FUNCTION_TYPE]:
    def add_handler(f: IRC_CALLBACK_FUNCTION_TYPE, single_use: bool = False) -> IRC_CALLBACK_FUNCTION_TYPE:
        try:
            irc_callbacks[cmd].append((f, single_use))
        except KeyError:
            irc_callbacks[cmd] = [(f, single_use)]

        return f

    return add_handler


@register_irc_callback(b"PING")
def handle_ping(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    try:
        send(s, b"PONG", msg.args[0])
    except IndexError:
        raise ProtocolViolation("PING without cookie") from None


@register_irc_callback(b"376")  # MOTD end: Ready to join channels
def handle_376(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    for channel in channels.values():
        send(s, b"JOIN", channel.name)


@register_irc_callback(b"422")  # No MOTD: Ready to join channels
def handle_422(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    for channel in channels.values():
        send(s, b"JOIN", channel.name)


@register_irc_callback(b"JOIN")
def handle_join(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    if msg.source is None:
        raise ProtocolViolation("JOIN without source")
    if msg.source.nick.lower() == me.nick.lower():
        try:
            channels[msg.args[0]].joined = True
        except KeyError:
            channels[msg.args[0]] = Channel(joined=True, name=msg.args[0])
        except IndexError:
            raise ProtocolViolation("JOIN without channel name") from None
    else:
        msg.source.in_channels.append(channels[msg.args[0]])
        channels[msg.args[0]].users.append(msg.source)


@register_irc_callback(b"PART")
def handle_part(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    if msg.source is None:
        raise ProtocolViolation("PART without source")
    if msg.source.nick.lower() == me.nick.lower():
        try:
            channels[msg.args[0]].joined = False
        except KeyError:
            # channels[msg.args[0]] = Channel(joined=False, name=msg.args[0])
            raise ProtocolViolation(
                "Received self-PART from channel that hasn't been JOINed"
            )
        except IndexError:
            raise ProtocolViolation("PART without channel name") from None
    else:
        try:
            msg.source.in_channels.remove(channels[msg.args[0]])
            channels[msg.args[0]].users.remove(msg.source)
        except ValueError:
            raise ProtocolViolation("Received PART for a user that hasn't joined the channel")


@register_irc_callback(b"352")  # WHO
def handle_352(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    try:
        user = users[msg.args[5].lower()]
    except KeyError:
        user = User(nick=msg.args[5], ident=msg.args[2], host=msg.args[3])
        users[msg.args[5].lower()] = user


@register_irc_callback(b"NICK")
def handle_nick(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    if msg.source is None:
        raise ProtocolViolation("NICK without source")
    del users[
        msg.source.nick.lower()
    ]  # We can't rename dictionary keys, so we remove and readd it.
    msg.source.nick = msg.args[0]
    users[msg.source.nick.lower()] = msg.source


@register_irc_callback(b"353")  # NAMES
def handle_353(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    channel = channels[msg.args[2]]
    nicklist = msg.args[3].split(b" ")
    for nick in nicklist:
        if nick.startswith(b"@") or nick.startswith(b"+"):
            nick = nick[1:]
        try:
            user = users[nick.lower()]
        except KeyError:
            user = User(nick=nick)
            users[nick.lower()] = user
        channel.users.append(user)
        user.in_channels.append(channel)
        if nick.startswith(b"@"):
            channel.ops.append(user)
        elif nick.startswith(b"+"):
            channel.voices.append(user)


@register_irc_callback(b"CAP")
def handle_cap(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    if msg.args[0] == b"*" and msg.args[1] == b"LS":
        capspecs = msg.args[2].split(b" ")
        for capspec in capspecs:
            kvp = capspec.split(b"=", 1)
            cap: bytes
            cap_arg: Optional[bytes]
            try:
                cap, cap_arg = kvp[0], kvp[1]
            except IndexError:
                cap, cap_arg = kvp[0], None

            if LOGIN and PASSWORD and cap == b"sasl":
                if cap_arg is None:
                    raise ProtocolViolation(
                        "Received capability list contains SASL entry without methods"
                    )
                if b"PLAIN" in cap_arg.split(b","):
                    send(s, b"CAP", b"REQ", b"sasl")
                else:
                    raise Exception("Server does not support any SASL methods that I have implemented")
            else:
                send(s, b"CAP", b"END")
                break # since we don't handle any capabilities other than SASL, we can just stop here...

    if msg.args[1] == b"ACK":
        if msg.args[2] == b"sasl":
            state.negotiated_caps.append(b"sasl")
            state.deal_with_these_caps_before_cap_end.append(b"sasl")
            send(s, b"AUTHENTICATE", b"PLAIN")


@register_irc_callback(b"AUTHENTICATE")
def handle_authenticate(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    assert LOGIN and PASSWORD
    send(
        s,
        b"AUTHENTICATE",
        base64.b64encode(LOGIN + b"\x00" + LOGIN + b"\x00" + PASSWORD),
    )


@register_irc_callback(b"903")  # SASL success
def handle_903(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    state.deal_with_these_caps_before_cap_end.remove(b"sasl")
    if not state.deal_with_these_caps_before_cap_end:
        send(s, b"CAP", b"END")


@register_irc_callback(b"PRIVMSG")
def handle_privmsg(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    if not msg.source:
        raise ProtocolViolation("PRIVMSG without source")

    target = msg.args[0]
    text = msg.args[1]

    channel: Optional[Channel]
    if target.startswith(b"#"):
        channel = channels[target]
        if not text.startswith(PREFIX):
            return
        text = text[len(PREFIX) :]
    elif target.lower() == me.nick.lower():
        channel = None
        if text.startswith(PREFIX):
            text = text[len(PREFIX) :]
    else:
        # A message addressed to a non-channel that isn't the bot itself?  Weird!
        return

    chat_command = text.split(b" ")
    chat_command[0] = chat_command[0].upper()

    if chat_command[0] == b"DUMP":
        print(repr(channels))
        print(repr(users))
        reply(s, msg, b"I dumped my channel and user database to standard output.")
        return
    elif chat_command[0] == b"BAN":
        if not channel:
            reply(s, msg, b"You may only do this in a channel.")
            return
        elif msg.source not in channel.users:
            reply(
                s,
                msg,
                b"You are not on the channel, and you're haxsending messages to it.  This isn't nice.",
            )
            return
        priv = is_admin(msg.source)
        if not priv:
            reply(s, msg, b"Access denied.")
            return
        elif not me in channel.ops:
            reply(
                s,
                msg,
                b"I am not a channel operator, so I can't kickban people.",
            )
            return

        kickban_string = chat_command[1]
        if b"@" in kickban_string:
            kickban_mask = kickban_string
            if b"!" not in kickban_mask:
                kickban_mask = b"*!" + kickban_mask
            n = ban_mask(s, channel, kickban_mask, protect=[me, msg.source])
            if n is None:
                reply(s, msg, b"I refuse to kick you or myself, for the sake of being kind!")
            else:
                reply(s, msg, b"Banned mask %s and kicked %d clients." % (kickban_mask, len(n)))

            return
        else:
            try:
                kickban_target = users[kickban_string.lower()]
                if not kickban_target.nick and kickban_target.ident and kickban_target.host:
                    send(s, "WHOIS", kickban_string)
                    reply(s, msg, b"Sorry, I don't know this user. Maybe try again?") # too lazy to get delay execution done right now
                    return
                # save the stack, perform another cycle of handling the new WHOIS information, and use this as a restart point
                # I miss Scheme
                # I can't handle the missing information here
                # TODO
                kickban_mask = b"*!%s@%s" % (kickban_target.ident if (not kickban_target.ident.startswith(b"~")) else b"*", kickban_target.host)
                n = ban_mask(s, channel, kickban_mask, protect=[me, msg.source])
                if n is None:
                    reply(s, msg, b"I refuse to kick you or myself, for the sake of being kind!")
                else:
                    reply(s, msg, b"Banned mask %s and kicked %d clients." % (kickban_mask, len(n)))
                    return
            except KeyError:
                reply(s, msg, b"You didn't provide a hostmask for me to kickban, so I assumed it's a nickname, but I don't know %s." % kickban_string)
                return
    elif chat_command[0] == b"FAKEOP":
        if not channel:
            reply(s, msg, b"You may only do this in a channel.")
            return
        elif msg.source not in channel.users:
            reply(
                s,
                msg,
                b"You are not on the channel, and you're haxsending messages to it.  This isn't nice.",
            )
            return
        priv = is_admin(msg.source)
        if not priv:
            reply(s, msg, b"Access denied.")
            return
        elif not me in channel.ops:
            channel.ops.append(me)
            reply(
                s,
                msg,
                b"I didn't think that I was a channel operator before, now I assume so.",
            )
            return
        else:
            reply(s, msg, b"No need!")
    elif chat_command[0] == b"OP":
        if not channel:
            reply(s, msg, b"You may only do this in a channel.")
            return
        elif msg.source not in channel.users:
            reply(
                s,
                msg,
                b"You are not on the channel, and you're haxsending messages to it.  This isn't nice.",
            )
            return
        priv = is_admin(msg.source)
        if priv is False:
            reply(s, msg, b"Access denied.")
            return
        elif priv is None:
            reply(
                s,
                msg,
                b"I don't know your ident or host, so I can't check your permissions.  Something is wrong.",
            )
            return
        elif msg.source in channel.ops:
            reply(s, msg, b"You are already a channel operator.")
            return
        elif not me in channel.ops:
            reply(
                s,
                msg,
                b"I am not a channel operator, so I can't make you a channel operator.",
            )
            return
        else:
            send(s, b"MODE", channel.name, b"+o", msg.source.nick)
            reply(s, msg, b"I tried to make you a channel operator.")
    elif chat_command[0] == b"WHOIS":
        if not is_admin(msg.source):
            reply(s, msg, b"Access denied.")
            return
        whois_target_nick = chat_command[1]
        if whois_target_nick.lower() == me.nick.lower():
            reply(s, msg, b"That's me, right?")
            return
        elif whois_target_nick.lower() == msg.source.nick.lower():
            reply(s, msg, b"You should know enough about yourself.  But oh well...")
        try:
            whois_target = users[whois_target_nick.lower()]
        except KeyError:
            reply(s, msg, b"I know nothing about %s." % whois_target_nick)
            return
        if whois_target.last_activity_time is None:
            reply(
                s,
                msg,
                b"I didn't see %s do anything while I was here." % whois_target.nick,
            )
        else:
            reply(
                s,
                msg,
                b"%s's last activity was %s seconds ago: %s"
                % (
                    whois_target.nick,
                    str(int(time.time() - whois_target.last_activity_time)).encode("ascii"),
                    whois_target.last_activity
                ),
            )
        if whois_target.in_channels:
            reply(s, msg, b"I am actively keeping track of %s through %s." % (whois_target.nick, human_list_sep([c.name for c in whois_target.in_channels])))
        else:
            reply(s, msg, b"I am not actively keeping track of %s as we don't have common channels." % whois_target.nick)
    elif chat_command[0] == b"HELP":
        # TODO for forkers: If you run this bot for public use, and you've changed the code (well, except for config.py), you must update the information below, in accordance with the AGPL.
        reply(
            s,
            msg,
            b"Hi!  I'm a simple IRC bot.  Consult git://git.andrewyu.org/irc-mod-bot.git/ for documentation.",
        )
    else:
        reply(s, msg, b"Unknown command: %s" % chat_command[0])


def handle_incoming_message(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    msg: Message,
) -> None:
    try:
        for callback in irc_callbacks[msg.cmd]:
            callback[0](s, state, me, users, channels, msg)
            if callback[1]:
                # Remove single-use callbacks after use.
                irc_callbacks[msg.cmd].remove(callback)
    except KeyError:
        pass


def handle_incoming_line(
    s: socket.socket,
    state: State,
    me: User,
    users: dict[bytes, User],
    channels: dict[bytes, Channel],
    m: bytes,
) -> None:
    print(">", m.decode("utf-8", "surrogateescape"))
    parsed: tuple[
        bytes, tuple[Optional[bytes], Optional[bytes], Optional[bytes]], list[bytes]
    ] = parse_message(m)
    source: Optional[User] # wow, random type declaration sticking out of nowhere, great Python style
    try:
        source = users[parsed[1][0].lower()] if parsed[1][0] else None
    except KeyError:
        assert parsed[1][0] # why are we asserting this again, what if it's some server that's snoting it
        source = User(nick=parsed[1][0])
        users[parsed[1][0].lower()] = source

    if source:
        # These assignments are to update the ident and the host from incoming messages to users in our database, though this may be a bit redundent to do every time.
        source.ident = parsed[1][1]
        source.host = parsed[1][2]
        source.last_activity_time = time.time()
        source.last_activity = m
    msg = Message(parsed[0].upper(), source, parsed[2])

    handle_incoming_message(s, state, me, users, channels, msg)


def main() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER, PORT))

    me = User(nick=NICK)
    users: dict[bytes, User] = {NICK: me}
    channels: dict[bytes, Channel] = {}
    for channel_name in CHANNELS:
        channels[channel_name] = Channel(name=channel_name, joined=None)
    state = State()

    send(s, b"CAP", b"LS", b"302")

    # if LOGIN and PASSWORD:
    #     send(s, b"PASS", LOGIN + b":" + PASSWORD)
    # elif LOGIN or PASSWORD:
    #     print(
    #         "[-] Login and password must be both set to authenticate", file=sys.stderr
    #     )
    #     sys.exit(2)
    send(s, b"NICK", NICK)
    send(s, b"USER", IDENT, b"0", b"0", GECOS)

    recv_msg: bytes = b""
    while True:

        new_recv_msg: bytes = s.recv(512)
        if new_recv_msg == b"":
            sys.exit(0)
        recv_msg += new_recv_msg
        split_recv_msg: list[bytes] = recv_msg.split(b"\r\n")
        if len(split_recv_msg) < 2:
            continue
        for m in split_recv_msg[0:-1]:
            handle_incoming_line(s, state, me, users, channels, m)
        recv_msg = split_recv_msg[-1]


if __name__ == "__main__":
    main()
