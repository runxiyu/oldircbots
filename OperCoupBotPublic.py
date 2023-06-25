#!/usr/bin/env python3

import socket
import ssl

context = ssl.create_default_context()

s = context.wrap_socket(
    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
    server_hostname="irc.andrewyu.org",
)

s.connect(("irc.andrewyu.org", 6697))

s.sendall(b"USER CoupBot CoupBot CoupBot :CoupBot\r\nNICK CoupBot\r\n")

while True:
    msg = s.recv(512)
    while not msg.endswith(b"\r\n"):
        newmsg = s.recv(512)
        if newmsg == b"":
            print("Error: disconnected.")
            exit()
        msg = msg + newmsg
    for line in [line for line in msg.split(b"\r\n") if line != b""]:
        print(line)

        source = b""
        lastarg = b""
        if line.startswith(b":"):
            source = line.split(b" ")[0][1:]
            line = b" ".join(line.split(b" ")[1:])

        command = line.split(b" ")[0]
        line = b" ".join(line.split(b" ")[1:])

        if line.startswith(b":"):
            line = b" " + line
        if len(line.split(b" :")) > 1:
            lastarg = b" :".join(line.split(b" :")[1:])
            line = line.split(b" :")[0]

        args = line.split(b" ")
        if args == [b""]:
            args = []

        print([source, command, args, lastarg])

        if command == b"PING":
            if lastarg == b"":
                if args == []:
                    s.sendall(b"PONG\r\n")
                else:
                    s.sendall(b"PONG " + b" ".join(args) + b"\r\n")
            else:
                if args == []:
                    s.sendall(b"PONG :" + lastarg + b"\r\n")
                else:
                    s.sendall(b"PONG " + b" ".join(args) + b" :" + lastarg + b"\r\n")
        elif command == b"376":
            s.sendall(b"OPER <insert oper stuff here>\r\n")  # EDIT
            s.sendall(b"MODE CoupBot +p\r\n")
            s.sendall(b"JOIN #LibreIRC\r\n")
        elif command == b"WALLOPS":
            if lastarg.startswith(b"OPER: \x02"):
                name = lastarg.split(b"\x02")[1]
                print(b"OPER detected: " + name + b".")
                if name != b"CoupBot":
                    print(b"Killing " + name + b"...")
                    s.sendall(b"KILL " + name + b" :COUP\r\n")
            elif lastarg.startswith(b"SOPER"):
                name = (lastarg.split(b"\x02")[1]).split(b" ")[0]
                print(b"SOPER detected: " + name + b".")
                print(b"Killing " + name + b"...")
                s.sendall(b"KILL " + name + b" :COUP\r\n")
