# Campus Outbreak

A 2D top-down survival horror action-adventure game built with Pygame.

## Overview
Set in a quarantined university campus during a sudden viral outbreak, you must navigate various department blocks, solve environmental puzzles, fight infected hordes, rescue stranded students, and locate the cure in the secret Research Department.

## Game Controls
- **Movement**: `W`, `A`, `S`, `D` or `Arrow Keys`
- **Aim / Shoot**: Mouse Left Click / Spacebar
- **Interact**: `E` or `Enter` (Terminals, NPCs, Books, Doors)
- **Escape / Pause**: `ESC`

## Packaging and Build
This project includes PyInstaller specification files for creating standalone binaries:
- `CampusOutbreak.spec`: Standard directory bundle.
- `CampusOutbreak_OneFile.spec`: Single executable package bundling all assets.

To build:
```bash
pyinstaller CampusOutbreak_OneFile.spec
```
