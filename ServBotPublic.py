#!/usr/bin/env python3

import threading
import socket
import math
import time
import ssl
import sys

send_password = b""
accept_password = b""

trusted_IDs = [[b"hax", b"173.249.27.223"], [b"Andrew", b"173.249.27.223"]]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(("irc.andrewyu.org", 6666))

s.sendall(
    b"PASS "
    + send_password
    + b" TS 6 1HC\r\nCAPAB BAN CHW CLUSTER ECHO ENCAP EOPMOD EUID EX IE KLN KNOCK MLOCK QS RSFNC SAVE SERVICES TB UNKLN\r\nSERVER coup.irc.andrewyu.org 0 :Coup Serv\r\nSVINFO 6 6 0 :"
    + str(time.time()).encode("UTF-8")
    + b"\r\n"
)

msg = b""

connected_server = b""

servlist = {}
userlist = {}
chanlist = {}


def read_and_send():
    for line in sys.stdin:
        try:
            s.sendall(line.encode("UTF-8"))
        except Exception:
            pass


threading.Thread(target=read_and_send, daemon=True).start()

while True:
    newmsg = s.recv(512)
    if newmsg == b"":
        break
    msg += newmsg
    split_msg = msg.split(b"\r\n")
    if len(split_msg) < 2:
        continue
    commands = split_msg[0:-1]
    msg = split_msg[-1]
    for command in commands:
        print(command)

        source = b""
        if command.startswith(b":"):
            source = command.split(b" ")[0][1:]
            command = b" ".join(command.split(b" ")[1:])

        lastarg = b" :".join(command.split(b" :")[1:])
        args = command.split(b" :")[0].split(b" ")[1:]
        args.append(lastarg)
        command = command.split(b" :")[0].split(b" ")[0]

        if command.upper() == b"PING":
            try:
                s.sendall(args[1] + b" PONG " + args[0] + b"\r\n")
            except IndexError:
                s.sendall(b":1HC PONG " + args[0] + b"\r\n")
        elif command.upper() == b"PASS":
            if source != b"":
                print("Received PASS from another source!")
                continue
            if connected_server != b"":
                print("Received PASS from the server more than once!")
                continue
            if args[0] != accept_password:
                print("Invalid password given by the server!")
                exit()
            connected_server = args[3]
        elif command.upper() == b"SERVER":
            if source != b"":
                print("Received SERVER from another source!")
                continue
            if connected_server == b"":
                print("Server sent SERVER before PASS!")
                exit()
            servlist[connected_server] = {
                "server name": args[0],
                "hopcount": args[1],
                "server description": args[2],
            }

            s.sendall(
                b"EUID CoupServ 0 "
                + str(math.floor(time.time())).encode("UTF-8")
                + b" +SZio CoupServ hax/CoupServ 127.0.0.1 1HC000001 localhost * :CoupServ\r\n:1HC000001 OPER CoupServ admin\r\n"
            )
            s.sendall(
                b"EUID SpamServ 0 "
                + str(math.floor(time.time())).encode("UTF-8")
                + b" +Zi SpamServ hax/SpamServ 0.0.0.0 1HC000002 0.0.0.0 * :SpamServ\r\n"
            )
        elif command.upper() == b"SID":
            servlist[args[2]] = {
                "server name": args[0],
                "hopcount": args[1],
                "server description": args[3],
            }
        elif command.upper() == b"EUID":
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
            }
        elif command.upper() == b"SJOIN":
            chanlist[args[1]] = {
                "channelTS": args[0],
                "simple modes": args[2],
                "mode params": args[3:-1],
                "nicklist": {},
            }
            for uid in args[-1].split(b" "):
                mode = {"@": False, "+": False}
                if uid.startswith(b"@"):
                    mode["@"] = True
                    uid = uid[1:]
                if uid.startswith(b"+"):
                    mode["+"] = True
                    uid = uid[1:]
                chanlist[args[1]]["nicklist"][uid] = mode
            s.sendall(
                b":1HC000001 JOIN "
                + str(time.time()).encode("UTF-8")
                + b" "
                + args[1]
                + b" +\r\n:1HC MODE "
                + args[1]
                + b" +ov 1HC000001 1HC000001\r\n"
            )
        elif command.upper() == b"NICK":
            if len(source) == 9:
                userlist[source]["nickname"] = args[0]
                userlist[source]["nickTS"] = args[1]
        elif command.upper() == b"QUIT":
            try:
                del userlist[source]
            except KeyError:
                continue
            for channel in chanlist:
                try:
                    del chanlist[channel]["nicklist"][source]
                except KeyError:
                    pass
        elif command.upper() == b"KILL":
            try:
                del userlist[args[0]]
            except KeyError:
                continue
            for channel in chanlist:
                try:
                    del chanlist[channel]["nicklist"][args[0]]
                except KeyError:
                    pass
        elif command.upper() == b"TMODE":
            if int(args[0].decode("UTF-8")) <= int(
                chanlist[args[1]]["channelTS"].decode("UTF-8")
            ):
                dir = b"-"
                for i in range(0, len(args[2])):
                    if args[2][i : i + 1] == b"+":
                        dir = b"+"
                    elif args[2][i : i + 1] == b"-":
                        dir = b"-"
                    elif args[2][i : i + 1] == b"o":
                        try:
                            chanlist[args[1]]["nicklist"][args[3]]["@"] = dir == b"+"
                        except KeyError:
                            pass
                        del args[3]
                    elif args[2][i : i + 1] == b"v":
                        try:
                            chanlist[args[1]]["nicklist"][args[3]]["+"] = dir == b"+"
                        except KeyError:
                            pass
                        del args[3]
                    elif args[2][i : i + 1] in [
                        b"e",
                        b"I",
                        b"b",
                        b"q",
                        b"k",
                        b"f",
                        b"l",
                        b"j",
                    ]:
                        del args[3]
        elif command.upper() == b"JOIN":
            if len(args) == 1:
                if args[0] == b"0":
                    for channel in chanlist:
                        try:
                            del chanlist[channel]["nicklist"][source]
                        except KeyError:
                            pass
            else:
                chanlist[args[1]]["nicklist"][source] = {"@": False, "+": False}
        elif command.upper() == b"PRIVMSG":
            if [
                userlist[source]["username"],
                userlist[source]["IP address"],
            ] in trusted_IDs:
                if args[0] == b"1HC000001" or (
                    args[0].startswith(b"#") and args[1].startswith(b"-")
                ):
                    if args[0] != b"1HC000001":
                        args[1] = args[1][1:]

                    if args[1] == b"print userlist":
                        print(userlist)
                    elif args[1] == b"print chanlist":
                        print(chanlist)
                    elif args[1] == b"print servlist":
                        print(servlist)
                    elif args[1].startswith(b"join "):
                        s.sendall(
                            b":1HC000001 JOIN "
                            + str(time.time()).encode("UTF-8")
                            + b" "
                            + args[1].split(b" ")[1]
                            + b" +\r\n"
                        )
                    elif args[1].startswith(b"sanick "):
                        current = args[1].split(b" ")[1]
                        target = args[1].split(b" ")[2]
                        for id in userlist:
                            if userlist[id]["nickname"] == current:
                                current = id
                                break
                        try:
                            s.sendall(
                                b":1HC ENCAP * RSFNC "
                                + current
                                + b" "
                                + target
                                + b" "
                                + str(math.floor(time.time())).encode("UTF-8")
                                + b" :"
                                + userlist[current]["nickTS"]
                                + b"\r\n"
                            )
                        except KeyError:
                            continue
                    elif args[1].startswith(b"coup "):  # temp disabled
                        chan = args[1].split(b" ")[1]
                        modechanges = []
                        for user in chanlist[chan]["nicklist"]:
                            if [
                                userlist[user]["username"],
                                userlist[user]["IP address"],
                            ] in trusted_IDs:
                                if not chanlist[chan]["nicklist"][user]["@"]:
                                    chanlist[chan]["nicklist"][user]["@"] = True
                                    modechanges.append([b"+", b"o", user])
                            else:
                                if chanlist[chan]["nicklist"][user]["@"]:
                                    chanlist[chan]["nicklist"][user]["@"] = False
                                    modechanges.append([b"-", b"o", user])

                        while len(modechanges) > 0:
                            modechange = [b" "]
                            dir = b""
                            for change in modechanges[:4]:
                                if change[0] != dir:
                                    modechange[0] += change[0]
                                    dir = change[0]
                                modechange[0] += change[1]
                                modechange.append(change[2])
                            s.sendall(
                                b":1HC000001 MODE "
                                + chan
                                + b" ".join(modechange)
                                + b"\r\n"
                            )
                            modechanges = modechanges[4:]
                    elif args[1].startswith(b"spam "):
                        chan = args[1].split(b" ")[1]
                        s.sendall(
                            b":1HC000002 JOIN "
                            + str(time.time()).encode("UTF-8")
                            + b" "
                            + chan
                            + b" +\r\n"
                        )
                        for _ in range(1000):
                            s.sendall(
                                b":1HC000002 PRIVMSG "
                                + chan
                                + b" :\x02\x03\x04\x05\x06\x07YAY SPAMMY SPAM https://users.andrewyu.org/~hax\r\n"
                            )
                        s.sendall(b":1HC000002 PART " + chan + b"\r\n")
                    elif args[1].startswith(b":"):
                        s.sendall(args[1] + b"\r\n")
