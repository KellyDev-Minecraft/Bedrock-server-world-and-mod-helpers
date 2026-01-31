# Developer Report: InvalidEntityError in onEntitySpawn

This report details the bug and fix implemented in `main.js` to resolve `InvalidEntityError`.

## The Issue

The Minecraft Bedrock server logs reported multiple instances of:
```
[ERROR] [Scripting] InvalidEntityError: Failed to get property 'location' due to Entity being invalid (has the Entity been removed?).
    at onEntitySpawn (main.js:1)
```

This occurs when an `onEntitySpawn` event handler is called, but the entity becomes invalid (removed from the world or failed initialization) before the script can access its properties. In the minified code, the handler was immediately accessing `.location` or other properties without checking `.isValid`.

## Fix Locations & Details

### 1. Common Mob Spawn Handler (Zombie, Skeleton, Spider)

**Original Code (approximate deminification):**
```javascript
['minecraft:zombie', 'minecraft:skeleton', 'minecraft:spider'].forEach(mobId => {
    system.register({
        id: mobId,
        events: {
            onEntitySpawn: (entity, cause) => {
                if (!(entity.location.y < 120) && dimension.isThunder() && Math.random() < 1/6) {
                    // lightning bolt logic...
                }
            }
        }
    });
});
```

**Problem:** `entity.location` was accessed before checking if `entity` is valid.

**Fix Applied:**
Added `entity && entity.isValid` check.
```javascript
if (entity && entity.isValid && !(entity.location.y < 120) && ...)
```

---

### 2. Eye of Ender Signal Handler

**Original Code (approximate deminification):**
```javascript
system.register({
    id: 'minecraft:eye_of_ender_signal',
    events: {
        onEntitySpawn: entity => {
            if (random(0, 1) > 0.1) return;
            let location = entity.location;
            let dimension = entity.dimension;
            entity.remove();
            dimension.spawnEntity('cc:ender_bat', location);
        }
    }
});
```

**Problem:** `entity.location` and `entity.dimension` were accessed without validation.

**Fix Applied:**
Added early exit if entity is invalid.
```javascript
onEntitySpawn: entity => {
    if (!entity || !entity.isValid || random(0, 1) > 0.1) return;
    // ...
}
```

## Recommendations for the Developer

1.  **Always check `.isValid`**: In Minecraft Bedrock scripting, entities passed to event handlers are not guaranteed to remain valid. Always wrap property access (especially `.location`, `.dimension`, `.id`) in an `if (entity && entity.isValid)` block.
2.  **Generic Event Hooks**: If you have a generic event dispatcher, consider adding a validity check there before invoking specific mod logic.
3.  **Error Handling**: Consider wrapping event handlers in `try-catch` blocks to prevent a single invalid entity from causing script-wide issues, although checking `.isValid` is the preferred and more performant approach.
