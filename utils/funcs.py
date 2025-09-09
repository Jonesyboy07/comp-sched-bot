import json
from os import path

def CheckIfBotChannel(channel_id, guild_id):
    filename = "data/servers.json"
    if not path.exists(filename):
        return False
    data = ReadJSON(filename)
    if str(guild_id) in data:
        return str(channel_id) in data[str(guild_id)]["bot_channels"]
    else:
        return False

def CheckIfAdminRole(role_ids, guild_id):
    filename = "data/servers.json"
    if not path.exists(filename):
        return False
    data = ReadJSON(filename)
    if str(guild_id) in data:
        for role_id in role_ids:
            if str(role_id) in data[str(guild_id)]["admin_roles"]:
                return True
    return False

def ReadJSON(filename):
    with open(filename, 'r') as f:
        return json.load(f)
