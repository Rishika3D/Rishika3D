#!/usr/bin/env python3
"""
Rimuru Tamagotchi — GitHub profile virtual pet.
Usage: python tamagotchi.py "<issue_title>" "<event_name>"
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
README_PATH   = "README.md"
STATE_PATH    = "pet-state.json"

# ── SVG asset URLs (hosted in profile repo /assets/) ──────────────────────────
GIFS = {
    "happy":    "https://raw.githubusercontent.com/Rishika3D/Rishika3D/main/assets/slime-happy.svg",
    "hungry":   "https://raw.githubusercontent.com/Rishika3D/Rishika3D/main/assets/slime-hungry.svg",
    "sleeping": "https://raw.githubusercontent.com/Rishika3D/Rishika3D/main/assets/slime-sleeping.svg",
}

DEFAULT_STATE = {
    "hunger":   100,
    "level":    1,
    "xp":       0,
    "lastFed":  datetime.now(timezone.utc).isoformat(),
    "lastPet":  datetime.now(timezone.utc).isoformat(),
}

# ── State I/O ─────────────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return DEFAULT_STATE.copy()

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

# ── Time helpers ──────────────────────────────────────────────────────────────
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def hours_since(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 3600

def time_ago(iso_str):
    h = hours_since(iso_str)
    if h < 1:   return "just now"
    if h < 24:  return f"{int(h)}h ago"
    return f"{int(h // 24)}d ago"

# ── Game logic ────────────────────────────────────────────────────────────────
def apply_decay(state):
    """Lose 3 hunger per hour since last fed (min 0)."""
    elapsed_hours = hours_since(state["lastFed"])
    decay = int(elapsed_hours * 3)
    state["hunger"] = max(0, state["hunger"] - decay)
    return state

def apply_action(state, action):
    action = action.strip().lower()
    if action == "feed":
        state["hunger"] = min(100, state["hunger"] + 40)
        state["lastFed"] = now_iso()
        state["xp"] = state.get("xp", 0) + 5
        print("🍱 Fed! +40 hunger, +5 XP")

    elif action == "train":
        state["xp"] = state.get("xp", 0) + 20
        state["hunger"] = max(0, state["hunger"] - 10)  # training costs hunger
        if state["xp"] >= 100:
            state["level"] += 1
            state["xp"] = 0
            print(f"⚔️ LEVEL UP! Now level {state['level']}")
        else:
            print(f"⚔️ Trained! +20 XP, -10 hunger")

    elif action == "headpat":
        state["lastPet"] = now_iso()
        state["xp"] = state.get("xp", 0) + 2
        print("👋 Headpat! +2 XP")

    return state

def get_mood(hunger):
    if hunger >= 80: return "Happy 😊"
    if hunger >= 50: return "Okay 😐"
    if hunger >= 20: return "Hungry 😟"
    return "Starving 😢"

def get_gif_key(hunger):
    if hunger >= 50: return "happy"
    if hunger >= 20: return "hungry"
    return "sleeping"

def progress_bar(value, max_val=100, filled="🟪", empty="⬛", segments=10):
    filled_count = round((value / max_val) * segments)
    return filled * filled_count + empty * (segments - filled_count)

# ── README rendering ──────────────────────────────────────────────────────────
def build_stats_block(state):
    hunger   = state["hunger"]
    level    = state["level"]
    xp       = state.get("xp", 0)
    mood     = get_mood(hunger)
    last_fed = time_ago(state["lastFed"])
    h_bar    = progress_bar(hunger)
    xp_bar   = progress_bar(xp)

    lines = [
        "<!-- pet-stats -->",
        "```",
        f"  ⚔️  Level {level}   ·   {mood}",
        f"  ─────────────────────────────────────────────────",
        f"  Hunger   {h_bar}  {hunger}/100",
        f"  XP       {xp_bar}  {xp}/100",
        f"  Fed      {last_fed}",
        "```",
        "<!-- pet-stats -->",
    ]
    return "\n".join(lines)

def update_readme(state):
    with open(README_PATH) as f:
        content = f.read()

    # Swap SVG asset based on hunger level
    gif_url = GIFS[get_gif_key(state["hunger"])]
    content = re.sub(
        r"<!-- pet-gif -->.*?<!-- pet-gif -->",
        f'<!-- pet-gif -->\n<img src="{gif_url}" width="200" height="200" />\n<!-- pet-gif -->',
        content, flags=re.DOTALL,
    )

    # Update stats code block
    content = re.sub(
        r"<!-- pet-stats -->.*?<!-- pet-stats -->",
        build_stats_block(state),
        content, flags=re.DOTALL,
    )

    with open(README_PATH, "w") as f:
        f.write(content)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    issue_title = sys.argv[1] if len(sys.argv) > 1 else ""
    event       = sys.argv[2] if len(sys.argv) > 2 else "schedule"

    state = load_state()
    state = apply_decay(state)

    if event == "issues" and "|" in issue_title:
        action = issue_title.split("|", 1)[1]
        state  = apply_action(state, action)

    save_state(state)
    update_readme(state)
    print(f"✅ hunger={state['hunger']} level={state['level']} xp={state['xp']} mood={get_mood(state['hunger'])}")
