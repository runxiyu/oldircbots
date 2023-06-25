# configuration file


class server:
    sid = "12A"
    capabilities = "QS ENCAP EX IE CHW KNOCK SAVE EUID SERVICES RSFNC BAN CLUSTER ECHO EOPMOD EUID KLN MLOCK SAVE SERVICES TB UNKLN"
    name = "spec.irc.andrewyu.org"
    hopcount = "0"
    description = "Special Services"
    send_password = ""


class connection:
    host = "irc.andrewyu.org"
    port = 6666


class uplink:
    name = "irc.andrewyu.org"
    recv_password = ""


class logging:
    channel = "#services"
    flooders = "-b"
    debug = "+d"
    kill = "+k"
    generic = "+s"


class SigServ:
    nick = "SigServ"
    ip = "0.0.0.0"
    ident = "SigServ"
    host = "spec.irc.andrewyu.org"
    gecos = "Signal Services"
    channels = ["#idc", "#LibreIRC", "#spam"]
    flood_life = 60
    flood_permit = 31
    flood_ban = 120
    flood_msg = "No floods"
