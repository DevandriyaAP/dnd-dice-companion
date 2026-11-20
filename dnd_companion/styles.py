# Nuppi Design System & QSS Styles

COLOR_BG = "#0c0d10"
COLOR_CARD = "#16171d"
COLOR_CARD_HOVER = "#1c1d25"
COLOR_CARD_BORDER = "rgba(255, 255, 255, 0.07)"
COLOR_TEXT_MAIN = "#f3f4f6"
COLOR_TEXT_MUTED = "#9ca3af"
COLOR_TEXT_DARK = "#6b7280"

COLOR_GOLD = "#f59e0b"
COLOR_GOLD_BG = "rgba(245, 158, 11, 0.15)"
COLOR_GOLD_BORDER = "rgba(245, 158, 11, 0.35)"

COLOR_PURPLE = "#a855f7"
COLOR_PURPLE_BG = "rgba(168, 85, 247, 0.15)"

COLOR_GREEN = "#10b981"
COLOR_GREEN_BG = "rgba(16, 185, 129, 0.15)"

COLOR_RED = "#dc2626"
COLOR_RED_HOVER = "#ef4444"

COLOR_DICE_DEFAULT_TOP = "#254877"
COLOR_DICE_DEFAULT_BOTTOM = "#142640"
COLOR_DICE_BORDER = "#3b82f6"

COLOR_CRIT_HIT_TOP = "#f59e0b"
COLOR_CRIT_HIT_BOTTOM = "#b45309"
COLOR_CRIT_HIT_BORDER = "#fde047"

COLOR_CRIT_FAIL_TOP = "#dc2626"
COLOR_CRIT_FAIL_BOTTOM = "#7f1d1d"
COLOR_CRIT_FAIL_BORDER = "#fca5a5"

MAIN_STYLE = f"""
QWidget {{
    color: {COLOR_TEXT_MAIN};
    font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
}}

QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 0 4px 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.15);
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.3);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
