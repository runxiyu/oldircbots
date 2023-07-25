#!/usr/bin/env python3

import threading
import socket
import time
import ssl

names = []

trusted = [b"Andrew", b"Noisytoot"]

channel = b"#librespeech"


def init(name):
    while True:
        run(name)


def run(name):
    global names

    chanmodes = []
    coupmodes = []

    context = ssl.create_default_context()

    joined = False
    ready = False

    s = context.wrap_socket(
        socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        server_hostname="irc.libera.chat",
    )

    s.connect(("irc.libera.chat", 6697))

    s.sendall(
        b"USER librespeech librespeech librespeech :librespeech\r\nNICK "
        + name
        + b"\r\n"
    )

    while True:
        msg = s.recv(512)
        while not msg.endswith(b"\r\n"):
            newmsg = s.recv(512)
            if newmsg == b"":
                global names
                print(
                    name.decode("UTF-8", "backslashreplace")
                    + " disconnected. Remaining: "
                    + str(names)
                )
                try:
                    names.remove(name)
                except ValueError:
                    pass
                return
            msg = msg + newmsg
        for line in [line for line in msg.split(b"\r\n") if line != b""]:
            if not joined and ready:
                s.sendall(b"JOIN " + channel + b"\r\n")

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
                        s.sendall(
                            b"PONG " + b" ".join(args) + b" :" + lastarg + b"\r\n"
                        )
            elif command == b"005":
                for arg in args:
                    if arg.startswith(b"CHANMODES="):
                        arg = arg[10:]
                        for section in arg.split(b",")[0:3]:
                            for i in range(0, len(section)):
                                chanmodes.append(section[i : i + 1])
                    elif arg.startswith(b"PREFIX="):
                        arg = (arg.split(b"(")[1]).split(b")")[0]
                        for i in range(0, len(arg)):
                            chanmodes.append(arg[i : i + 1])
                            coupmodes.append(arg[i : i + 1])
            elif command == b"376":
                ready = True
                # 				s.sendall(b"OPER <insert oper stuff here>\r\n") #EDIT
                s.sendall(b"MODE " + name + b" +p\r\n")
                names.append(name)
                print(
                    name.decode("UTF-8", "backslashreplace")
                    + " connected. Connected clients: "
                    + str(names)
                )
            elif command == b"MODE":
                if lastarg != b"":
                    args.append(lastarg)
                target = args[0]
                del args[0]
                modes = args[0]
                del args[0]
                dir = b"-"
                if target == channel:
                    for i in range(0, len(modes)):
                        if modes[i : i + 1] == b"+":
                            dir = b"+"
                        elif modes[i : i + 1] == b"-":
                            dir = b"-"
                        else:
                            if modes[i : i + 1] in chanmodes:
                                arg = args[0]
                                del args[0]
                                if modes[i : i + 1] in coupmodes:
                                    if (
                                        arg not in names
                                        and arg not in trusted
                                        and dir == b"+"
                                    ):
                                        s.sendall(
                                            b"MODE "
                                            + channel
                                            + b" -"
                                            + modes[i : i + 1]
                                            + b" "
                                            + arg
                                            + b"\r\n"
                                        )
                                        if (
                                            source.split(b"!")[0] not in trusted
                                            and source.split(b"!")[0] not in names
                                        ):
                                            s.sendall(
                                                b"KICK "
                                                + channel
                                                + b" "
                                                + source.split(b"!")[0]
                                                + b" :COUP\r\n"
                                            )
                                    elif (
                                        arg in names or arg in trusted
                                    ) and dir == b"-":
                                        s.sendall(
                                            b"MODE "
                                            + channel
                                            + b" +"
                                            + modes[i : i + 1]
                                            + b" "
                                            + arg
                                            + b"\r\n"
                                        )
                                        if (
                                            source.split(b"!")[0] not in trusted
                                            and source.split(b"!")[0] not in names
                                        ):
                                            s.sendall(
                                                b"KICK "
                                                + channel
                                                + b" "
                                                + source.split(b"!")[0]
                                                + b" :COUP\r\n"
                                            )
                                elif modes[i : i + 1] == b"b" and dir == b"+":
                                    s.sendall(
                                        b"MODE " + channel + b" -b " + arg + b"\r\n"
                                    )
                elif target == name:
                    for i in range(0, len(modes)):
                        if modes[i : i + 1] == b"+":
                            dir = b"+"
                        elif modes[i : i + 1] == b"-":
                            dir = b"-"
                        else:
                            if modes[i : i + 1] == b"o" and dir == b"-":
                                s.sendall(
                                    b"OPER <insert oper stuff here>\r\nMODE "
                                    + name
                                    + b" +p\r\n"
                                )  # EDIT
                            elif modes[i : i + 1] == b"p" and dir == b"-":
                                s.sendall(b"MODE " + name + b" +p\r\n")
            elif command == b"JOIN":
                if lastarg != b"":
                    args.append(lastarg)
                if args[0] == channel:
                    if source.split(b"!")[0] == name:
                        joined = True
                    elif (
                        source.split(b"!")[0] in names
                        or source.split(b"!")[0] in trusted
                    ):
                        for mode in coupmodes:
                            s.sendall(
                                b"MODE "
                                + channel
                                + b" +"
                                + mode
                                + b" "
                                + source.split(b"!")[0]
                                + b"\r\n"
                            )
            elif command == b"KICK":
                if lastarg != b"":
                    args.append(lastarg)
                if args[0] == channel:
                    if args[1] == name:
                        s.sendall(b"JOIN " + channel + b"\r\n")
                        joined = False
                    elif args[1] in names or args[1] in trusted:
                        if (
                            source.split(b"!")[0] not in names
                            and source.split(b"!")[0] not in trusted
                        ):
                            s.sendall(
                                b"KICK "
                                + channel
                                + b" "
                                + source.split(b"!")[0]
                                + b" :COUP\r\n"
                            )


for i in range(0, 3):
    print("Starting librespeech" + str(i) + "...")
    threading.Thread(
        target=init, args=(b"librespeech" + str(i).encode("UTF-8"),)
    ).start()
    time.sleep(3)

print("All clients started.")
