import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QScrollArea, QLineEdit, QStackedWidget,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QCursor, QKeySequence, QShortcut, QIcon, QAction
)

from dice_engine import DiceEngine, DICE_TYPES
from components import DiceButton, DiceResultTile, KopiCatAvatar
from styles import (
    COLOR_BG, COLOR_CARD, COLOR_CARD_HOVER, COLOR_CARD_BORDER,
    COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_TEXT_DARK,
    COLOR_GOLD, COLOR_GOLD_BG, COLOR_GOLD_BORDER,
    COLOR_PURPLE, COLOR_PURPLE_BG,
    COLOR_GREEN, COLOR_GREEN_BG,
    COLOR_RED, COLOR_RED_HOVER,
    MAIN_STYLE
)

def get_asset_path(filename):
    """Helper to locate assets both in normal python execution and PyInstaller bundled exe"""
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

class FloatingDndWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = DiceEngine()
        self.dice_counts = {d: 0 for d in DICE_TYPES}
        self.modifier = 0
        self.roll_mode = "normal"  # "normal", "advantage", "disadvantage"
        self.is_collapsed = False
        self.is_pinned = True
        self.drag_position = QPoint()

        self.setWindowTitle("D&D Dice Widget")
        self.icon_path = get_asset_path("dnd_dice.ico")
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Real top-level window (not a popup), frameless, always-on-top
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(MAIN_STYLE)

        self.normal_width = 420
        self.normal_height = 580
        self.collapsed_width = 280
        self.collapsed_height = 44

        self.setFixedSize(self.normal_width, self.normal_height)

        # Central Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self._init_ui()
        self._init_tray_icon()

        # Keyboard shortcuts
        QShortcut(QKeySequence("Space"), self, self.on_roll_clicked)
        QShortcut(QKeySequence("Escape"), self, self.on_clear_clicked)

        # Default roll state
        self.last_result = None
        self.roll_animation_timer = QTimer(self)
        self.roll_animation_timer.timeout.connect(self._animate_roll_tick)
        self.anim_ticks = 0

    def _init_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray.setIcon(QIcon(self.icon_path))
        else:
            self.tray.setIcon(self.windowIcon())
        
        tray_menu = QMenu()
        act_show = QAction("Show / Restore", self)
        act_show.triggered.connect(self.show_normal_window)
        tray_menu.addAction(act_show)

        act_mini = QAction("Mini Notch Mode", self)
        act_mini.triggered.connect(self.toggle_collapse)
        tray_menu.addAction(act_mini)

        tray_menu.addSeparator()
        act_quit = QAction("Quit D&D Companion", self)
        act_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(act_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.show_normal_window()

    def show_normal_window(self):
        if self.is_collapsed:
            self.toggle_collapse()
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        if hasattr(self, 'tray'):
            self.tray.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(0)

        # Main background container with rounded corners and subtle shadow
        self.container = QWidget(self.central_widget)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(14, 12, 14, 14)
        self.container_layout.setSpacing(10)

        self.main_layout.addWidget(self.container)

        # 1. Header with Nuppi Pill Tabs and Controls
        self._build_header()

        # 2. Collapsed View Widget (hidden by default)
        self._build_collapsed_view()

        # 3. Stacked Pages (Dice Page, History Page, Character Page)
        self.pages = QStackedWidget(self)
        self._build_dice_page()
        self._build_history_page()
        self._build_character_page()

        self.container_layout.addWidget(self.pages)
        self.set_active_tab("dice")

    def _build_header(self):
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Mascot Avatar
        self.mascot = KopiCatAvatar(self)
        header_layout.addWidget(self.mascot)

        # Navigation Pills (Nuppi Style)
        self.nav_container = QWidget()
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        self.btn_tab_dice = self._create_pill_btn("🎲 Dice", "dice")
        self.btn_tab_hist = self._create_pill_btn("📜 History", "history")
        self.btn_tab_char = self._create_pill_btn("⚔️ Hero", "character")

        nav_layout.addWidget(self.btn_tab_dice)
        nav_layout.addWidget(self.btn_tab_hist)
        nav_layout.addWidget(self.btn_tab_char)
        header_layout.addWidget(self.nav_container)

        header_layout.addStretch()

        # Window Controls: Pin, Collapse, Close
        self.btn_pin = QPushButton("📌")
        self.btn_pin.setToolTip("Toggle Always on Top")
        self.btn_pin.setFixedSize(26, 26)
        self.btn_pin.clicked.connect(self.toggle_pin)

        self.btn_collapse = QPushButton("➖")
        self.btn_collapse.setToolTip("Mini Notch Mode")
        self.btn_collapse.setFixedSize(26, 26)
        self.btn_collapse.clicked.connect(self.toggle_collapse)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Close / Minimize to Tray")
        self.btn_close.setFixedSize(26, 26)
        self.btn_close.clicked.connect(self.close)

        for btn in (self.btn_pin, self.btn_collapse, self.btn_close):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 13px;
                    color: {COLOR_TEXT_MUTED};
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.15);
                    color: {COLOR_TEXT_MAIN};
                }}
            """)
            header_layout.addWidget(btn)

        self.container_layout.addWidget(self.header_widget)

    def _create_pill_btn(self, text, tab_id):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.clicked.connect(lambda: self.set_active_tab(tab_id))
        return btn

    def set_active_tab(self, tab_id):
        self.active_tab = tab_id
        base_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 14px;
                color: #9ca3af;
                font-weight: 600;
                padding: 0 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #f3f4f6;
            }
        """
        gold_active = f"""
            QPushButton {{
                background: {COLOR_GOLD_BG};
                border: 1px solid {COLOR_GOLD_BORDER};
                border-radius: 14px;
                color: {COLOR_GOLD};
                font-weight: bold;
                padding: 0 10px;
                font-size: 12px;
            }}
        """
        purple_active = f"""
            QPushButton {{
                background: {COLOR_PURPLE_BG};
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 14px;
                color: {COLOR_PURPLE};
                font-weight: bold;
                padding: 0 10px;
                font-size: 12px;
            }}
        """
        green_active = f"""
            QPushButton {{
                background: {COLOR_GREEN_BG};
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 14px;
                color: {COLOR_GREEN};
                font-weight: bold;
                padding: 0 10px;
                font-size: 12px;
            }}
        """
        self.btn_tab_dice.setStyleSheet(gold_active if tab_id == "dice" else base_style)
        self.btn_tab_hist.setStyleSheet(purple_active if tab_id == "history" else base_style)
        self.btn_tab_char.setStyleSheet(green_active if tab_id == "character" else base_style)

        if tab_id == "dice":
            self.pages.setCurrentWidget(self.page_dice)
        elif tab_id == "history":
            self._refresh_history_feed()
            self.pages.setCurrentWidget(self.page_history)
        elif tab_id == "character":
            self.pages.setCurrentWidget(self.page_character)

    def _build_collapsed_view(self):
        self.collapsed_widget = QWidget()
        c_layout = QHBoxLayout(self.collapsed_widget)
        c_layout.setContentsMargins(10, 4, 10, 4)
        c_layout.setSpacing(8)

        self.c_cat = KopiCatAvatar(self)
        self.c_label = QLabel("🎲 D&D Dice Widget")
        self.c_label.setStyleSheet("color: #f3f4f6; font-weight: bold; font-size: 12px;")

        self.btn_expand = QPushButton("▼")
        self.btn_expand.setFixedSize(24, 24)
        self.btn_expand.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: #f3f4f6;
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_expand.clicked.connect(self.toggle_collapse)

        c_layout.addWidget(self.c_cat)
        c_layout.addWidget(self.c_label)
        c_layout.addStretch()
        c_layout.addWidget(self.btn_expand)
        self.collapsed_widget.hide()
        self.container_layout.addWidget(self.collapsed_widget)

    def _build_dice_page(self):
        self.page_dice = QWidget()
        p_layout = QVBoxLayout(self.page_dice)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(8)

        self.lbl_char_tag = QLabel(self.engine.character_name)
        self.lbl_char_tag.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        p_layout.addWidget(self.lbl_char_tag)

        self._build_result_card(p_layout)
        self._build_dice_selector(p_layout)
        self._build_roll_modifiers(p_layout)
        self._build_action_buttons(p_layout)

        self.pages.addWidget(self.page_dice)

    def _build_result_card(self, parent_layout):
        self.result_card = QFrame()
        self.result_card.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: 16px;
            }}
        """)
        rc_layout = QVBoxLayout(self.result_card)
        rc_layout.setContentsMargins(12, 10, 12, 10)
        rc_layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        left_info = QVBoxLayout()
        left_info.setSpacing(2)
        self.lbl_roll_type = QLabel("CUSTOM: ROLL")
        self.lbl_roll_type.setStyleSheet("color: #9ca3af; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
        self.lbl_formula = QLabel("Ready to roll")
        self.lbl_formula.setStyleSheet("color: #e5e7eb; font-size: 12px; font-weight: 600;")
        left_info.addWidget(self.lbl_roll_type)
        left_info.addWidget(self.lbl_formula)
        top_row.addLayout(left_info)

        top_row.addStretch()

        self.lbl_total = QLabel("--")
        self.lbl_total.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 32px; font-weight: 900;")
        top_row.addWidget(self.lbl_total)

        rc_layout.addLayout(top_row)

        self.lbl_crit_banner = QLabel("")
        self.lbl_crit_banner.setStyleSheet("font-size: 11px; font-weight: bold; border-radius: 8px; padding: 2px 8px;")
        self.lbl_crit_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_crit_banner.hide()
        rc_layout.addWidget(self.lbl_crit_banner)

        self.dice_grid_scroll = QScrollArea()
        self.dice_grid_scroll.setFixedHeight(105)
        self.dice_grid_scroll.setWidgetResizable(True)
        self.dice_grid_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.dice_grid_container = QWidget()
        self.dice_grid_layout = QGridLayout(self.dice_grid_container)
        self.dice_grid_layout.setContentsMargins(2, 2, 2, 2)
        self.dice_grid_layout.setSpacing(6)
        self.dice_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.dice_grid_scroll.setWidget(self.dice_grid_container)
        rc_layout.addWidget(self.dice_grid_scroll)

        parent_layout.addWidget(self.result_card)

    def _build_dice_selector(self, parent_layout):
        self.selector_card = QFrame()
        self.selector_card.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: 16px;
            }}
        """)
        sc_layout = QVBoxLayout(self.selector_card)
        sc_layout.setContentsMargins(8, 8, 8, 8)
        sc_layout.setSpacing(4)

        d_grid = QGridLayout()
        d_grid.setContentsMargins(0, 0, 0, 0)
        d_grid.setSpacing(4)

        self.dice_buttons = {}
        order = [
            ("d20", 0, 0), ("d12", 0, 1), ("d100", 0, 2), ("d10", 0, 3),
            ("d8", 1, 0),  ("d6", 1, 1),  ("d4", 1, 2)
        ]
        for die, r, c in order:
            btn = DiceButton(die, self)
            btn.clicked.connect(self.on_die_clicked)
            btn.right_clicked.connect(self.on_die_right_clicked)
            self.dice_buttons[die] = btn
            d_grid.addWidget(btn, r, c, Qt.AlignmentFlag.AlignCenter)

        sc_layout.addLayout(d_grid)
        parent_layout.addWidget(self.selector_card)

    def _build_roll_modifiers(self, parent_layout):
        mod_widget = QWidget()
        m_layout = QHBoxLayout(mod_widget)
        m_layout.setContentsMargins(0, 0, 0, 0)
        m_layout.setSpacing(6)

        self.btn_mode_norm = QPushButton("Normal")
        self.btn_mode_adv = QPushButton("Adv")
        self.btn_mode_dis = QPushButton("Disadv")

        for b, m in [(self.btn_mode_norm, "normal"), (self.btn_mode_adv, "advantage"), (self.btn_mode_dis, "disadvantage")]:
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(26)
            b.clicked.connect(lambda _, mode=m: self.set_roll_mode(mode))
            m_layout.addWidget(b)

        self.update_mode_buttons()
        m_layout.addStretch()

        lbl_mod = QLabel("Mod:")
        lbl_mod.setStyleSheet("color: #9ca3af; font-size: 11px; font-weight: 600;")
        m_layout.addWidget(lbl_mod)

        btn_dec_mod = QPushButton("-")
        btn_dec_mod.setFixedSize(24, 24)
        btn_dec_mod.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dec_mod.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                color: #e5e7eb;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.2); }
        """)
        btn_dec_mod.clicked.connect(self.decrement_modifier)

        self.lbl_mod_val = QLabel("+0")
        self.lbl_mod_val.setStyleSheet("color: #f3f4f6; font-weight: bold; font-size: 12px; min-width: 26px;")
        self.lbl_mod_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_inc_mod = QPushButton("+")
        btn_inc_mod.setFixedSize(24, 24)
        btn_inc_mod.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_inc_mod.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                color: #e5e7eb;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.2); }
        """)
        btn_inc_mod.clicked.connect(self.increment_modifier)

        m_layout.addWidget(btn_dec_mod)
        m_layout.addWidget(self.lbl_mod_val)
        m_layout.addWidget(btn_inc_mod)

        parent_layout.addWidget(mod_widget)

    def _build_action_buttons(self, parent_layout):
        act_widget = QWidget()
        a_layout = QHBoxLayout(act_widget)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.setSpacing(8)

        self.btn_reset = QPushButton("CLEAR DICE")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setFixedHeight(40)
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                color: {COLOR_TEXT_MAIN};
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.16);
            }}
        """)
        self.btn_reset.clicked.connect(self.on_clear_clicked)
        a_layout.addWidget(self.btn_reset, 1)

        self.btn_roll = QPushButton("ROLL")
        self.btn_roll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_roll.setFixedHeight(40)
        self.btn_roll.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_RED_HOVER}, stop:1 {COLOR_RED});
                border: 1px solid rgba(255, 100, 100, 0.5);
                border-radius: 20px;
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f87171, stop:1 #dc2626);
                border: 1px solid #ffffff;
            }}
            QPushButton:pressed {{
                background: #b91c1c;
            }}
        """)
        self.btn_roll.clicked.connect(self.on_roll_clicked)
        a_layout.addWidget(self.btn_roll, 2)

        parent_layout.addWidget(act_widget)

    def _build_history_page(self):
        self.page_history = QWidget()
        ph_layout = QVBoxLayout(self.page_history)
        ph_layout.setContentsMargins(0, 0, 0, 0)
        ph_layout.setSpacing(8)

        h_bar = QHBoxLayout()
        lbl_h_title = QLabel("Roll History")
        lbl_h_title.setStyleSheet(f"color: {COLOR_PURPLE}; font-size: 13px; font-weight: bold;")
        h_bar.addWidget(lbl_h_title)
        h_bar.addStretch()

        btn_clear_hist = QPushButton("Clear All")
        btn_clear_hist.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_hist.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
                color: #9ca3af;
                font-size: 10px;
                padding: 3px 8px;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        """)
        btn_clear_hist.clicked.connect(self.on_clear_history_clicked)
        h_bar.addWidget(btn_clear_hist)
        ph_layout.addLayout(h_bar)

        self.hist_scroll = QScrollArea()
        self.hist_scroll.setWidgetResizable(True)
        self.hist_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.hist_container = QWidget()
        self.hist_layout = QVBoxLayout(self.hist_container)
        self.hist_layout.setContentsMargins(0, 0, 0, 0)
        self.hist_layout.setSpacing(8)
        self.hist_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.hist_scroll.setWidget(self.hist_container)
        ph_layout.addWidget(self.hist_scroll)

        self.pages.addWidget(self.page_history)

    def _build_character_page(self):
        self.page_character = QWidget()
        pc_layout = QVBoxLayout(self.page_character)
        pc_layout.setContentsMargins(0, 0, 0, 0)
        pc_layout.setSpacing(10)

        lbl_c_title = QLabel("Character Profile & Presets")
        lbl_c_title.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 13px; font-weight: bold;")
        pc_layout.addWidget(lbl_c_title)

        card_name = QFrame()
        card_name.setStyleSheet(f"background: {COLOR_CARD}; border: 1px solid {COLOR_CARD_BORDER}; border-radius: 14px;")
        cn_layout = QVBoxLayout(card_name)
        cn_layout.setContentsMargins(12, 10, 12, 10)
        cn_layout.setSpacing(4)

        lbl_cn = QLabel("Character Name:")
        lbl_cn.setStyleSheet("color: #9ca3af; font-size: 11px; font-weight: bold;")
        self.txt_char_name = QLineEdit(self.engine.character_name)
        self.txt_char_name.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #f3f4f6;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.txt_char_name.textChanged.connect(self.on_character_name_changed)
        cn_layout.addWidget(lbl_cn)
        cn_layout.addWidget(self.txt_char_name)
        pc_layout.addWidget(card_name)

        lbl_presets = QLabel("Quick Roll Presets:")
        lbl_presets.setStyleSheet("color: #9ca3af; font-size: 11px; font-weight: bold; margin-top: 4px;")
        pc_layout.addWidget(lbl_presets)

        presets = [
            ("⚡ Initiative (1d20)", {"d20": 1}, 0),
            ("🔥 Fireball! (8d6)", {"d6": 8}, 0),
            ("🗡️ Sneak Attack (3d6)", {"d6": 3}, 0),
            ("🧪 Healing Potion (2d4+2)", {"d4": 2}, 2),
            ("✨ Eldritch Blast (1d10)", {"d10": 1}, 0),
            ("⚔️ Greatsword (2d6+3)", {"d6": 2}, 3),
        ]

        p_grid = QGridLayout()
        p_grid.setSpacing(6)
        for i, (name, d_map, mod) in enumerate(presets):
            btn_p = QPushButton(name)
            btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_p.setFixedHeight(32)
            btn_p.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_CARD};
                    border: 1px solid {COLOR_CARD_BORDER};
                    border-radius: 10px;
                    color: {COLOR_TEXT_MAIN};
                    font-size: 11px;
                    font-weight: 600;
                    text-align: left;
                    padding-left: 8px;
                }}
                QPushButton:hover {{
                    background: {COLOR_CARD_HOVER};
                    border: 1px solid rgba(16, 185, 129, 0.4);
                    color: {COLOR_GREEN};
                }}
            """)
            btn_p.clicked.connect(lambda _, dm=d_map, m=mod: self.apply_preset(dm, m))
            p_grid.addWidget(btn_p, i // 2, i % 2)

        pc_layout.addLayout(p_grid)
        pc_layout.addStretch()

        self.pages.addWidget(self.page_character)

    def apply_preset(self, dice_map, mod):
        self.dice_counts = {d: 0 for d in DICE_TYPES}
        for d, c in dice_map.items():
            self.dice_counts[d] = c
        self.modifier = mod
        self.lbl_mod_val.setText(f"{'+' if mod >= 0 else ''}{mod}")
        for d, btn in self.dice_buttons.items():
            btn.set_count(self.dice_counts.get(d, 0))
        self.set_active_tab("dice")
        self.on_roll_clicked()

    def on_die_clicked(self, die_name):
        self.dice_counts[die_name] += 1
        self.dice_buttons[die_name].set_count(self.dice_counts[die_name])

    def on_die_right_clicked(self, die_name):
        if self.dice_counts[die_name] > 0:
            self.dice_counts[die_name] -= 1
            self.dice_buttons[die_name].set_count(self.dice_counts[die_name])

    def on_clear_clicked(self):
        for d in DICE_TYPES:
            self.dice_counts[d] = 0
            self.dice_buttons[d].set_count(0)
        self.modifier = 0
        self.lbl_mod_val.setText("+0")
        self.set_roll_mode("normal")
        self.lbl_total.setText("--")
        self.lbl_formula.setText("Ready to roll")
        if hasattr(self, 'lbl_crit_banner'):
            self.lbl_crit_banner.setText("")
            self.lbl_crit_banner.hide()
        if hasattr(self, 'dice_grid_layout'):
            while self.dice_grid_layout.count():
                item = self.dice_grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def increment_modifier(self):
        self.modifier += 1
        self.lbl_mod_val.setText(f"{'+' if self.modifier >= 0 else ''}{self.modifier}")

    def decrement_modifier(self):
        self.modifier -= 1
        self.lbl_mod_val.setText(f"{'+' if self.modifier >= 0 else ''}{self.modifier}")

    def set_roll_mode(self, mode):
        self.roll_mode = mode
        self.update_mode_buttons()

    def update_mode_buttons(self):
        base_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 11px;
                color: #9ca3af;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.12); }
        """
        active_style = f"""
            QPushButton {{
                background: {COLOR_GOLD_BG};
                border: 1px solid {COLOR_GOLD_BORDER};
                border-radius: 11px;
                color: {COLOR_GOLD};
                font-weight: bold;
                font-size: 11px;
                padding: 0 8px;
            }}
        """
        self.btn_mode_norm.setStyleSheet(active_style if self.roll_mode == "normal" else base_style)
        self.btn_mode_adv.setStyleSheet(active_style if self.roll_mode == "advantage" else base_style)
        self.btn_mode_dis.setStyleSheet(active_style if self.roll_mode == "disadvantage" else base_style)

    def on_character_name_changed(self, text):
        self.engine.character_name = text.strip() or "Malexius"
        self.lbl_char_tag.setText(self.engine.character_name)
        self.engine.save_data()

    def on_clear_history_clicked(self):
        self.engine.clear_history()
        self._refresh_history_feed()

    def on_roll_clicked(self):
        self.target_result = self.engine.roll(self.dice_counts, self.modifier, self.roll_mode)
        self.anim_ticks = 0
        self.btn_roll.setEnabled(False)
        self.roll_animation_timer.start(40)

    def _animate_roll_tick(self):
        self.anim_ticks += 1
        if self.anim_ticks < 8:
            import random
            fake_total = random.randint(1, 99)
            self.lbl_total.setText(str(fake_total))
        else:
            self.roll_animation_timer.stop()
            self.btn_roll.setEnabled(True)
            self._render_result(self.target_result)

    def _render_result(self, result):
        self.last_result = result
        self.lbl_total.setText(str(result.total))
        self.lbl_formula.setText(result.formula_str())

        if result.is_crit_hit:
            self.mascot.set_mood("happy")
            self.c_cat.set_mood("happy")
            self.lbl_crit_banner.setText("✨ CRITICAL HIT! (NATURAL 20) ✨")
            self.lbl_crit_banner.setStyleSheet(f"background: {COLOR_GOLD_BG}; color: {COLOR_GOLD}; border: 1px solid {COLOR_GOLD_BORDER};")
            self.lbl_crit_banner.show()
        elif result.is_crit_fail:
            self.mascot.set_mood("shocked")
            self.c_cat.set_mood("shocked")
            self.lbl_crit_banner.setText("💀 CRITICAL MISS! (NATURAL 1) 💀")
            self.lbl_crit_banner.setStyleSheet("background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);")
            self.lbl_crit_banner.show()
        else:
            self.mascot.set_mood("normal")
            self.c_cat.set_mood("normal")
            self.lbl_crit_banner.hide()

        self.c_label.setText(f"🎲 {result.formula_str()} = {result.total}")

        while self.dice_grid_layout.count():
            item = self.dice_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 6
        for i, r in enumerate(result.rolls_detail):
            tile = DiceResultTile(r["die"], r["value"], r.get("dropped", False), self)
            self.dice_grid_layout.addWidget(tile, i // cols, i % cols)

    def _refresh_history_feed(self):
        while self.hist_layout.count():
            item = self.hist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.engine.history:
            empty_lbl = QLabel("No rolls yet. Roll the dice to see history!")
            empty_lbl.setStyleSheet("color: #6b7280; font-size: 12px; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hist_layout.addWidget(empty_lbl)
            return

        for r in self.engine.history:
            card = self._create_history_item_card(r)
            self.hist_layout.addWidget(card)

    def _create_history_item_card(self, res):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: {COLOR_CARD_HOVER};
            }}
        """)
        l = QVBoxLayout(frame)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(3)

        lbl_c = QLabel(res.character_name)
        lbl_c.setStyleSheet("color: #9ca3af; font-size: 11px; font-weight: 600;")
        l.addWidget(lbl_c)

        row = QHBoxLayout()
        pill = QFrame()
        pill.setStyleSheet("""
            QFrame {
                background: rgba(59, 130, 246, 0.12);
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 8px;
            }
        """)
        pl = QHBoxLayout(pill)
        pl.setContentsMargins(8, 3, 8, 3)

        lbl_custom = QLabel("CUSTOM: ROLL")
        lbl_custom.setStyleSheet("color: #e5e7eb; font-size: 10px; font-weight: bold;")
        pl.addWidget(lbl_custom)
        pl.addStretch()

        lbl_val = QLabel(str(res.total))
        lbl_val.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 900;")
        pl.addWidget(lbl_val)

        row.addWidget(pill)
        l.addLayout(row)

        lbl_dt = QLabel(f"{res.formula_str()} = {res.detail_math_str()}")
        lbl_dt.setStyleSheet("color: #6b7280; font-size: 10px;")
        l.addWidget(lbl_dt)

        return frame

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.btn_pin.setStyleSheet(f"background: {COLOR_GOLD_BG}; color: {COLOR_GOLD}; border: 1px solid {COLOR_GOLD_BORDER}; border-radius: 13px;")
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.btn_pin.setStyleSheet(f"background: rgba(255, 255, 255, 0.06); color: {COLOR_TEXT_MUTED}; border-radius: 13px;")
        self.show()

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.header_widget.hide()
            self.pages.hide()
            self.collapsed_widget.show()
            self.setFixedSize(self.collapsed_width, self.collapsed_height)
            screen_geom = self.screen().geometry()
            self.move(int((screen_geom.width() - self.collapsed_width) / 2), 10)
        else:
            self.collapsed_widget.hide()
            self.header_widget.show()
            self.pages.show()
            self.setFixedSize(self.normal_width, self.normal_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radius = 20.0 if not self.is_collapsed else 16.0

        bg_gradient = QLinearGradient(bg_rect.topLeft(), bg_rect.bottomLeft())
        bg_gradient.setColorAt(0.0, QColor(14, 15, 18, 245))
        bg_gradient.setColorAt(1.0, QColor(10, 11, 13, 248))

        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1.2))
        painter.drawRoundedRect(bg_rect, radius, radius)
