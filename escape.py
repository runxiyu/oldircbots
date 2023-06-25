#!/usr/bin/python3


import miniirc, sys, ast

assert miniirc.ver >= (1, 4, 0), "This bot requires miniirc >= v1.4.0."

# Variables
nick = "escape-witch"
ident = nick
realname = "i break your terminal haha"
identity = None
# identity = '<username> <password>'
debug = False
channels = ["#librespeech", "#botwar"]
prefix = "`"

ip = "irc.libera.chat"
port = 6697

# Welcome!
print("Welcome to {}!".format(nick), file=sys.stderr)
irc = miniirc.IRC(
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

# Handle normal messages
# This could probably be better than a large if/else statement.
@irc.Handler("PRIVMSG", colon=False)
def handle_privmsg(irc, hostmask, args):
    channel = args[0]
    text = args[-1].split(" ")
    cmd = text[0].lower()
    if not channel.startswith("#"): return
    if cmd.startswith(prefix):
        # Prefixed commands
        cmd = cmd[len(prefix) :]
        if cmd == "eval":
            try:
                irc.msg(channel, str(ast.literal_eval(' '.join(text[1:]))))
            except ValueError:
                irc.send("KICK", channel, hostmask[0], "sussy baka")
            except SyntaxError:
                irc.send("KICK", channel, hostmask[0], "do I look like I enjoy invalid syntax")
            except Exception as e:
                irc.msg(channel, f"{hostmask[0]}: {type(e).__name__}: {str(e)}")


# Connect
if __name__ == "__main__":
    irc.connect()
