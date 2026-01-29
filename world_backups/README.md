# Backups Directory

This directory stores `.mcworld` backup files.

**Contents are ignored by Git** - backups are large and can be recreated.

## Creating Backups

Create a backup of the current world:

```bash
python3 ../scripts/backup_world.py
```

**Backup Filename Format:** `LevelName_MmmDD_YYYY.mcworld`

Examples:
- `World_Jan28_2026.mcworld`
- `World_Jan28_2026a.mcworld` (second backup same day)
- `World_Jan29_2026.mcworld` (next day)

## Restoring from Backup

To restore a world from backup:

```bash
# Stop the server
sudo docker stop mcpe

# Extract backup to world directory
unzip Core_Craft_TK2_Jan28_2026.mcworld -d ../mcpe/worlds/Bedrock\ level

# Restart the server
sudo docker start mcpe
```

## Backup Strategy

**Recommended Schedule:**
- Daily backups before major changes
- Weekly full backups
- Keep at least 2 weeks of backups
- Archive old backups separately

## Storage

- Each backup is ~55-60 MB (compressed)
- Keep 10-20 backups to balance storage vs recovery options
- Consider external storage for long-term archival

## Automated Backups

To schedule automatic daily backups, add to crontab:

```bash
# Daily backup at 3 AM
0 3 * * * cd /mnt/z/Minecraft/server && python3 scripts/backup_world.py
```

Run `crontab -e` to edit:

```bash
crontab -e
```

Add the line above, save and exit.
