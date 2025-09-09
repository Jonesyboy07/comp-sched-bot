import os
import json

def EnsurePreReq():
    os.makedirs("data", exist_ok=True)

    # Ensure servers.json exists
    servers_path = "data/servers.json"
    if not os.path.exists(servers_path):
        with open(servers_path, "w") as f:
            json.dump({}, f, indent=4)

    # Ensure commands.json exists
    commands_path = "data/commands.json"
    if not os.path.exists(commands_path):
        with open(commands_path, "w") as f:
            json.dump({
                "sections": [
                    {
                        "name": "Setup",
                        "commands": []
                    },
                    {
                        "name": "General",
                        "commands": []
                    }
                ]
            }, f, indent=4)



