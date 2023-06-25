#!/usr/bin/python3

# Bot to keep track of people who play a specific game
# Public domain

import miniirc
import sys
import json
import time
import os
from pprint import pprint

with open("lgmdata.json", "r") as f:
    data = json.load(f)

try:
    pprint(data["games"])
except KeyError:
    data["games"] = {}


assert miniirc.ver >= (1, 8, 1), "This bot requires miniirc >= v1.8.1."

nick = "LibreGameMatch"
ident = "game"
realname = "Player tracker and pinger for LibreGameNight"
identity = None
# identity = '<username> <password>'
debug = True
channels = ["#libregaming-matchmaking", "#botwar"]
prefix = "."

ip = "irc.libera.chat"
port = 6697

print("Welcome to {}!".format(nick), file=sys.stderr)
irc = miniirc.IRC(
    ip,
    port,
    nick,
    channels,
    ident=ident,
    realname=realname,
    ns_identity=identity,
    debug=debug and (lambda line: print(repr(line))),
    auto_connect=False,
)

@irc.Handler("PRIVMSG", colon=False)
def handle_privmsg(irc, hostmask, args):
    channel = args[0]
    if not channel.startswith("#"):
        irc.notice(hostmask[0], "Error: This bot does not work with private messages.  You MUST use this bot in a channel.")
        return
    text = args[-1].split(" ")
    cmd = text[0].lower()
    if not cmd.startswith(prefix):
        return
    cmd = cmd[len(prefix) :]
    if cmd == "help":
        irc.msg(channel, f"{hostmask[0]}: \x02{nick}\x02 is a utility to track players games, and when requested by a member thereof, highlights all players of the said game.")
        irc.msg(channel, f"{hostmask[0]}: Available commands: help, join, match, players, and games.  All commands MUST be called in a channel with '.' (ASCII dot) as its prefix.")
    elif cmd == "join":
        try:
            data['games'][text[1].title()][hostmask[0]] = True
        except KeyError:
            data['games'][text[1].title()] = {hostmask[0]: True} # just use a dict... solves the multiple instances at the same time
            irc.msg(channel, f"{hostmask[0]}: You have created and joined the {text[1].title()} player list.")
        else:
            irc.msg(channel, f"{hostmask[0]}: You have joined the {text[1].title()} player list.")
        print(json.dumps(data, indent="\t", sort_keys=True))
    elif cmd == "part":
        try:
            irc.msg(channel, f"{hostmask[0]}: You have parted the {text[1].title()} player list.")
        except KeyError:
            irc.msg(channel, f"{hostmask[0]}: You are not in the {text[1].title()} player list, or the player list does not exist.")
        finally:
            del data["games"][text[1].title()][hostmask[0]]
    elif cmd == "match":
        irc.msg(channel, f"{', '.join([p for p in data['games'][text[1].title()] if p != hostmask[0]])}: Anyone ready for {text[1].title()}?  {hostmask[0]} has called a game.")
    elif cmd == "players":
        irc.notice(hostmask[0], f"[{channel}] These are the players in {text[1].title()}: {', '.join([p for p in data['games'][text[1].title()]])}.")
    elif cmd == "games":
        irc.msg(channel, f"{hostmask[0]}: The following games are available: {', '.join([g for g in data['games']])}.")
    else:
        if not (cmd == "" or "." in cmd):
            irc.notice(hostmask[0], f"[{channel}] Invalid {nick} command: {cmd}.  Use the .help command for more information.")


if __name__ == "__main__":
    irc.connect()
    try:
        irc.wait_until_disconnected()
        #while True:
        #    time.sleep(999999999999999999999999) # much better
    except KeyboardInterrupt:
        with open("lgmdata.tmp.json", "w") as f:
            json.dump(data, f, indent="\t", sort_keys=True)
        os.replace("lgmdata.tmp.json", "lgmdata.json")
        irc.disconnect()
