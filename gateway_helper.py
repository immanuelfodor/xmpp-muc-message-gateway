import json
import yaml


def error_handler(code):
    """
    Create a new Flask error handler dynamically. Returns the given error code and
    a lambda function in a tuple which can be unpacked with * upon registering

    :param: code int
    :return: int, lambda
    """

    return code, lambda e: (jsonify(error=str(e)), code)


def parse_known_rooms(rooms):
    """
    Parse a known rooms string (token:room@conf.host:nick [...]) to a Python dictionary
    Keys are tokens, values are nested dicts of room JIDs and associated user nicks

    :param: rooms string
    :return: dict
    """

    known_rooms = {}

    for pairs in rooms.split(' '):
        valid_token, valid_room, nick = pairs.split(':')
        known_rooms[valid_token] = {'room': valid_room, 'nick': nick}

    return known_rooms


def format_message(msg_format, request_json):
    """
    Prepares the incoming request JSON object for the XMPP forward

    :param: msg_format string
    :param: request_json dict
    :return: string
    """

    if msg_format == 'json':
        return json.dumps(request_json, indent=2)  # ensure_ascii=False allows unicode chars
    if msg_format == 'yaml':
        return yaml.dump(request_json, indent=2, allow_unicode=True)

    raise EnvironmentError
