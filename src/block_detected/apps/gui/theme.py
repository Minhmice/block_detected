"""Robo-Vision OS v2.4 theme — ported from example_ui/stitch_block_pickup_vision_console/DESIGN.md."""

COLORS = {
    "bg": "#0b1326",
    "surface_lowest": "#060e20",
    "surface_low": "#131b2e",
    "surface": "#171f33",
    "surface_high": "#2d3449",
    "outline": "#3d494c",
    "text": "#dae2fd",
    "text_muted": "#bcc9cd",
    "text_dim": "#869397",
    "primary": "#4cd7f6",
    "primary_dark": "#003640",
    "secondary": "#4edea3",
    "orange": "#f59e0b",
    "error": "#ffb4ab",
    "error_dark": "#690005",
}

RADII = {"sm": 4, "md": 8, "lg": 10}
SPACING = {"sm": 8, "md": 12, "lg": 16}

QSS_BASE = f"""
QWidget {{
    background: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: "Inter", "SF Pro Text", Arial, sans-serif;
    font-size: 13px;
}}
QLabel#BrandTitle {{
    color: {COLORS["primary"]};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#CapsLabel {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
}}
QLabel#MetricPrimary {{ color: {COLORS["primary"]}; font-weight: 700; font-family: "JetBrains Mono", Menlo, monospace; }}
QLabel#MetricSecondary {{ color: {COLORS["secondary"]}; font-weight: 700; font-family: "JetBrains Mono", Menlo, monospace; }}
QLabel#MetricRender {{ color: {COLORS["orange"]}; font-weight: 700; font-family: "JetBrains Mono", Menlo, monospace; }}
QLabel#MetricMuted {{ color: {COLORS["text_muted"]}; font-family: "JetBrains Mono", Menlo, monospace; }}
QLabel#PrimaryDetectName {{
    color: {COLORS["primary"]};
    font-size: 20px;
    font-weight: 600;
    font-family: "JetBrains Mono", Menlo, monospace;
}}
QLabel#PrimaryDetectConf {{
    color: {COLORS["secondary"]};
    font-family: "JetBrains Mono", Menlo, monospace;
    font-size: 14px;
}}
QLabel#ComingSoon {{
    color: {COLORS["text"]};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.2em;
    border: 1px solid {COLORS["outline"]};
    background: {COLORS["surface_high"]};
    padding: 8px 14px;
    border-radius: {RADII["md"]}px;
}}
QLabel#Preview {{
    background: {COLORS["surface_lowest"]};
    border: none;
    color: {COLORS["text_dim"]};
}}
QLabel#PreviewOverlay {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-family: "JetBrains Mono", Menlo, monospace;
    background: rgba(6, 14, 32, 180);
    padding: 4px 8px;
}}
QLabel#RestartHint {{ color: {COLORS["orange"]}; font-size: 11px; }}
QLabel#LiveBadge {{
    color: {COLORS["secondary"]};
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    border: 1px solid rgba(78, 222, 163, 0.3);
    background: rgba(78, 222, 163, 0.1);
    padding: 2px 6px;
    border-radius: {RADII["sm"]}px;
}}
QFrame#HeaderBar, QFrame#ViewportToolbar, QFrame#Panel {{
    background: {COLORS["surface_low"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
}}
QFrame#Sidebar {{
    background: {COLORS["surface_lowest"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
}}
QFrame#PreviewFrame {{
    background: {COLORS["surface_lowest"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
}}
QFrame#AccordionSection {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
}}
QFrame#AccordionBody {{
    background: {COLORS["surface_lowest"]};
    border-top: 1px solid {COLORS["outline"]};
}}
"""

QSS_BUTTONS = f"""
QPushButton#NavButton {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
    padding: 10px 16px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
}}
QPushButton#NavButton:hover {{ background: {COLORS["surface_high"]}; }}
QPushButton#NavButton:disabled {{ color: #5a6670; background: {COLORS["surface_low"]}; }}
QPushButton#StartButton {{
    background: {COLORS["primary"]};
    color: {COLORS["primary_dark"]};
    border: none;
    border-radius: {RADII["md"]}px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.06em;
}}
QPushButton#StartButton:hover {{ background: #6de4ff; }}
QPushButton#StopButton {{
    background: {COLORS["error"]};
    color: {COLORS["error_dark"]};
    border: none;
    border-radius: {RADII["md"]}px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.06em;
}}
QPushButton#StopButton:hover {{ background: #ffc9c2; }}
QPushButton#ApplyButton {{
    background: {COLORS["primary"]};
    color: {COLORS["primary_dark"]};
    border: none;
    border-radius: {RADII["md"]}px;
    padding: 12px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.05em;
}}
QPushButton#SaveButton {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
    padding: 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
}}
QPushButton#DeleteButton {{
    background: transparent;
    border: 1px solid #ff7f8b;
    color: #ff7f8b;
    border-radius: {RADII["md"]}px;
    padding: 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
}}
QPushButton#DeleteButton:hover {{ background: rgba(255, 127, 139, 0.1); }}
QPushButton#AccordionToggle {{
    background: transparent;
    border: none;
    text-align: left;
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: {COLORS["text_muted"]};
}}
QPushButton#AccordionToggle:hover {{ background: {COLORS["surface_high"]}; }}
"""

QSS_CONTROLS = f"""
QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS["surface_high"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: {COLORS["primary"]};
}}
QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {{
    background: {COLORS["bg"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["sm"]}px;
    padding: 4px 6px;
    min-height: 24px;
    color: {COLORS["text"]};
    font-family: "JetBrains Mono", Menlo, monospace;
    font-size: 12px;
}}
QDoubleSpinBox::up-button, QSpinBox::up-button,
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    width: 0px;
    height: 0px;
    border: none;
}}
QCheckBox {{ spacing: 8px; color: {COLORS["text"]}; }}
QCheckBox:disabled {{ color: #5a6670; }}
QProgressBar {{
    border: none;
    background: {COLORS["surface"]};
    height: 8px;
    border-radius: 4px;
}}
QProgressBar::chunk {{ background: {COLORS["primary"]}; border-radius: 4px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    width: 8px;
    background: {COLORS["bg"]};
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["outline"]};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {COLORS["text_dim"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 2px 4px;
    border: none;
}}
QListWidget::item:hover {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: {RADII["sm"]}px;
}}
"""

QSS_TOGGLE_PILL = f"""
QCheckBox#TogglePill {{
    spacing: 8px;
    padding: 6px 12px;
    background: {COLORS["surface_high"]};
    border: 1px solid {COLORS["outline"]};
    border-radius: {RADII["md"]}px;
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
}}
QCheckBox#TogglePill:checked {{
    border-color: {COLORS["primary"]};
    color: {COLORS["text"]};
}}
QCheckBox#TogglePill::indicator {{
    width: 36px;
    height: 20px;
    border-radius: 10px;
    background: {COLORS["outline"]};
}}
QCheckBox#TogglePill::indicator:checked {{
    background: #004e5c;
    image: none;
}}
QCheckBox#TogglePill:disabled {{
    color: #5a6670;
}}
"""

ROBO_VISION_QSS = QSS_BASE + QSS_BUTTONS + QSS_CONTROLS + QSS_TOGGLE_PILL
