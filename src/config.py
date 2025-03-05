from configobj import ConfigObj

config = ConfigObj("config.ini")


def reload():
    config.reload()
