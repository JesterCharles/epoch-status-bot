import asyncio
import socket
import aiohttp
import os
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple
from db import Database

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
    """Main function - tries socket connections first, falls back to API if needed"""
    try:
        # Try socket method first
        socket_result = await poll_servers_socket()
        
        # Check if all servers appear offline - might indicate connection issues
        all_offline = all(not server_info.get("online", False) for server_info in socket_result.values())
        
        # Also check if only Auth is online (common scenario when worlds are down)
        auth_only = (socket_result.get("Auth", {}).get("online", False) and 
                    not socket_result.get("Kezan", {}).get("online", False) and
                    not socket_result.get("Gurubashi", {}).get("online", False))
        
        if all_offline or auth_only:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            if all_offline:
                print(f"[{timestamp}] All servers appear offline via socket, trying API fallback...")
            else:
                print(f"[{timestamp}] Only Auth server online via socket, trying API fallback...")
            
            # Try API as backup
            api_result = await check_servers_via_api()
            if api_result:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"[{timestamp}] Using API results as fallback")
                return api_result
            else:
                print(f"[{timestamp}] API fallback also failed, using socket results")
        
        return socket_result
        
    except Exception as e:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] Socket method failed ({e}), trying API fallback...")
        
        # If socket method completely fails, try API
        api_result = await check_servers_via_api()
        if api_result:
            return api_result
        else:
            # If both fail, return empty states
            print(f"[{timestamp}] Both socket and API methods failed")
            return {}

async def check_patch_updates() -> Tuple[bool, Optional[Dict], List[str]]:
    """
    Check for patch updates by comparing current manifest version and UID with stored values.
    Returns (has_updates, manifest_data, updated_files)
    """
    url = "https://updater.project-epoch.net/api/v2/manifest?environment=production"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    manifest = await response.json()
                    
                    # Use the same database file as the main bot
                    DATABASE_FILE = os.environ.get("DATABASE_FILE", "bot_settings.db")
                    db = Database(DATABASE_FILE)
                    
                    current_version = manifest.get("Version", "Unknown")
                    current_uid = manifest.get("Uid", "Unknown")
                    
                    # Check if version has changed
                    stored_version_info = db.get_stored_version()
                    has_updates = False
                    
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    if stored_version_info:
                        stored_version, stored_uid = stored_version_info
                        if stored_version != current_version or stored_uid != current_uid:
                            has_updates = True
                            print(f"[{timestamp}] PATCH UPDATE DETECTED:")
                            print(f"[{timestamp}]   Version: {stored_version} → {current_version}")
                            print(f"[{timestamp}]   UID: {stored_uid[:12]}... → {current_uid[:12]}...")
                            # Update stored version
                            db.update_version(current_version, current_uid)
                        else:
                            print(f"[{timestamp}] Patch check: No updates - Version {current_version} unchanged")
                    else:
                        # First time - store current version
                        has_updates = True
                        print(f"[{timestamp}] INITIAL PATCH SETUP:")
                        print(f"[{timestamp}]   Version: {current_version}")
                        print(f"[{timestamp}]   UID: {current_uid[:12]}...")
                        db.update_version(current_version, current_uid)
                    
                    # For compatibility, return empty list for updated_files since we're not tracking individual files anymore
                    updated_files = []
                    
                    return has_updates, manifest, updated_files
                    
                else:
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"[{timestamp}] Patch API returned status code: {response.status}")
                    return False, None, []
                    
    except Exception as e:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] Patch check failed: {e}")
        return False, None, []

async def get_current_patch_info() -> Optional[Dict]:
    """Get current patch information without checking for updates."""
    url = "https://updater.project-epoch.net/api/v2/manifest?environment=production"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] Failed to get patch info: {e}")
        return None

# Example usage for testing
if __name__ == "__main__":
   async def main():
       while True:
           timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
           states = await poll_servers()
           print(f"[{timestamp}] Server states: {states}")
           await asyncio.sleep(15)
   asyncio.run(main())