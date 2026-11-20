# 🎲 D&D Beyond Dice Companion Widget

Floating desktop companion widget for D&D 5e tabletop gaming, inspired by Nuppi aesthetic. Built with Python (`pywebview`), Microsoft Edge WebView2, and styled with high-performance CSS/JavaScript.

## ✨ Features
- **2D Polyhedral Dice Roller**: Roll d20, d12, d100, d10, d8, d6, d4 with Advantage / Disadvantage, modifiers, and authentic roll formulas.
- **Dynamic Reroll System**: One-click reroll for 1s & 2s (Great Weapon Fighting / Savage Attacker) or reroll all dice.
- **Natural 1 & Natural 20 Detection**: Exclusive critical miss / critical hit audio and visual animations on single 1d20 rolls.
- **Combat & Turn Order Tracker HUD**: Initiative tracker, HP damage/healing stepper, and 8 quick D&D status condition chips.
- **Combo & Macro Vault**: Pre-configured signature attack combos plus a custom macro builder with one-click rolling.
- **Procedural Tabletop Audio & Ambience**: Synthesized sound effects (dice rattle, crit boom, fumble shatter, blade clash, spell chime) plus procedural background ambiences (Tavern Hearth, Dungeon Rain, Astral Drone).
- **Interactive Character Sheet & Sheet Importer**:
  - Built-in legendary sheet for **Malexius, The One Who Defied Fate** (Level 20 Rogue/Fighter/Wizard).
  - **Dynamic Sheet Importer**: Import your own character sheets via `.pdf`, `.txt`, or `.md` files or direct paste.
  - Automatic extraction of D&D 5e stats, saving throws, weapons, actions, and skills powered by Google Gemini AI.
  - Interactive 1-click rolls for attacks, damage, ability checks, and saving throws directly from your sheet.
- **AI Companion & Rules Oracle**: Powered by Google Gemini AI to describe dramatic cinematic action narrations, explain 5e rules, or calculate tactical options.
- **Window Controls**: Always on top toggle (Pin 📌), size presets (S / M / L), interactive edge resizers, and minimal dark scrollbars.

## 🚀 Running from Source
```bash
# Install dependencies
pip install pywebview pypdf

# Launch application
python dnd_companion/app.py
```

## 📦 Building Executable
```bash
pyinstaller --noconsole --onefile --icon="dnd_companion/dnd_dice.ico" --add-data "dnd_companion/index.html;." --distpath="." --name="DndDiceWidget" dnd_companion/app.py
```
