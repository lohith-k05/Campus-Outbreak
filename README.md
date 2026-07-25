# Campus Outbreak

![Game Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-orange)
![License](https://img.shields.io/badge/License-Proprietary-lightgrey)

A 2D top-down survival horror action-adventure game developed in Pygame.

---

## 🎮 Synopsis
A peaceful university campus becomes the epicenter of a catastrophic viral outbreak. As a lone survivor trapped within the perimeter walls, you must navigate through quarantined departmental blocks, evade and neutralize mutated students and faculty, uncover the origin of the contagion, and secure the synthesized cure before the campus undergoes total sterilization.

---

## 🕹️ Controls

| Action | Primary Key | Secondary Key |
|---|---|---|
| **Move Up** | `W` | `Up Arrow` |
| **Move Down** | `S` | `Down Arrow` |
| **Move Left** | `A` | `Left Arrow` |
| **Move Right** | `D` | `Right Arrow` |
| **Aim / Fire** | `Left Mouse Click` | `Spacebar` |
| **Interact / Inspect** | `E` | `Return / Enter` |
| **Pause / Menu** | `ESC` | - |

---

## 🏛️ Campus Departments & Chapters

1. **Campus Grounds & Main Gate**:
   - Expansive 2600x1800 procedural campus grounds.
   - Roads, crosswalks, sports stadium, NCC wing, and department footprints.
   - Smooth top-down camera with interior deadzone tracking.

2. **AI Department (Block A)**:
   - Security lockdown terminals and decipherable lore logs.
   - 4-wave horde defense encounter.
   - Tactical HUD overlay displaying ammo, health, and wave progress.

3. **Mechanical Engineering Workshop**:
   - Industrial hazards, machine tools, and narrow corridors.
   - Swarms of aggressive Student Zombies.
   - Survivor escort mission requiring companion protection.

4. **Library Dome & Archives**:
   - Multi-tiered book stacks, reading rooms, and stealth navigation.
   - Hidden door puzzle concealed behind historical archives.
   - Elite, highly durable Faculty Zombies.

5. **Secret Research Department**:
   - Underground containment facility.
   - Climax boss battle against the infected Chief Research Doctor.
   - Synthesizing and extracting the viral cure sample.

6. **Epilogue & Evacuation**:
   - Cinematic climax cutscene with full audio synchronization.
   - Final shot cutscene and credits sequence.

---

## 🧟 Enemy Profiles

| Enemy Type | Speed | Health | Behavior |
|---|---|---|---|
| **Base Zombie** | Normal | 3 HP | Direct pursuit towards the player's last known position. |
| **Student Zombie** | Fast | 2 HP | High velocity swarm behavior in tight workshop spaces. |
| **Faculty Zombie** | Slow | 8 HP | Tank-like durability with devastating melee damage. |
| **Research Doctor** | Very Fast | 15 HP | Final boss with rapid dashes, erratic pathing, and lethal strikes. |

---

## 🎧 Audio & Cutscenes

- **Ambient Audio**: Looping atmospheric soundtrack tailored for campus tension.
- **Positional SFX**: Electrical sparks, flickering fluorescent lights, slamming security doors, ringing rotary phones, and terminal glitching.
- **Cinematics**: Embedded high-definition MP4 cutscenes using `libVLC` with graceful Pygame fallback renderer for universal compatibility.

---

## 🚀 Installation & Running

### Requirements
- Python 3.10 or higher
- Pygame 2.5.0+
- python-vlc 3.0.0+ (optional, for enhanced video playback)
- VLC Media Player installed (for VLC bindings)

### Setup
```bash
# Clone the repository
git clone <repository_url>
cd CampusOutbreak_New

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

---

## 📦 Building Executables

Build standalone Windows executables using the included PyInstaller specifications:

```bash
# Single-file bundled executable
pyinstaller CampusOutbreak_OneFile.spec

# Folder distribution bundle
pyinstaller CampusOutbreak.spec
```

The compiled binaries will be output to the `dist/` directory.

---

## 📁 Project Architecture

```
CampusOutbreak_New/
├── main.py                     # Main game loop, state machine, and scene controller
├── player.py                   # Player physics, animation, and interaction radius
├── camera.py                   # Smooth tracking camera with deadzone
├── collision.py                # AABB collision system for buildings and obstacles
├── map.py                      # Campus layout, terrain palettes, and road networks
├── transition.py               # Scene transition fades and wipes
├── zombie.py                   # Base zombie AI and bullet projectiles
├── student_zombie.py           # Swarm student zombie variant
├── faculty_zombie.py           # Elite faculty zombie entity
├── combat.py                   # AI Block wave combat logic
├── combat_ui.py                # Combat HUD overlay
├── npc.py                      # Interactive NPC dialogue system
├── rescued_student.py          # Companion follower AI and escort logic
├── ai_block.py                 # AI Department interior layout
├── ai_interaction.py           # Computer terminal interaction and puzzle state
├── mechanical_block.py         # Mechanical Workshop interior
├── mechanical_combat.py        # Workshop combat wave system
├── mechanical_ui.py            # Mechanical department HUD
├── library_chapter.py          # Library interior, racks, and hidden door
├── research_department.py      # Secret lab, doctor boss, and cure logic
├── CampusOutbreak.spec         # PyInstaller folder build spec
├── CampusOutbreak_OneFile.spec # PyInstaller single executable spec
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules for builds and caches
├── intro/                      # Intro cutscenes and splash screen
├── ending/                     # Climax video cutscenes
└── sounds/                     # Ambience, environment, and UI audio
```
