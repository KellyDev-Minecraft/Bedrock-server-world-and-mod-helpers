#!/usr/bin/env python3
"""
Backup/Export Minecraft Bedrock world to .mcworld file.
Automatically handles date-based naming with incrementing letters for duplicates.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional

# Paths
SERVER_ROOT = Path("/mnt/z/Minecraft/server")
WORLDS_DIR = SERVER_ROOT / "mcpe" / "worlds"
BEDROCK_WORLD = WORLDS_DIR / "Bedrock level"
BACKUPS_DIR = SERVER_ROOT / "backups"

def get_next_backup_filename() -> str:
    """
    Generate backup filename with date and incrementing letter if needed.
    Format: LevelName_MmmDD_YYYY.mcworld or LevelName_MmmDD_YYYYa.mcworld, etc.
    Spaces in level name are replaced with underscores.
    """
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read level name from levelname.txt
    levelname_file = BEDROCK_WORLD / "levelname.txt"
    level_name = "World"
    if levelname_file.exists():
        try:
            with open(levelname_file, 'r') as f:
                level_name = f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read level name: {e}")
    
    # Replace spaces with underscores
    level_name = level_name.replace(" ", "_")
    
    date_str = datetime.now().strftime("%b%d_%Y")
    base_name = f"{level_name}_{date_str}"
    
    # Check if base filename exists
    base_file = BACKUPS_DIR / f"{base_name}.mcworld"
    if not base_file.exists():
        return base_name
    
    # Find next available letter
    for i, letter in enumerate("abcdefghijklmnopqrstuvwxyz"):
        filename = f"{base_name}{letter}"
        file_path = BACKUPS_DIR / f"{filename}.mcworld"
        if not file_path.exists():
            return filename
    
    # Fallback if we somehow run out of letters (unlikely)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_backup_{timestamp}"

def create_backup() -> bool:
    """Create .mcworld backup file from the current world."""
    
    if not BEDROCK_WORLD.exists():
        print(f"Error: World directory not found: {BEDROCK_WORLD}")
        return False
    
    # Generate backup filename
    backup_name = get_next_backup_filename()
    backup_path = BACKUPS_DIR / f"{backup_name}.mcworld"
    
    print("=" * 70)
    print("MINECRAFT BEDROCK WORLD BACKUP")
    print("=" * 70)
    print(f"\nSource world: {BEDROCK_WORLD}")
    print(f"Backup destination: {backup_path}")
    print(f"Backup name: {backup_name}.mcworld")
    
    try:
        # Create temporary zip file with progress
        print("\nCreating backup...")
        
        # List all files to be backed up
        files_to_backup = []
        total_size = 0
        
        for root, dirs, files in os.walk(BEDROCK_WORLD):
            for file in files:
                file_path = Path(root) / file
                files_to_backup.append((file_path, file_path.relative_to(BEDROCK_WORLD)))
                total_size += file_path.stat().st_size
        
        print(f"  Files to backup: {len(files_to_backup)}")
        print(f"  Total size: {total_size / (1024*1024):.2f} MB")
        
        # Create the zip file
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, arcname in files_to_backup:
                zipf.write(file_path, arcname)
                sys.stdout.write(f"\r  Compressing... {len(zipf.namelist())} files")
                sys.stdout.flush()
        
        backup_size = backup_path.stat().st_size
        compression = ((total_size - backup_size) / total_size * 100) if total_size > 0 else 0
        
        print(f"\n\n✓ Backup created successfully!")
        print(f"  Backup file: {backup_path.name}")
        print(f"  Compressed size: {backup_size / (1024*1024):.2f} MB")
        print(f"  Compression ratio: {compression:.1f}%")
        print(f"  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating backup: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up partial backup
        if backup_path.exists():
            try:
                backup_path.unlink()
                print(f"  Cleaned up partial backup: {backup_path}")
            except:
                pass
        
        return False

def list_backups():
    """List all existing backups."""
    if not BACKUPS_DIR.exists() or not list(BACKUPS_DIR.glob("*.mcworld")):
        print("No backups found.")
        return
    
    print("\n" + "=" * 70)
    print("EXISTING BACKUPS")
    print("=" * 70)
    
    backups = sorted(BACKUPS_DIR.glob("*.mcworld"), reverse=True)
    
    for i, backup_file in enumerate(backups, 1):
        size_mb = backup_file.stat().st_size / (1024*1024)
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"{i:2d}. {backup_file.name:45s} {size_mb:8.2f} MB  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print()

def main():
    """Main backup function."""
    try:
        # Create backup
        success = create_backup()
        
        if success:
            # List all backups
            list_backups()
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n\nBackup cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
