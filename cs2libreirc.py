ip = "irc.andrewyu.org"
port = 6697
nick = "Guard"
ident = nick
realname = "git://git.andrewyu.org/ircbots"
#identity = open("idents").read()
identity = ""
debug = True
channels = ["#discard", "#libresociety", "#libreirc", "#fsi"]
prefix = "?"
chandata = {
    "#fsi": {
        "Andrew!Andrew@libreirc/staff/Andrew": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        },
    },
    "#discard": {
        "Andrew!Andrew@libreirc/staff/Andrew": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        },
    },
    "#libreirc": {
        "Andrew!Andrew@libreirc/staff/Andrew": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        }
    },
    "#libresociety": {
        "Andrew!Andrew@libreirc/staff/Andrew": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        }
    },
}
chaneww = {"#discard": {}, "#libreirc": {}, "#libresociety": {}, "#fsi": {}}
