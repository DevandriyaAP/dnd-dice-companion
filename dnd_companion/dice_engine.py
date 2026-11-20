import random
import time
import json
import os
from datetime import datetime

DICE_TYPES = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]

class RollResult:
    def __init__(self, character_name, dice_counts, modifier, rolls_detail, total, is_crit_hit=False, is_crit_fail=False, mode="normal"):
        self.character_name = character_name
        self.dice_counts = dice_counts  # dict like {"d6": 12}
        self.modifier = modifier        # int
        self.rolls_detail = rolls_detail  # list of dicts: [{"die": "d6", "value": 4}, ...]
        self.total = total              # int
        self.is_crit_hit = is_crit_hit
        self.is_crit_fail = is_crit_fail
        self.mode = mode                # "normal", "advantage", "disadvantage"
        self.timestamp = datetime.now().isoformat()

    def formula_str(self):
        parts = []
        for die, count in self.dice_counts.items():
            if count > 0:
                parts.append(f"{count}{die}")
        formula = " + ".join(parts) if parts else "d20"
        if self.modifier != 0:
            formula += f" {'+' if self.modifier > 0 else '-'} {abs(self.modifier)}"
        return formula

    def detail_math_str(self):
        vals = [str(r["value"]) for r in self.rolls_detail]
        if not vals:
            return ""
        if len(vals) > 8:
            prefix = " + ".join(vals[:4])
            suffix = " + ".join(vals[-2:])
            body = f"{prefix} + ... + {suffix}"
        else:
            body = " + ".join(vals)
        if self.modifier != 0:
            return f"({body}) {'+' if self.modifier > 0 else '-'} {abs(self.modifier)}"
        return body

    def to_dict(self):
        return {
            "character_name": self.character_name,
            "dice_counts": self.dice_counts,
            "modifier": self.modifier,
            "rolls_detail": self.rolls_detail,
            "total": self.total,
            "is_crit_hit": self.is_crit_hit,
            "is_crit_fail": self.is_crit_fail,
            "mode": self.mode,
            "timestamp": self.timestamp,
            "formula": self.formula_str(),
        }

    @staticmethod
    def from_dict(d):
        res = RollResult(
            character_name=d.get("character_name", "Malexius"),
            dice_counts=d.get("dice_counts", {}),
            modifier=d.get("modifier", 0),
            rolls_detail=d.get("rolls_detail", []),
            total=d.get("total", 0),
            is_crit_hit=d.get("is_crit_hit", False),
            is_crit_fail=d.get("is_crit_fail", False),
            mode=d.get("mode", "normal")
        )
        res.timestamp = d.get("timestamp", datetime.now().isoformat())
        return res


class DiceEngine:
    def __init__(self, data_file="dnd_dice_data.json"):
        self.data_file = data_file
        self.character_name = "Malexius, The One Who Defied Fate"
        self.history = []
        self.load_data()

    def roll(self, dice_counts, modifier=0, mode="normal"):
        """
        dice_counts: {"d4": 0, "d6": 2, ...}
        mode: "normal", "advantage", "disadvantage" (only applies if rolling d20)
        """
        rolls_detail = []
        dice_sum = 0
        is_crit_hit = False
        is_crit_fail = False

        # If nothing selected, default to 1d20
        active_dice = {k: v for k, v in dice_counts.items() if v > 0}
        if not active_dice:
            active_dice = {"d20": 1}

        # Special Advantage / Disadvantage handling for single d20
        if "d20" in active_dice and active_dice["d20"] == 1 and len(active_dice) == 1 and mode in ("advantage", "disadvantage"):
            r1 = random.randint(1, 20)
            r2 = random.randint(1, 20)
            if mode == "advantage":
                chosen = max(r1, r2)
                dropped = min(r1, r2)
            else:
                chosen = min(r1, r2)
                dropped = max(r1, r2)
            rolls_detail.append({"die": "d20", "value": chosen, "dropped": False})
            rolls_detail.append({"die": "d20", "value": dropped, "dropped": True})
            dice_sum = chosen
            if chosen == 20:
                is_crit_hit = True
            elif chosen == 1:
                is_crit_fail = True
        else:
            for die_name, count in active_dice.items():
                sides = int(die_name.replace("d", ""))
                for _ in range(count):
                    val = random.randint(1, sides)
                    rolls_detail.append({"die": die_name, "value": val, "dropped": False})
                    dice_sum += val
                    if sides == 20:
                        if val == 20:
                            is_crit_hit = True
                        elif val == 1:
                            is_crit_fail = True

        total = dice_sum + modifier
        result = RollResult(
            character_name=self.character_name,
            dice_counts=active_dice,
            modifier=modifier,
            rolls_detail=rolls_detail,
            total=total,
            is_crit_hit=is_crit_hit,
            is_crit_fail=is_crit_fail,
            mode=mode
        )
        self.history.insert(0, result)
        # Keep latest 50 rolls
        if len(self.history) > 50:
            self.history = self.history[:50]
        self.save_data()
        return result

    def clear_history(self):
        self.history = []
        self.save_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.character_name = data.get("character_name", self.character_name)
                    hist_data = data.get("history", [])
                    self.history = [RollResult.from_dict(d) for d in hist_data]
            except Exception as e:
                print(f"Error loading {self.data_file}: {e}")

    def save_data(self):
        try:
            data = {
                "character_name": self.character_name,
                "history": [r.to_dict() for r in self.history[:50]]
            }
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {self.data_file}: {e}")
