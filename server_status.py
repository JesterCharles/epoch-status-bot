import asyncio
import socket
from datetime import datetime, timezone
from typing import Dict, Optional

SERVERS = {
    "Auth": {"host": "game.project-epoch.net", "port": 3724},
    "Kezan":        {"host": "game.project-epoch.net", "port": 8085},
    "Gurubashi":    {"host": "game.project-epoch.net", "port": 8086},
}

server_states: Dict[str, dict] = {}

async def check_server(host: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=3
        )
        print(f"Async socket check for {host}:{port}: OPEN")
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        print(f"Async socket check for {host}:{port}: CLOSED ({e})")
        return False

async def poll_servers():
    # Prepare all checks concurrently
    tasks = [check_server(info["host"], info["port"]) for info in SERVERS.values()]
    results = await asyncio.gather(*tasks)
    now_str = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M:%S UTC")
    for (name, info), current in zip(SERVERS.items(), results):
        previous = server_states.get(name, {}).get("online", None)
        if name not in server_states:
            server_states[name] = {
                "online": current,
                "lastOnline": None,
                "lastChange": now_str
            }
        elif current != previous:
            server_states[name]["lastOnline"] = previous
            server_states[name]["lastChange"] = now_str
            server_states[name]["online"] = current
    return server_states

# Example usage for testing
if __name__ == "__main__":
   async def main():
       while True:
           states = await poll_servers()
           print(states)
           await asyncio.sleep(15)
   asyncio.run(main())
