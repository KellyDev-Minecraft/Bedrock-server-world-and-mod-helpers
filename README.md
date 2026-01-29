# Minecraft Bedrock Server

A Docker-based Minecraft Bedrock Edition server with automated world setup and backup utilities.

## Overview

This project sets up and manages a Minecraft Bedrock Edition server running in Docker with support for multiple mods and automated world backups.

**Docker Image:** [lomot/minecraft-bedrock:latest](https://hub.docker.com/r/lomot/minecraft-bedrock)

## Quick Start

### Create the Container (First Time)

To create the Minecraft Bedrock server container using the mcpe folder from this project:

```bash
sudo docker run -itd --restart=always --name=mcpe --net=host \
  -v $(pwd)/mcpe:/data \
  lomot/minecraft-bedrock:latest
```

**Environment Variables:**
- `$(pwd)/mcpe` - Path to server data (mount to `/data` in container)
- `--net=host` - Use host network for better performance
- `--restart=always` - Auto-restart container on reboot or crash

### Start the Server
```bash
sudo docker start mcpe
```

### Stop the Server
```bash
sudo docker stop mcpe
```

### View Server Logs
```bash
sudo docker logs -f mcpe
```

### Check Server Status
```bash
sudo docker ps
```

## Project Structure

```
.
├── mcpe/                              # Server data directory
│   ├── worlds/                        # World data (ignored)
│   │   └── Bedrock level/             # Current world
│   │       ├── db/                    # World database files
│   │       ├── level.dat              # World metadata
│   │       ├── world_behavior_packs.json
│   │       └── world_resource_packs.json
│   ├── development_behavior_packs/    # Installed behavior packs (ignored)
│   ├── development_resource_packs/    # Installed resource packs (ignored)
│   ├── server.properties              # Server configuration
│   ├── allowlist.json                 # Whitelist (if enabled)
│   └── permissions.json               # Player permissions
├── mods/                              # Mod files (original .mcaddon/.mcpack)
├── backups/                           # World backups (ignored)
├── scripts/                           # Utility scripts
│   ├── setup_world.py                 # Setup world and install mods
│   └── backup_world.py                # Backup world to .mcworld file
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

## Current World

**World Name:** Core Craft TK2  
**Installed Mods:** 16 packs (7 behavior, 9 resource)

### Installed Behavior Packs
- Lost Chests (V0.0.3)
- Magic Broomsticks (V0.2.2)
- Scuba Goggles (V0.0.5)
- SmellyBlox (1.0.38)
- Stargate Bedrock (1.1.43)
- SilkTouchSpawners (v1.0.19)
- Core Craft (v1.0.5)

### Installed Resource Packs
- DoubleHands Animations (3.1.0)
- GraveStone (V2.0.7) x2
- Magic Broomsticks (V0.2.2)
- Scuba Goggles (V0.0.5)
- SmellyBlox (1.0.38)
- Stargate Bedrock (1.1.43)
- SilkTouchSpawners (v1.0.19)
- Core Craft (v1.0.5)

## Scripts

### Setup World & Mods
```bash
python3 scripts/setup_world.py
```

**What it does:**
- Selects world from `world_backups/` directory or uses existing world
- Installs all mods from the `mods/` directory
- Generates proper pack JSON configurations
- Cleans up previously deployed mods before reinstalling
- Creates backup of previous world

**Requirements:**
- World file in `world_backups/` directory (`.mcworld` format), or existing world in `mcpe/worlds/Bedrock level/`
- All mods in `mods/` directory

**Important - Importing Worlds from Another Server:**

If you are using an exported world (`.mcworld` file) from another server/game that has mods, you **must** ensure those mods are present in the `mods/` folder before running setup. The script will:

1. Detect the world's required mods from `world_*_packs.json` files
2. Install the corresponding mod packs from the `mods/` folder
3. Fail if a required mod is missing

**To import a modded world:**
1. Copy the exported `.mcworld` file to `world_backups/`
2. Obtain all the mod files (`.mcaddon`/`.mcpack`) that were used in that world
3. Place them in the `mods/` folder
4. Run: `python3 scripts/setup_world.py`
5. Select the world file when prompted
- World file: `Core Craft TK2 1-26-26d.mcworld`
- Mods in: `mods/` directory

---

### Backup World
```bash
python3 scripts/backup_world.py
```

**What it does:**
- Exports current world to `.mcworld` file
- Saves to `backups/` directory
- Auto-generates filename: `LevelName_MmmDD_YYYY.mcworld`
- Increments letter (a, b, c...) for same-day backups
- Compresses world data

**Backup Naming Examples:**
- `Core_Craft_TK2_Jan28_2026.mcworld`
- `Core_Craft_TK2_Jan28_2026a.mcworld`
- `Core_Craft_TK2_Jan28_2026b.mcworld`

---

## Docker Commands

### View Running Containers
```bash
sudo docker ps
```

### View All Containers
```bash
sudo docker ps -a
```

### View Container Logs
```bash
# Live logs (last 100 lines, follow)
sudo docker logs -f --tail 100 mcpe

# Show all logs
sudo docker logs mcpe
```

### Restart Server
```bash
sudo docker restart mcpe
```

### Enter Server Container
```bash
sudo docker exec -it mcpe bash
```

### Remove Container (stops and deletes)
```bash
sudo docker stop mcpe
sudo docker rm mcpe
```

## Server Configuration

### Server Properties
Located at: `mcpe/server.properties`

Key settings:
- `server-name`: Display name for the server
- `gamemode`: Creative, Survival, Adventure, Spectator
- `difficulty`: Peaceful, Easy, Normal, Hard
- `max-players`: Maximum players allowed
- `online-mode`: Enable Microsoft account verification
- `allow-cheats`: Enable command blocks and cheats

### Allowlist (Whitelist)
Located at: `mcpe/allowlist.json`

Add players to allow them to join the server.

### Permissions
Located at: `mcpe/permissions.json`

Manage player roles and permissions.

## Backup & Recovery

### Creating Backups
```bash
# Automatic backup
python3 scripts/backup_world.py

# Manual Docker backup
docker cp mcpe:/data/worlds/"Bedrock level" ./backup-manual/
```

### Restore from Backup
```bash
# Stop the server
sudo docker stop mcpe

# Restore world
cp -r backups/Core_Craft_TK2_Jan28_2026.mcworld /tmp/restore.mcworld
unzip /tmp/restore.mcworld -d mcpe/worlds/Bedrock\ level

# Restart server
sudo docker start mcpe
```

## Adding New Mods

1. Place `.mcaddon` or `.mcpack` files in the `mods/` directory
2. Stop the server: `sudo docker stop mcpe`
3. Run setup: `python3 scripts/setup_world.py`
4. Start the server: `sudo docker start mcpe`

The setup script will:
- Extract all mod UUIDs
- Install packs to development directories
- Update world pack JSON files automatically

## Troubleshooting

### Server Won't Start
```bash
# Check logs
sudo docker logs mcpe

# Ensure volume is mounted correctly
sudo docker inspect mcpe | grep -A 10 "Mounts"
```

### Can't Connect to Server
- Verify server is running: `sudo docker ps`
- Check firewall settings
- Verify world file integrity
- Check `server.properties` settings

### Mods Not Loading
- Verify `world_behavior_packs.json` and `world_resource_packs.json` exist
- Check pack UUIDs are correct
- Ensure packs are in `development_*_packs/` directories
- Restart server after mod installation

### Corrupted World
```bash
# Restore from backup
cp -r mcpe/worlds/Bedrock\ level.backup mcpe/worlds/Bedrock\ level
sudo docker restart mcpe
```

## System Requirements

- Docker & Docker Compose installed
- ~60MB disk space per world backup
- 1GB+ RAM for server
- Network access for player connections

## Maintenance

### Weekly Tasks
- Monitor server logs for errors
- Check available disk space

### Monthly Tasks
- Create full world backup: `python3 scripts/backup_world.py`
- Review and clean old backups

### Before Major Changes
- Always create a backup: `python3 scripts/backup_world.py`

## Notes

- Server data is mounted as volume: `/mnt/z/Minecraft/server/mcpe` → `/data` in container
- Mods are installed in development packs directories (not packed into world)
- World is automatically backed up before setup script runs
- All scripts use absolute paths for reliability

## Support

For issues with:
- **Docker:** See [Docker Documentation](https://docs.docker.com/)
- **Minecraft Bedrock:** See [Minecraft Wiki](https://minecraft.wiki/)
- **Server Image:** See [lomot/minecraft-bedrock](https://hub.docker.com/r/lomot/minecraft-bedrock)

## License

Minecraft Bedrock is owned by Mojang/Microsoft. This project is for personal server management.

---

**Last Updated:** January 28, 2026  
**Setup Date:** January 28, 2026  
**Server Image Version:** latest
