ip = "irc.libera.chat"
port = 6697
nick = "ChanGuard"
ident = nick
realname = "git://git.andrewyu.org/ircbots"
identity = open("idents").read()
debug = True
channels = ["#librespeech", "##libresociety", "#fsi"]
prefix = "?"
chandata = {
    "#librespeech": {
        "werdnA!andrew@andrewyu.org": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        },
        "Andrew!Andrew@user/AndrewYu": {
            "ban",
            "op",
            "autoop",
            "flags",
            "invite",
            "voice",
            "exempt",
            "quiet",
        },
        "leah!~leah@libreboot/developer/leah": {
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
    "#fsi": {
        "Andrew!Andrew@user/AndrewYu": {
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
    "##libresociety": {
        "Andrew!Andrew@user/AndrewYu": {
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
chaneww = {"#librespeech": {}, "#fsi": {}, "##libresociety": {}}
