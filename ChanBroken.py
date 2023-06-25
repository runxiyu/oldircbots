#!/usr/bin/env python3

"""
Simple Channel Services for Internet Relay Chat
Copyright (C) 2022  Andrew Yu <https://www.andrewyu.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import socket
import threading
import time
import ssl
import sys
import subprocess


ENCODING = "utf-8"
SERVER = "irc.libera.chat"
NICK = "GuardianDevil"
IDENT = "GuardianDevil"
GECOS = "Channel Services"
CHANNELS = ["#librespeech", "##gnuhackers"]
PREFIX = "&"

trusted = [NICK, "Andrew", "leah", "LibreBot"]

e = lambda s: s.encode(ENCODING)
d = lambda b: b.decode(ENCODING)


def t(s, t):
    print("[T] " + t)
    s.sendall(e(t + "\r\n"))


def err(s, t=""):
    print(s, t, file=sys.stderr)


def errl(s):
    print(s, file=sys.stderr, end="")


def run():
    joined = False
    ready = False
    authenticated = False
    joined = False
    joining = False

    chanmodes = []
    statusmodes = []

    errl("[*] Creating SSL context...")
    ssl_context = ssl.create_default_context()
    err(" done.")

    errl("[*] Creating socket...")
    s = ssl_context.wrap_socket(
        socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=SERVER
    )
    err(" done.")

    errl("[*] Connecting...")
    s.connect((SERVER, 6697))
    err(" done.")

    errl("[*] Registering...")
    t(s, f"NICK {NICK}")
    t(s, f"USER {IDENT} {IDENT} {IDENT} :{GECOS}")
    err(" done.")

    while True:
        err(72 * "-")
        errl("[*] Fetching a line...")
        msg = d(s.recv(512))
        err(" done.")
        err("[*] msg:", msg)
        while not msg.endswith("\r\n"):
            errl("[*] The line didn't end with \\r\\n, fetching more...")
            moremsg = d(s.recv(512))
            err(" done.")
            err("[*] moremsg:", moremsg)
            if moremsg == "":
                err("[!] Socket closed.")
                return
            msg = msg + moremsg
            err("[*] msg + moremsg:", msg)
        print("[R] " + msg)
        for line in [l for l in msg.split("\r\n") if l != ""]:
            err("[*] line:", line)
            segs = line.split(" ")
            err("[*] segs:", segs)

            if not ready:
                if not authenticated:
                    errl("[*] Authenticating...")
                    process = subprocess.Popen(
                        ["pass", "IRC:Libera:NickServ:LibreBot"], stdout=subprocess.PIPE
                    )
                    t(s, "PRIVMSG NickServ :IDENTIFY Guard " + d(process.stdout.read()))
                    err(" complete.")
                    authenticated = True
                if not joined and not joining:
                    errl("[*] Joining channels...")
                    for c in CHANNELS:
                        t(s, "JOIN " + c)
                    err(" sent.")
                    joining = True

            hostmask = ""
            lastarg = ""
            if line.startswith(":"):
                err("[*] The line I got starts with a colon.")
                hostmask = segs[0][1:]
                err("[*] hostmask:", hostmask)
                line = " ".join(segs[1:])
                err("[*] updated line:", line)

            err("[*] updated line:", line)
            segs = line.split(" ")
            err("[*] updated segs:", segs)

            command = segs[0]
            err("[*] command:", command)
            line = " ".join(segs[1:])
            err("[*] updated line:", line)
            segs = line.split(" ")
            err("[*] updated segs:", segs)

            if line.startswith(":"):
                err("[*] line now starts with a colon.")
                line = " " + line
                err("[*] updated line:", line)
            if len(line.split(" :")) > 1:
                err("[*] The line still has other arguments left.")
                lastarg = " :".join(line.split(" :")[1:])
                err("[*] lastarg:", lastarg)
                line = line.split(" :")[0]
                err("[*] updated line:", line)

            args = line.split(" ")
            err("[*] extra args:", args)
            if args == [""]:
                args = []
            err("[*] updated extra args:", args)
            if lastarg != "":
                args.append(lastarg)
            err("[*] updated args:", args)

            if command == "PING":
                t(s, "PONG " + " ".join(args))
            elif command == "005":
                for arg in args:
                    if arg.startswith("CHANMODES="):
                        arg = arg[10:]
                        for section in arg.split(",")[0:3]:
                            for i in range(0, len(section)):
                                chanmodes.append(section[i : i + 1])
                    elif arg.startswith("PREFIX="):
                        arg = (arg.split("(")[1]).split(")")[0]
                        for i in range(0, len(arg)):
                            chanmodes.append(arg[i : i + 1])
                            statusmodes.append(arg[i : i + 1])
            elif command == "376":
                ready = True
                err("[+] Connected.")
            elif command == "MODE":
                err("[*] I got a MODE.")
                target = args.pop(0)
                err("[*] target:", target)
                modes = args.pop(0)
                err("[*] modes:", modes)
                dir = "-"
                err("[*] dir (default):", dir)
                if target.lower() in [c.lower() for c in CHANNELS]:
                    err("[*] The MODE change happened in a channel I look after.")
                    for i in range(0, len(modes)):
                        if modes[i] == "+":
                            dir = "+"
                            err("[*] dir:", dir)
                        elif modes[i] == "-":
                            dir = "-"
                            err("[*] dir:", dir)
                        else:
                            err("[*] chanmodes:", chanmodes)
                            if modes[i] in chanmodes:
                                err("[*] A MODE change affected a channel mode.")
                                err("[*] args:", args)
                                arg = args.pop(0)
                                err("[*] arg:", arg)
                                if modes[i] in statusmodes:
                                    err(
                                        "[*] A MODE change affected a user's channel status."
                                    )
                                    if arg not in trusted and dir == "+":
                                        err(
                                            "[*] A channel status was added to a untrusted user."
                                        )
                                        t(
                                            s,
                                            "MODE "
                                            + target
                                            + " -"
                                            + modes[i : i + 1]
                                            + " "
                                            + arg,
                                        )
                                    elif (arg in trusted) and dir == "-":
                                        err(
                                            "[*] A channel status was removed from a trusted user."
                                        )
                                        t(
                                            s,
                                            "MODE "
                                            + target
                                            + " +"
                                            + modes[i : i + 1]
                                            + " "
                                            + arg,
                                        )
                                elif modes[i] == "b" and dir == "+":
                                    err("[*] I'm the only client to ban!")
                                    t(s, "MODE " + target + " -b " + arg)
                                if hostmask.split("!")[0] not in trusted:
                                    err(
                                        "[*] The mode change came from an untrusted user."
                                    )
                                    t(
                                        s,
                                        "MODE "
                                        + target
                                        + " -o "
                                        + hostmask.split("!")[0],
                                    )
            elif command == "JOIN":
                err("[*] Someone joined a channel.")
                if lastarg != "":
                    args.append(lastarg)
                if args[0] == target:
                    if hostmask.split("!")[0] == NICK:
                        err("[*] I joined the channel!")
                        joined = True
                    elif hostmask.split("!")[0] in trusted:
                        for mode in statusmodes:
                            t(
                                s,
                                "MODE "
                                + target
                                + " +"
                                + mode
                                + " "
                                + hostmask.split("!")[0],
                            )
            elif command == "KICK":
                if lastarg != "":
                    args.append(lastarg)
                if args[0] in CHANNELS:
                    channel = args[0]
                    if args[1] == NICK:
                        joined = False
                        t(s, "JOIN " + channel)
                    elif args[1] in trusted:
                        if hostmask.split("!")[0] not in trusted:
                            t(s, "MODE " + channel + " -o " + hostmask.split("!")[0])
            elif command == "PRIVMSG":
                if not lastarg.startswith(PREFIX): return
                sep = lastarg[1:].split(" ")
                err("[+] Got command:", sep)
                cmd = sep[0].lower()
                if cmd == "help":
                    t(s, "PRIVMSG " + args[0] + " :Guard is a ChanServ-like bot.  It is currently under heavy development.")

if __name__ == "__main__":
    run()
