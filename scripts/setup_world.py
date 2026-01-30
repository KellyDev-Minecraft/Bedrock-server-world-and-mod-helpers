#!/usr/bin/env python3
"""
Setup world and mods for Minecraft Bedrock server.
Extracts world from mcworld file or uses existing world, then installs mods with proper UUIDs.
"""

import json
import os
import subprocess
import zipfile
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Paths - get git repository root
try:
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True, cwd=Path(__file__).parent
    )
    SERVER_ROOT = Path(result.stdout.strip())
except Exception:
    # Fallback: assume script is in scripts/ subdirectory of repo root
    SERVER_ROOT = Path(__file__).resolve().parent.parent
WORLD_BACKUPS_DIR = SERVER_ROOT / "world_backups"
MODS_DIR = SERVER_ROOT / "mods"
MCPE_DIR = SERVER_ROOT / "mcpe"
WORLDS_DIR = MCPE_DIR / "worlds"
BEDROCK_WORLD = WORLDS_DIR / "Bedrock level"
TEMP_EXTRACT = Path(__import__('tempfile').gettempdir()) / "minecraft_setup"

def select_world_backup() -> Optional[Path]:
    """
    Prompt user to select a world backup file or continue with existing world.
    Returns the path to the selected world file, or None if no selection.
    Always asks user to select from available worlds.
    """
    # List available world backups
    world_files = []
    if WORLD_BACKUPS_DIR.exists():
        world_files = sorted(WORLD_BACKUPS_DIR.glob("*.mcworld"), reverse=True)
    
    print("\n" + "=" * 70)
    print("AVAILABLE WORLD BACKUPS")
    print("=" * 70)
    
    if world_files:
        for i, world_file in enumerate(world_files, 1):
            size_mb = world_file.stat().st_size / (1024*1024)
            print(f"{i:2d}. {world_file.name:50s} {size_mb:8.2f} MB")
        if BEDROCK_WORLD.exists():
            print(f" 0. Skip - use existing world at {BEDROCK_WORLD}")
        else:
            print(f" 0. Skip - continue setup")
    else:
        if BEDROCK_WORLD.exists():
            print("No world backups available.")
            print(f" 0. Skip - use existing world at {BEDROCK_WORLD}")
        else:
            print("No world backups available.")
            print(f" 0. Skip - continue setup")
    print()
    
    while True:
        try:
            choice = input("Select world backup (0 to skip): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("Skipping world import.")
                return None
            
            if 1 <= choice_num <= len(world_files):
                selected = world_files[choice_num - 1]
                print(f"Selected: {selected.name}")
                return selected
            else:
                print(f"Invalid choice. Please select 0-{len(world_files)}")
        except ValueError:
            print("Invalid input. Please enter a number.")

def extract_uuid_from_manifest(manifest_path: str) -> Tuple[str, List[int]]:
    """Extract UUID and version from a manifest.json file."""
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            uuid = data.get('header', {}).get('uuid', '')
            version = data.get('header', {}).get('version', [0, 0, 1])
            return uuid, version
    except Exception as e:
        print(f"Error reading manifest {manifest_path}: {e}")
        return '', [0, 0, 1]

def get_mod_uuids() -> Dict[str, Dict]:
    """Extract UUIDs from all mods in the mods directory."""
    mod_uuids = {}
    
    if not MODS_DIR.exists():
        print(f"Mods directory not found: {MODS_DIR}")
        return mod_uuids
    
    # Process each mod
    for mod_file in sorted(MODS_DIR.glob("*.*")):
        if mod_file.suffix not in ['.mcaddon', '.mcpack']:
            continue
        
        mod_name = mod_file.stem
        print(f"\nProcessing: {mod_file.name}")
        
        # Extract mod to temp location
        mod_temp = TEMP_EXTRACT / mod_name
        mod_temp.mkdir(parents=True, exist_ok=True)
        
        try:
            with zipfile.ZipFile(mod_file, 'r') as zip_ref:
                zip_ref.extractall(mod_temp)
        except Exception as e:
            print(f"  Error extracting {mod_file.name}: {e}")
            continue
        
        # Find all manifest.json files
        for manifest in mod_temp.rglob("manifest.json"):
            uuid, version = extract_uuid_from_manifest(str(manifest))
            if uuid:
                try:
                    with open(manifest, 'r') as f:
                        data = json.load(f)
                    pack_type = determine_pack_type(data)
                except:
                    pack_type = "resource"
                print(f"  Found {pack_type} pack: {uuid} (version {version})")
                
                if uuid not in mod_uuids:
                    mod_uuids[uuid] = {
                        'mod': mod_name,
                        'version': version,
                        'type': determine_pack_type(data),
                        'file': mod_file.name
                    }
    
    return mod_uuids

def extract_world(world_file: Path) -> bool:
    """Extract world from mcworld file."""
    print(f"\nExtracting world from {world_file.name}...")
    
    if not world_file.exists():
        print(f"Error: World file not found: {world_file}")
        return False
    
    # Create temporary extraction directory
    world_temp = TEMP_EXTRACT / "world"
    world_temp.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(world_file, 'r') as zip_ref:
            zip_ref.extractall(world_temp)
        print(f"  Extracted world to {world_temp}")
        return True
    except Exception as e:
        print(f"  Error extracting world: {e}")
        return False

def backup_existing_world():
    """Backup existing Bedrock level world."""
    if BEDROCK_WORLD.exists():
        backup_path = WORLDS_DIR / "Bedrock level.backup"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(BEDROCK_WORLD, backup_path)
        print(f"Backed up existing world to {backup_path}")
        shutil.rmtree(BEDROCK_WORLD)

def replace_world(skip_extraction: bool = False):
    """Replace world with extracted world, or skip if using existing world."""
    print("\nReplacing world...")
    
    if skip_extraction:
        print("  Using existing world")
        return True
    
    world_temp = TEMP_EXTRACT / "world"
    
    if not world_temp.exists():
        print(f"Error: Extracted world not found at {world_temp}")
        return False
    
    # Backup existing world
    backup_existing_world()
    
    # Move extracted world to bedrock location
    shutil.move(str(world_temp), str(BEDROCK_WORLD))
    print(f"Moved world to {BEDROCK_WORLD}")
    
    return True

def create_pack_json(pack_ids: List[Dict], json_file: str):
    """Create world_*_packs.json file."""
    packs = []
    for pack_info in pack_ids:
        packs.append({
            "pack_id": pack_info['pack_id'],
            "version": pack_info['version']
        })
    
    with open(json_file, 'w') as f:
        json.dump(packs, f, indent=8)
    print(f"Created {Path(json_file).name}")

# Setup pack directories
def setup_packs_json(mod_uuids: Dict[str, Dict]):
    """Setup the world_behavior_packs.json and world_resource_packs.json files."""
    print("\nSetting up pack JSON files...")
    
    behavior_packs = []
    resource_packs = []
    
    for uuid, info in mod_uuids.items():
        pack_dict = {
            'pack_id': uuid,
            'version': info['version']
        }
        
        if info['type'] == 'behavior':
            behavior_packs.append(pack_dict)
        else:
            resource_packs.append(pack_dict)
    
    # Create behavior packs JSON
    behavior_json = BEDROCK_WORLD / "world_behavior_packs.json"
    create_pack_json(behavior_packs, str(behavior_json))
    
    # Create resource packs JSON
    resource_json = BEDROCK_WORLD / "world_resource_packs.json"
    create_pack_json(resource_packs, str(resource_json))

def determine_pack_type(manifest_data: dict) -> str:
    """Determine if a pack is behavior or resource based on its modules."""
    modules = manifest_data.get('modules', [])
    for module in modules:
        mtype = module.get('type')
        if mtype in ['data', 'javascript', 'script']:
            return "behavior"
        elif mtype in ['resources', 'client_data']:
            return "resource"
    return "resource"  # Default to resource if unknown

def install_mods():
    """Copy all mod files to mcpe/behavior_packs and mcpe/resource_packs directories."""
    print("\nInstalling mods...")
    
    dev_bp_dir = MCPE_DIR / "behavior_packs"
    dev_rp_dir = MCPE_DIR / "resource_packs"
    
    # Clean up existing packs first
    print("  Cleaning up previously deployed mods...")
    for d in [dev_bp_dir, dev_rp_dir]:
        if d.exists():
            for item in d.iterdir():
                if item.is_dir():
                    # Skip vanilla and internal folders
                    if item.name.lower().startswith('vanilla') or item.name.lower() in ['chemistry', 'definitions', 'experimental']:
                        print(f"  Skipping cleanup of internal pack: {item.name}")
                        continue
                    shutil.rmtree(item)
    
    # Create directories if they don't exist
    dev_bp_dir.mkdir(parents=True, exist_ok=True)
    dev_rp_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract and install each mod
    for mod_file in sorted(MODS_DIR.glob("*.*")):
        if mod_file.suffix not in ['.mcaddon', '.mcpack']:
            continue
        
        mod_name = mod_file.stem
        print(f"\nInstalling: {mod_file.name}")
        
        mod_temp = TEMP_EXTRACT / mod_name
        if mod_temp.exists():
            shutil.rmtree(mod_temp)
        mod_temp.mkdir(parents=True, exist_ok=True)
        
        # Extract mod
        try:
            with zipfile.ZipFile(mod_file, 'r') as zip_ref:
                zip_ref.extractall(mod_temp)
        except Exception as e:
            print(f"  Error extracting {mod_file.name}: {e}")
            continue
        
        # Find all manifest.json files (nested or flat)
        manifests = list(mod_temp.rglob("manifest.json"))
        
        for manifest_path in manifests:
            try:
                with open(manifest_path, 'r') as f:
                    data = json.load(f)
                    header = data.get('header', {})
                    uuid = header.get('uuid')
                    if not uuid:
                        continue
                        
                    pack_type = determine_pack_type(data)
                    dest_dir = dev_bp_dir if pack_type == 'behavior' else dev_rp_dir
                    
                    dest = dest_dir / uuid
                    print(f"  Installing {pack_type} pack: {header.get('name')} ({uuid})")
                    
                    # Remove destination if it exists
                    if dest.exists():
                        shutil.rmtree(dest)
                    
                    # Copy the pack folder (parent of manifest.json)
                    shutil.copytree(manifest_path.parent, dest)
            except Exception as e:
                print(f"  Warning: Could not process {manifest_path}: {e}")

def check_required_mods(world_file: Path) -> bool:
    """
    Check if a world file has required mods and if they exist in mods directory.
    Returns True if all required mods are available, False otherwise.
    """
    print("\nValidating required mods for world...")
    
    # Extract world temporarily to read pack JSON files
    temp_check = TEMP_EXTRACT / "world_check"
    temp_check.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(world_file, 'r') as zip_ref:
            zip_ref.extractall(temp_check)
        
        # Read pack JSON files
        behavior_file = temp_check / "world_behavior_packs.json"
        resource_file = temp_check / "world_resource_packs.json"
        
        required_packs = []  # List of (uuid, version, type)
        
        # Get required UUIDs from world
        for pack_file, pack_type in [(behavior_file, "behavior"), (resource_file, "resource")]:
            if pack_file.exists():
                try:
                    with open(pack_file, 'r') as f:
                        packs = json.load(f)
                        for pack in packs:
                            uuid = pack.get('pack_id', '')
                            version = pack.get('version', [0, 0, 0])
                            if uuid:
                                required_packs.append((uuid, version, pack_type))
                except Exception as e:
                    print(f"  Warning: Could not read {pack_file.name}: {e}")
        
        if not required_packs:
            print("  ✓ No mods required by world")
            return True
        
        # Get available mod UUIDs and metadata
        available_packs = {}  # uuid -> {name, version, type, file}
        if MODS_DIR.exists():
            for mod_file in MODS_DIR.glob("*.*"):
                if mod_file.suffix not in ['.mcaddon', '.mcpack']:
                    continue
                
                mod_temp = TEMP_EXTRACT / f"check_{mod_file.stem}"
                mod_temp.mkdir(parents=True, exist_ok=True)
                
                try:
                    with zipfile.ZipFile(mod_file, 'r') as zip_ref:
                        zip_ref.extractall(mod_temp)
                    
                    for manifest in mod_temp.rglob("manifest.json"):
                        try:
                            with open(manifest, 'r') as f:
                                data = json.load(f)
                                uuid = data.get('header', {}).get('uuid', '')
                                name = data.get('header', {}).get('name', 'Unknown')
                                version = data.get('header', {}).get('version', [0, 0, 0])
                                pack_scope = data.get('header', {}).get('pack_scope', 'global')
                                
                                # Determine pack type
                                pack_type = 'behavior' if pack_scope == 'world' or 'behavior' in str(manifest).lower() or 'BP' in str(manifest) else 'resource'
                                
                                if uuid:
                                    available_packs[uuid] = {
                                        'name': name,
                                        'version': version,
                                        'type': pack_type,
                                        'file': mod_file.name
                                    }
                        except:
                            pass
                except:
                    pass
                finally:
                    if mod_temp.exists():
                        shutil.rmtree(mod_temp)
        
        # Check for missing mods
        missing_packs = []
        found_count = 0
        
        print(f"  Required packs: {len(required_packs)}")
        print(f"  Checking availability...")
        
        for req_uuid, req_version, req_type in required_packs:
            if req_uuid in available_packs:
                found_count += 1
                pack_info = available_packs[req_uuid]
                print(f"    ✓ {pack_info['name']} ({pack_info['file']})")
            else:
                missing_packs.append((req_uuid, req_type))
        
        print(f"  Found packs: {found_count}/{len(required_packs)}")
        
        if missing_packs:
            print(f"\n  ✗ Missing {len(missing_packs)} mod pack(s):")
            for uuid, pack_type in missing_packs:
                print(f"    - [{pack_type.upper()}] {uuid}")
            print(f"\n  Actions:")
            print(f"    1. Export the missing mods from the original server/world")
            print(f"    2. Place the .mcaddon or .mcpack files in:")
            print(f"       {MODS_DIR}")
            print(f"    3. Run this script again")
            print(f"\n  Note: The UUID alone doesn't identify the mod. You need to:")
            print(f"    - Ask the server owner what mods were used")
            print(f"    - Check the Minecraft Marketplace/CurseForge/MCPEDL \n      for beddrock add-on packs")
            print(f"    - Find the mod creator's website or repository")
            
            # Ask user if they want to continue anyway
            print(f"\n  ⚠️  WARNING: Missing mods may cause the world to not work correctly!")
            while True:
                response = input(f"\n  Continue setup anyway? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    print(f"  Proceeding with setup at user's risk...")
                    return True
                elif response in ['n', 'no', '']:
                    print(f"  Setup cancelled.")
                    return False
                else:
                    print(f"  Please enter 'y' for yes or 'n' for no")
                    continue
        else:
            print(f"  ✓ All required mods are available")
            return True
            
    except Exception as e:
        print(f"  Warning: Could not validate mods: {e}")
        return True
    finally:
        # Clean up
        if temp_check.exists():
            shutil.rmtree(temp_check)

def main():
    """Main setup function."""
    print("=" * 70)
    print("Minecraft Bedrock Server Setup")
    print("=" * 70)
    
    # Create temp directory
    TEMP_EXTRACT.mkdir(parents=True, exist_ok=True)
    
    try:
        # Extract UUIDs from mods
        print("\nPhase 1: Extracting mod UUIDs...")
        mod_uuids = get_mod_uuids()
        
        if not mod_uuids:
            print("Warning: No mods found!")
        else:
            print(f"\nFound {len(mod_uuids)} mod packs")
        
        # Select world or use existing
        print("\nPhase 2: World Selection...")
        world_file = select_world_backup()
        skip_world_extraction = world_file is None
        
        # Validate required mods if importing a world
        if world_file is not None:
            print("\nPhase 2b: Validating Required Mods...")
            if not check_required_mods(world_file):
                print("\n✗ Setup aborted - required mods not available")
                return False
        
        # Extract world if selected
        if world_file is not None:
            if not extract_world(world_file):
                print("Error: Failed to extract world")
                return False
        elif not BEDROCK_WORLD.exists():
            print("\n✗ No world selected and no existing world found!")
            print("Cannot continue without a world.")
            return False
        # Replace world
        print("\nPhase 3: Replacing world...")
        if not replace_world(skip_extraction=skip_world_extraction):
            print("Error: Failed to replace world")
            return False
        
        # Setup pack JSON files
        print("\nPhase 4: Setting up pack JSON files...")
        setup_packs_json(mod_uuids)
        
        # Install mods
        print("\nPhase 5: Installing mods...")
        install_mods()
        
        print("\n" + "=" * 70)
        print("Setup complete!")
        print("=" * 70)
        print(f"World location: {BEDROCK_WORLD}")
        print(f"Behavior packs: {MCPE_DIR / 'behavior_packs'}")
        print(f"Resource packs: {MCPE_DIR / 'resource_packs'}")
        print("Next steps:")
        print("  1. Restart the server: sudo docker restart mcpe")
        print("     (Or if re-creating: include -e EULA=TRUE for itzg image)")
        print("  2. View logs: sudo docker logs -f mcpe")
        print()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temp directory
        if TEMP_EXTRACT.exists():
            shutil.rmtree(TEMP_EXTRACT)
            print(f"Cleaned up temporary files")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
