#!/usr/bin/env python3

"""
Something like Sigyn, but a TS6 server instead of a Limnoria bot!
Copyright (C) 2022  Andrew Yu <andrew@andrewyu.org>

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


Credits: Libera.Chat's ozone (took a lot of code from there)
"""

import ts6config
import socket
import time
import random
import re


def e(s):
    return s.encode("utf-8")


def d(b):
    return b.decode("utf-8", "replace")


def repetitions(s):
    # returns a list of (pattern,count), used to detect a repeated pattern inside a single string.
    r = re.compile(r"(.+?)\1+")
    for match in r.finditer(s):
        yield (match.group(1), len(match.group(0)) / len(match.group(1)))


def findPattern(text, minimalCount, minimalLength, minimalPercent):
    items = list(repetitions(text))
    size = len(text)
    candidates = []
    for item in items:
        (pattern, count) = item
        percent = (len(pattern) * count) / size * 100
        if len(pattern) > minimalLength:
            if count > minimalCount or percent > minimalPercent:
                candidates.append(pattern)
    candidates.sort(key=len, reverse=True)
    return None if len(candidates) == 0 else candidates[0]


def compareString(a, b):
    """return 0 to 1 float percent of similarity ( 0.85 seems to be a good average )"""
    if a == b:
        return 1
    sa, sb = set(a), set(b)
    n = len(sa.intersection(sb))
    if float(len(sa) + len(sb) - n) == 0:
        return 0
    jacc = n / float(len(sa) + len(sb) - n)
    return jacc


def largestString(s1, s2):
    """return largest pattern available in 2 strings"""
    # From https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python2
    # License: CC BY-SA
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest : x_longest]


def floatToGMT(t):
    f = None
    try:
        f = float(t)
    except:
        return None
    return time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime(f))


# # contains Chan instances
# channels = {}
# # contains Pattern instances
# patterns = {}
# # contains whowas requested for a short period of time
# whowas = {}
# # contains klines requested for a short period of time
# klines = {}
# # contains various TimeoutQueue for detection purpose
# # often it's [host] { with various TimeOutQueue and others elements }
# queues = {}
# ilines = {}
# throttled = False
# lastDefcon = False
# god = False
# mx = {}
# tokline = {}
# toklineresults = {}
# dlines = []
# invites = {}
# nicks = {}
# cleandomains = {}
# klinednicks = utils.structures.TimeoutQueue(86400*2)
# lastKlineOper = ''
# oldDlines = utils.structures.TimeoutQueue(86400*7)
#


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ts6config.connection.host, ts6config.connection.port))


def send(m):
    print(m)
    return s.sendall(e(m + "\r\n"))


send(f"PASS {ts6config.server.send_password} TS 6 :{ts6config.server.sid}")
send(f"CAPAB {ts6config.server.capabilities}")
send(
    f"SERVER {ts6config.server.name} {ts6config.server.hopcount} :{ts6config.server.description}"
)
send(f"SVINFO 6 6 0 {time.time()}")

msg = ""
connected_server = ""
servlist = {}
userlist = {}


def kline(source, duration, reason):
    save = 2 * int(duration)
    duration = str(duration)
    send(
        f":{ts6config.SigServ.uid} ENCAP * SNOTE k :{userlist[source]['nickname']} ({userlist[source]['username']}@{userlist[source]['visible hostname']}) from {userlist[source]['IP address']} klined for {str(duration)} because {reason}"
    )
    send(
        f":{ts6config.SigServ.uid} KILL {source} :{ts6config.server.name}!{ts6config.SigServ.host}!{ts6config.SigServ.ident}!{ts6config.SigServ.nick} ({reason})"
    )
    send(
        f":{ts6config.SigServ.uid} BAN K {userlist[source]['username']} {userlist[source]['IP address']} {time.time()} {duration} {save} * :{reason}"
    )


while True:
    newbytes = s.recv(512)
    if newbytes == b"":
        break
    newmsg = d(newbytes)
    msg += newmsg
    print(msg, end="")
    split_msg = msg.split("\r\n")
    if len(split_msg) < 2:
        continue
    commands = split_msg[0:-1]
    msg = split_msg[-1]
    for command in commands:
        source = ""
        if command.startswith(":"):
            source = command.split(" ")[0][1:]
            command = " ".join(command.split(" ")[1:])

        lastarg = " :".join(command.split(" :")[1:])
        args = command.split(" :")[0].split(" ")[1:]
        args.append(lastarg)
        command = command.split(" :")[0].split(" ")[0]

        # print([source, command, args],)

        if command.upper() == "PING":
            try:
                send("PONG " + args[0] + " " + args[1])
            except IndexError:
                send("PONG " + args[0])
        elif command.upper() == "PASS":
            if source != "":
                print("Received PASS from another source!", end="")
                continue
            if connected_server != "":
                print("Received PASS from the server more than once!", end="")
                continue
            if args[0] != ts6config.uplink.recv_password:
                print("Invalid password given by the server!", end="")
                exit()
            connected_server = args[3]
        elif command.upper() == "SERVER":
            if source != "":
                print("Received SERVER from another source!", end="")
                continue
            if connected_server == "":
                print("Server sent SERVER before PASS!", end="")
                exit()
            servlist[connected_server] = {
                "server name": args[0],
                "hopcount": args[1],
                "server description": args[2],
            }

            send(
                f"EUID {ts6config.SigServ.nick} 0 "
                + str(time.time())
                + f" +Sio {ts6config.SigServ.ident} {ts6config.SigServ.host} {ts6config.SigServ.ip} {ts6config.server.sid}000001 {ts6config.SigServ.realhost} * :{ts6config.SigServ.gecos}"
            )
            send(
                f":{ts6config.SigServ.uid} JOIN "
                + str(time.time())
                + f" {ts6config.logging.channel} +"
            )
            send(f":{ts6config.server.sid} MODE {ts6config.logging.channel} +o SigServ")
            for c in ts6config.SigServ.channels:
                send(f":{ts6config.SigServ.uid} JOIN " + str(time.time()) + f" {c} +")
                send(f":{ts6config.server.sid} MODE {c} +o SigServ")
        elif command.upper() == "SID":
            servlist[args[2]] = {
                "server name": args[0],
                "hopcount": args[1],
                "server description": args[3],
            }
        elif command.upper() == "EUID":
            userlist[args[7]] = {
                "nickname": args[0],
                "hopcount": args[1],
                "nickTS": args[2],
                "umodes": args[3],
                "username": args[4],
                "visible hostname": args[5],
                "IP address": args[6],
                "real hostname": args[8],
                "account name": args[9],
                "gecos": args[10],
                "history": [],
            }
        elif command.upper() == "PRIVMSG":
            text = args[-1]
            userlist[source]["history"].append((args[0], time.time(), text))
            t = text.lower()
            if "please ban me" == t:
                kline(source, ts6config.SigServ.askforban_duration, ts6config.SigServ.askforban_msg)
