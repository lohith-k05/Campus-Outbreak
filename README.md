# Campus Outbreak

A 2D top-down survival horror action-adventure game built with Pygame.

## Overview
Set in a quarantined university campus during a sudden viral outbreak, you must navigate various department blocks, solve environmental puzzles, fight infected hordes, rescue stranded students, and locate the cure in the secret Research Department.

## Game Controls
- **Movement**: `W`, `A`, `S`, `D` or `Arrow Keys`
- **Aim / Shoot**: Mouse Left Click / Spacebar
- **Interact**: `E` or `Enter` (Terminals, NPCs, Books, Doors)
- **Escape / Pause**: `ESC`

## Audio & Video Configuration
- **Audio Engine**: Powered by `pygame.mixer` with automatic fallbacks for headless/missing sound devices.
- **Cinematics**: Embedded high-resolution MP4 cinematics played using `python-vlc` (falls back to Pygame frame rendering if VLC is unavailable).

## Building Executables
```bash
pyinstaller CampusOutbreak_OneFile.spec
```
