import json
from os import path

def CheckIfBotChannel(channel_id, guild_id):
    """Check the Server JSON to see if the given channel ID is a bot channel.

    Args:
        channel_id (int): Channel ID that command was ran in.
        guild_id (int): The guild/server ID to check.

    Returns:
        bool: If the channel is a bot channel (True) or not (False).
    """
    filename = "data/servers.json"
    if not path.exists(filename):
        return False
    data = ReadJSON(filename)
    if str(guild_id) in data:
        return str(channel_id) in data[str(guild_id)]["bot_channels"]
    else:
        return False

def CheckIfAdminRole(role_ids, guild_id):
    """Check the Server JSON to see if any of the given role IDs are admin roles.

    Args:
        role_ids (array[int]): The role ID's of the user to check.
        guild_id (int): The guild/server ID to check.

    Returns:
        bool: The result of the check (True if any role ID is an admin role, False otherwise).
    """
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
    """Read a **JSON** file and **return** the data.

    Args:
        filename (Path): The file to read.

    Returns:
        **JSON**: The contents of the file as JSON.
    """
    with open(filename, 'r') as f:
        return json.load(f)

def WriteJSON(data, filename, indent=4):
    """Write **data** to a JSON file, with specified indentation.

    Args:
        filename (path): The file to write to.
        data (json): The JSON data to write.
        indent (int, optional): The indentation to use. Defaults to 4.
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=indent)