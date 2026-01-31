# Walkthrough - Fix InvalidEntityError in onEntitySpawn

I have fixed the `InvalidEntityError: Failed to get property 'location' due to Entity being invalid` error that was occurring in your Minecraft server logs.

## Changes Made

### [Minecraft Scripts]

#### [MODIFY] [main.js](file:///8TB/Server/minecraft/Bedrock-server-world-and-mod-helpers/mcpe/behavior_packs/d4ffea2a-7d37-4279-8986-3ec293263920/scripts/main.js)
Added `isValid` checks to the following `onEntitySpawn` event handlers:
- **Mob Spawn Handler**: For `zombie`, `skeleton`, and `spider`. Now checks if the entity is valid before checking its height for the lightning bolt effect.
- **Eye of Ender Handler**: Now checks if the Eye of Ender entity is valid before accessing its location to spawn an `ender_bat`.

The fix prevents the script from crashing when an entity is removed or becomes invalid immediately after spawning, which was the cause of the errors in your logs.

## Verification Results

### Automated Verification
I ran a custom script to verify that the checks were correctly applied to the minified `main.js` file:
- Verified `mob spawn handler` fix: **Applied**
- Verified `eye of ender handler` fix: **Applied**

### Manual Verification
The user should restart the server and observe the logs. The `InvalidEntityError` at `onEntitySpawn (main.js:1)` should no longer appear.
