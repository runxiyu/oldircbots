@module.rule(
    ".*(supernets.org|▄.*▄|#superbowl|williampitcock|#.s.u.p.e.r.b.o.w.l|GOT.NO.COOCHIE|<@.+<@.+<@.+|noobfarm)"
)
def globaln00bz(bot, trigger):
    if len(trigger) > 1 and (
        (trigger[0] == "<" and (trigger[1].isalnum() or trigger[1] == "\x03"))
        or trigger.startswith("\x02[")
    ):
        return
#    if trigger.nick.lower() in servers:
#        n = trigger.split(" ", 2)
#        if n[0] in ("*", "***") and len(n) > 1:
#            if n[0] == "***" and n[-1] == "left the game":
#                return
#            victim = n[1]
#        elif n[0].startswith("<") and n[0].endswith(">") and n[0][1].isalnum():
#            victim = n[0][1:-1]
#        else:
#            return
#
#        bot.reply(
#            "cmd kick {} Spamming is off-topic on {}.".format(victim, trigger.nick)
#        )
    if trigger.is_privmsg or bot.privileges[trigger.sender][bot.nick] < HALFOP:
        return bot.reply(
            "Hey, stop that! We have enough n00bz here to deal with without you!"
        )
    else:
        bot.write(
            ["KICK", trigger.sender, trigger.nick],
            "Spamming is off-topic on {}.".format(trigger.sender),
        )
