import asyncio
import socket
import aiohttp
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
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] Async socket check for {host}:{port}: OPEN")
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] Async socket check for {host}:{port}: CLOSED ({e})")
        return False

async def poll_servers_socket():
    """Original direct socket connection method"""
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

async def check_servers_via_api():
    """Backup API method to check server status"""
    url = "https://epoch-status.info/api/trpc/post.getStatus?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract status from nested JSON structure
                    status_data = data[0]["result"]["data"]["json"]
                    
                    # Build response in same format as socket method
                    now_str = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M:%S UTC")
                    api_states = {
                        "Auth": {
                            "online": status_data["auth"],
                            "lastOnline": None,
                            "lastChange": now_str
                        },
                        "Kezan": {
                            "online": status_data["world1"],
                            "lastOnline": None,
                            "lastChange": now_str
                        },
                        "Gurubashi": {
                            "online": status_data["world2"],
                            "lastOnline": None,
                            "lastChange": now_str
                        }
                    }
                    
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"[{timestamp}] API check successful - Auth: {'ON' if status_data['auth'] else 'OFF'}, Kezan: {'ON' if status_data['world1'] else 'OFF'}, Gurubashi: {'ON' if status_data['world2'] else 'OFF'}")
                    
                    return api_states
                else:
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"[{timestamp}] API returned status code: {response.status}")
                    return None
    except Exception as e:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] API check failed: {e}")
        return None

async def poll_servers():
    """Main function with socket-first, API-fallback logic"""
    # Try socket method first
    socket_result = await poll_servers_socket()
    
    # Check if socket method got any world servers online (not just auth)
    world_servers_online = False
    if socket_result:
        kezan_online = socket_result.get("Kezan", {}).get("online", False)
        gurubashi_online = socket_result.get("Gurubashi", {}).get("online", False)
        world_servers_online = kezan_online or gurubashi_online
    
    # If we have world servers online via socket, use socket result
    if socket_result and world_servers_online:
        return socket_result
    
    # If socket method failed completely or only auth is online, try API backup
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if socket_result and not world_servers_online:
        print(f"[{timestamp}] Only auth server online via socket, trying API backup for world servers...")
    else:
        print(f"[{timestamp}] Socket method failed or no servers online, trying API backup...")
    
    api_result = await check_servers_via_api()
    if api_result:
        return api_result
    
    # If both methods fail, return the socket result (which may have offline servers)
    return socket_result

# Example usage for testing
if __name__ == "__main__":
   async def main():
       while True:
           timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
           states = await poll_servers()
           print(f"[{timestamp}] Server states: {states}")
           await asyncio.sleep(15)
   asyncio.run(main())