from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QScrollArea, QLineEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF, QFont,
    QLinearGradient, QPainterPath
)
from styles import (
    COLOR_CARD, COLOR_CARD_HOVER, COLOR_CARD_BORDER,
    COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_TEXT_DARK,
    COLOR_GOLD, COLOR_GOLD_BG, COLOR_GOLD_BORDER,
    COLOR_PURPLE, COLOR_PURPLE_BG,
    COLOR_GREEN, COLOR_GREEN_BG,
    COLOR_RED, COLOR_RED_HOVER,
    COLOR_DICE_DEFAULT_TOP, COLOR_DICE_DEFAULT_BOTTOM, COLOR_DICE_BORDER,
    COLOR_CRIT_HIT_TOP, COLOR_CRIT_HIT_BOTTOM, COLOR_CRIT_HIT_BORDER,
    COLOR_CRIT_FAIL_TOP, COLOR_CRIT_FAIL_BOTTOM, COLOR_CRIT_FAIL_BORDER
)

class DiceButton(QWidget):
    clicked = pyqtSignal(str)          # die_name
    right_clicked = pyqtSignal(str)    # die_name

    def __init__(self, die_name, parent=None):
        super().__init__(parent)
        self.die_name = die_name
        self.count = 0
        self.is_hovered = False
        self.setFixedSize(68, 76)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_count(self, count):
        self.count = max(0, count)
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.die_name)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.die_name)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background rounded rect if selected or hovered
        if self.count > 0:
            bg_color = QColor(255, 255, 255, 45 if self.is_hovered else 35)
            border_pen = QPen(QColor(255, 255, 255, 180), 1.5)
        elif self.is_hovered:
            bg_color = QColor(255, 255, 255, 18)
            border_pen = QPen(QColor(255, 255, 255, 60), 1)
        else:
            bg_color = QColor(0, 0, 0, 0)
            border_pen = QPen(QColor(0, 0, 0, 0), 0)

        if bg_color.alpha() > 0:
            painter.setBrush(QBrush(bg_color))
            painter.setPen(border_pen)
            painter.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 14, 14)

        # Draw 2D Dice geometry in center
        cx = w / 2.0
        cy = 28.0
        self._draw_die_geometry(painter, cx, cy)

        # Draw Die Name
        painter.setPen(QColor(COLOR_TEXT_MAIN if self.count > 0 else COLOR_TEXT_MUTED))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold if self.count > 0 else QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(QRectF(0, 52, w, 20), Qt.AlignmentFlag.AlignCenter, self.die_name)

        # Draw Badge Counter at top right
        if self.count > 0:
            badge_radius = 9.0
            bx = w - 14.0
            by = 12.0
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(15, 15, 20), 1.5))
            painter.drawEllipse(QPoint(int(bx), int(by)), int(badge_radius), int(badge_radius))

            painter.setPen(QColor(15, 15, 20))
            badge_font = QFont("Segoe UI", 8, QFont.Weight.ExtraBold)
            painter.setFont(badge_font)
            painter.drawText(QRectF(bx - 9, by - 9, 18, 18), Qt.AlignmentFlag.AlignCenter, str(self.count))

    def _draw_die_geometry(self, painter, cx, cy):
        pen = QPen(QColor(240, 240, 245), 1.6)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 15 if self.count > 0 else 5)))

        d = self.die_name
        if d == "d4":
            # Triangle
            poly = QPolygonF([QPoint(int(cx), int(cy - 14)), QPoint(int(cx + 14), int(cy + 10)), QPoint(int(cx - 14), int(cy + 10))])
            painter.drawPolygon(poly)
            painter.drawLine(QPoint(int(cx), int(cy - 14)), QPoint(int(cx), int(cy + 3)))
            painter.drawLine(QPoint(int(cx - 14), int(cy + 10)), QPoint(int(cx), int(cy + 3)))
            painter.drawLine(QPoint(int(cx + 14), int(cy + 10)), QPoint(int(cx), int(cy + 3)))
        elif d == "d6":
            # Isometric Cube / Square
            s = 11
            painter.drawRoundedRect(QRectF(cx - s, cy - s, s * 2, s * 2), 3, 3)
            # Dots or inner bevel
            painter.drawEllipse(QPoint(int(cx), int(cy)), 2, 2)
        elif d == "d8":
            # Diamond / Octahedron
            poly = QPolygonF([
                QPoint(int(cx), int(cy - 14)),
                QPoint(int(cx + 12), int(cy)),
                QPoint(int(cx), int(cy + 14)),
                QPoint(int(cx - 12), int(cy))
            ])
            painter.drawPolygon(poly)
            painter.drawLine(QPoint(int(cx - 12), int(cy)), QPoint(int(cx + 12), int(cy)))
            painter.drawLine(QPoint(int(cx), int(cy - 14)), QPoint(int(cx), int(cy + 14)))
        elif d == "d10":
            # Kite / Trapezohedron
            poly = QPolygonF([
                QPoint(int(cx), int(cy - 14)),
                QPoint(int(cx + 13), int(cy - 2)),
                QPoint(int(cx), int(cy + 13)),
                QPoint(int(cx - 13), int(cy - 2))
            ])
            painter.drawPolygon(poly)
            painter.drawLine(QPoint(int(cx), int(cy - 14)), QPoint(int(cx), int(cy + 13)))
            painter.drawLine(QPoint(int(cx - 13), int(cy - 2)), QPoint(int(cx), int(cy + 2)))
            painter.drawLine(QPoint(int(cx + 13), int(cy - 2)), QPoint(int(cx), int(cy + 2)))
        elif d == "d12":
            # Dodecahedron (Pentagon Outline)
            poly = QPolygonF([
                QPoint(int(cx), int(cy - 13)),
                QPoint(int(cx + 12), int(cy - 4)),
                QPoint(int(cx + 8), int(cy + 11)),
                QPoint(int(cx - 8), int(cy + 11)),
                QPoint(int(cx - 12), int(cy - 4))
            ])
            painter.drawPolygon(poly)
            inner = QPolygonF([
                QPoint(int(cx), int(cy - 6)),
                QPoint(int(cx + 5), int(cy - 2)),
                QPoint(int(cx + 3), int(cy + 5)),
                QPoint(int(cx - 3), int(cy + 5)),
                QPoint(int(cx - 5), int(cy - 2))
            ])
            painter.drawPolygon(inner)
        elif d == "d20":
            # Hexagonal icosahedron
            poly = QPolygonF([
                QPoint(int(cx), int(cy - 14)),
                QPoint(int(cx + 13), int(cy - 7)),
                QPoint(int(cx + 13), int(cy + 7)),
                QPoint(int(cx), int(cy + 14)),
                QPoint(int(cx - 13), int(cy + 7)),
                QPoint(int(cx - 13), int(cy - 7))
            ])
            painter.drawPolygon(poly)
            inner_triangle = QPolygonF([
                QPoint(int(cx), int(cy + 8)),
                QPoint(int(cx - 10), int(cy - 6)),
                QPoint(int(cx + 10), int(cy - 6))
            ])
            painter.drawPolygon(inner_triangle)
            painter.drawLine(QPoint(int(cx), int(cy - 14)), QPoint(int(cx - 10), int(cy - 6)))
            painter.drawLine(QPoint(int(cx), int(cy - 14)), QPoint(int(cx + 10), int(cy - 6)))
            painter.drawLine(QPoint(int(cx - 13), int(cy + 7)), QPoint(int(cx), int(cy + 8)))
            painter.drawLine(QPoint(int(cx + 13), int(cy + 7)), QPoint(int(cx), int(cy + 8)))
        elif d == "d100":
            # Double kite
            k1 = QPolygonF([QPoint(int(cx - 6), int(cy - 11)), QPoint(int(cx + 3), int(cy - 2)), QPoint(int(cx - 6), int(cy + 10)), QPoint(int(cx - 14), int(cy - 2))])
            k2 = QPolygonF([QPoint(int(cx + 5), int(cy - 11)), QPoint(int(cx + 14), int(cy - 2)), QPoint(int(cx + 5), int(cy + 10)), QPoint(int(cx - 3), int(cy - 2))])
            painter.drawPolygon(k1)
            painter.drawPolygon(k2)


class DiceResultTile(QWidget):
    """2D Icewind Dale Blue Shimmer Dice Cube Tile matching screenshot 3"""
    def __init__(self, die_name, value, is_dropped=False, parent=None):
        super().__init__(parent)
        self.die_name = die_name
        self.value = value
        self.is_dropped = is_dropped
        self.setFixedSize(48, 52)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Shadow
        shadow_rect = QRectF(4, 7, w - 8, h - 8)
        painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 9, 9)

        # Tile Body
        body_rect = QRectF(3, 4, w - 8, h - 10)

        # Gradient based on value / crit
        gradient = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
        if self.die_name == "d20" and self.value == 20:
            gradient.setColorAt(0.0, QColor(COLOR_CRIT_HIT_TOP))
            gradient.setColorAt(1.0, QColor(COLOR_CRIT_HIT_BOTTOM))
            border_pen = QPen(QColor(COLOR_CRIT_HIT_BORDER), 1.8)
        elif self.die_name == "d20" and self.value == 1:
            gradient.setColorAt(0.0, QColor(COLOR_CRIT_FAIL_TOP))
            gradient.setColorAt(1.0, QColor(COLOR_CRIT_FAIL_BOTTOM))
            border_pen = QPen(QColor(COLOR_CRIT_FAIL_BORDER), 1.8)
        elif self.is_dropped:
            gradient.setColorAt(0.0, QColor(40, 45, 55))
            gradient.setColorAt(1.0, QColor(25, 28, 35))
            border_pen = QPen(QColor(80, 85, 95), 1.0)
        else:
            gradient.setColorAt(0.0, QColor(COLOR_DICE_DEFAULT_TOP))
            gradient.setColorAt(1.0, QColor(COLOR_DICE_DEFAULT_BOTTOM))
            border_pen = QPen(QColor(COLOR_DICE_BORDER), 1.3)

        painter.setBrush(QBrush(gradient))
        painter.setPen(border_pen)
        painter.drawRoundedRect(body_rect, 8, 8)

        # Sparkle / Shimmer highlight on top
        if not self.is_dropped:
            highlight = QLinearGradient(body_rect.topLeft(), QPoint(int(body_rect.center().x()), int(body_rect.top() + 14)))
            highlight.setColorAt(0.0, QColor(255, 255, 255, 70))
            highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(highlight))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(body_rect.left() + 2, body_rect.top() + 2, body_rect.width() - 4, 12), 6, 6)

        # Die Number
        text_color = QColor(COLOR_TEXT_DARK if self.is_dropped else COLOR_TEXT_MAIN)
        painter.setPen(text_color)
        font_size = 14 if len(str(self.value)) <= 2 else 11
        font = QFont("Segoe UI", font_size, QFont.Weight.ExtraBold)
        painter.setFont(font)
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, str(self.value))

        # Small die label below (e.g. d6)
        painter.setPen(QColor(COLOR_TEXT_MUTED if not self.is_dropped else COLOR_TEXT_DARK))
        sub_font = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        painter.setFont(sub_font)
        painter.drawText(QRectF(0, h - 9, w, 9), Qt.AlignmentFlag.AlignCenter, self.die_name)


class KopiCatAvatar(QWidget):
    """Kopi pixel cat avatar matching Nuppi's mascot"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(34, 34)
        self.mood = "normal"  # "normal", "happy", "shocked"

    def set_mood(self, mood):
        self.mood = mood
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Draw cute pixel cat
        # Cat head base
        painter.setPen(Qt.PenStyle.NoPen)
        cat_black = QColor(28, 28, 34)
        painter.setBrush(QBrush(cat_black))

        # Ears
        painter.drawRect(7, 6, 6, 8)
        painter.drawRect(21, 6, 6, 8)
        # Head
        painter.drawRoundedRect(5, 11, 24, 17, 4, 4)

        # Eyes based on mood
        if self.mood == "happy":
            # Gold smiling eyes ^ ^
            painter.setPen(QPen(QColor(COLOR_GOLD), 2))
            painter.drawLine(9, 18, 12, 16)
            painter.drawLine(12, 16, 15, 18)
            painter.drawLine(19, 18, 22, 16)
            painter.drawLine(22, 16, 25, 18)
        elif self.mood == "shocked":
            # Big wide red/gold eyes
            painter.setBrush(QBrush(QColor(COLOR_RED)))
            painter.drawRect(10, 16, 4, 4)
            painter.drawRect(20, 16, 4, 4)
        else:
            # Normal bright yellow eyes
            painter.setBrush(QBrush(QColor(COLOR_GOLD)))
            painter.drawRect(10, 16, 4, 4)
            painter.drawRect(20, 16, 4, 4)

        # Nose & Muzzle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(230, 160, 175)))
        painter.drawRect(16, 21, 2, 2)
