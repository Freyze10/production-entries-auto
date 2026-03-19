class AppStyles:
    """Tailwind-inspired design system for PyQt6/QSS"""

    # Main palette (indigo + cyan accent – similar to your original)
    INDIGO_600 = "#4F46E5"  # primary
    INDIGO_700 = "#4338CA"  # primary-hover
    INDIGO_500 = "#6366F1"
    INDIGO_400 = "#818CF8"  # primary-light

    CYAN_500 = "#06B6D4"  # accent

    EMERALD_500 = "#10B981"  # success
    EMERALD_600 = "#059669"

    AMBER_500 = "#F59E0B"  # warning
    AMBER_700 = "#B45309"

    RED_500 = "#EF4444"  # danger
    RED_600 = "#DC2626"

    BLUE_500 = "#3B82F6"  # info
    BLUE_600 = "#2563EB"

    # Neutrals (gray scale similar to Tailwind gray)
    GRAY_50 = "#F9FAFB"
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    GRAY_300 = "#D1D5DB"
    GRAY_400 = "#9CA3AF"
    GRAY_500 = "#6B7280"
    GRAY_600 = "#4B5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1F2937"
    GRAY_900 = "#111827"

    # Text
    TEXT_PRIMARY = GRAY_900
    TEXT_SECONDARY = GRAY_500
    TEXT_TERTIARY = GRAY_400
    TEXT_INVERSE = GRAY_50

    # Backgrounds
    BG_BASE = GRAY_50
    BG_SURFACE = "white"
    BG_ELEVATED = GRAY_50
    BG_DARK = GRAY_900

    # Borders & focus
    BORDER = GRAY_200
    BORDER_FOCUS = INDIGO_500
    RING_FOCUS = "0 0 0 3px rgba(79, 70, 229, 0.2)"  # indigo-500/20

    # Shadows (very close to Tailwind's default shadows)
    SHADOW_SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    SHADOW = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    SHADOW_MD = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    SHADOW_LG = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"

    LOGIN_STYLESHEET = f"""
        #LoginWindow, #FormFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {GRAY_100}, stop:1 #E0E7FF);
        }}

        QWidget {{
            font-family: "Inter", "Segoe UI", system-ui, sans-serif;
            font-size: 14px;
            color: {TEXT_PRIMARY};
        }}

        #FormFrame {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            border: 1px solid {GRAY_200};
        }}

        #LoginTitle {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: {TEXT_PRIMARY};
        }}

        #InputFrame {{
            background: {GRAY_50};
            border: 2px solid {GRAY_200};
            border-radius: 12px;
            padding: 4px 8px;
        }}

        #InputFrame:focus-within {{
            border-color: {INDIGO_600};
            box-shadow: {RING_FOCUS};
            background: white;
        }}

        QLineEdit {{
            border: none;
            background: transparent;
            padding: 10px 8px;
            font-size: 15px;
            color: {TEXT_PRIMARY};
        }}

        QLineEdit::placeholder {{
            color: {GRAY_400};
        }}

        QPushButton#PrimaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {INDIGO_600}, stop:1 {INDIGO_700});
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 32px;
            font-weight: 600;
            font-size: 15px;
            min-width: 140px;
        }}

        QPushButton#PrimaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {INDIGO_700}, stop:1 #312E81);
        }}

        QPushButton#PrimaryButton:pressed {{
            padding-top: 15px;
            padding-bottom: 13px;
        }}

        QPushButton#PrimaryButton:disabled {{
            background: {GRAY_300};
            color: {GRAY_100};
        }}

        #StatusLabel {{
            color: {RED_500};
            font-weight: 500;
            font-size: 13px;
        }}
    """

    MAIN_WINDOW_STYLESHEET = f"""
        QMainWindow, QStackedWidget > QWidget {{
            background-color: {BG_BASE};
        }}

        QWidget {{
            font-family: "Inter", "Segoe UI", system-ui, sans-serif;
            font-size: 14px;
            color: {TEXT_PRIMARY};
        }}

        QStatusBar, QStatusBar QLabel {{
            background: white;
            color: {TEXT_SECONDARY};
            border-top: 1px solid {BORDER};
            padding: 6px 12px;
            font-size: 12px;
        }}

        QWidget#SideMenu {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {GRAY_900}, stop:1 {GRAY_800});
            color: white;
            min-width: 240px;
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        #SideMenu QLabel {{
            color: white;
            font-size: 14px;
        }}

        #SideMenu #MenuLabel {{
            font-size: 12px;
            font-weight: 700;
            color: {GRAY_400};
            padding: 16px 20px 8px 20px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        #SideMenu QPushButton {{
            background: transparent;
            color: white;
            border: none;
            text-align: left;
            padding: 14px 20px;
            font-size: 14px;
            font-weight: 500;
            border-radius: 10px;
            margin: 2px 12px;
            transition: all 0.15s ease;
        }}

        #SideMenu QPushButton:hover {{
            background: rgba(255,255,255,0.09);
            padding-left: 24px;
        }}

        #SideMenu QPushButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {INDIGO_600}, stop:1 {INDIGO_400});
            font-weight: 600;
            color: white;
        }}

        QFrame#Separator {{
            background: rgba(255,255,255,0.12);
            height: 1px;
            margin: 10px 0;
        }}

        /* Form fields – input, select, textarea */
        QLineEdit, QComboBox, QDateEdit, QTextEdit {{
            background: white;
            border: 1px solid {GRAY_200};
            border-radius: 8px;
            padding: 4px 6px;
            min-height: 26px;
            color: {TEXT_PRIMARY};
            selection-background-color: {INDIGO_400};
        }}

        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
            border-color: {INDIGO_600};
            box-shadow: {RING_FOCUS};
            outline: none;
        }}

        QLineEdit:read-only {{
            background: {GRAY_100};
            color: {TEXT_SECONDARY};
        }}

        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {GRAY_400};
        }}

        /* Buttons – default, primary, success, danger, etc. */
        QPushButton {{
            background: white;
            border: 1px solid {GRAY_200};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
            color: {TEXT_PRIMARY};
        }}

        QPushButton:hover {{
            background: {GRAY_100};
            border-color: {GRAY_300};
        }}

        QPushButton:pressed {{
            background: {GRAY_200};
        }}

        QPushButton#PrimaryButton {{
            background: {INDIGO_600};
            color: white;
            border: none;
            font-weight: 600;
        }}

        QPushButton#PrimaryButton:hover {{
            background: {INDIGO_700};
        }}

        QPushButton#SuccessButton  {{ background: {EMERALD_500}; color: white; border: none; font-weight: 600; }}
        QPushButton#SuccessButton:hover {{ background: {EMERALD_600}; }}

        QPushButton#DangerButton   {{ background: {RED_500};    color: white; border: none; font-weight: 600; }}
        QPushButton#DangerButton:hover  {{ background: {RED_600};    }}

        QPushButton#WarningButton  {{ background: {AMBER_500}; color: {GRAY_900}; border: none; font-weight: 600; }}
        QPushButton#WarningButton:hover {{ background: {AMBER_700}; }}

        QPushButton#InfoButton     {{ background: {BLUE_500};  color: white; border: none; font-weight: 600; }}
        QPushButton#InfoButton:hover    {{ background: {BLUE_600};  }}

        /* Table – card-like with subtle stripes */
        QTableWidget {{
            background: white;
            border: 1px solid {GRAY_200};
            border-radius: 10px;
            gridline-color: {GRAY_200};
            alternate-background-color: {GRAY_50};
        }}

        QHeaderView::section {{
            background: {GRAY_100};
            padding: 10px 8px;
            border-bottom: 2px solid {GRAY_200};
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}

        QTableWidget::item:selected {{
            background: {INDIGO_400};
            color: {GRAY_900};
        }}

        QTableWidget::item:hover {{
            background: rgba(79,70,229,0.07);
        }}

        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {GRAY_200};
            border-top: none;
            background: white;
            padding: 16px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        }}

        QTabBar::tab {{
            background: {GRAY_100};
            border: 1px solid {GRAY_200};
            border-bottom: none;
            padding: 12px 28px;
            margin-right: 2px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            color: {TEXT_SECONDARY};
            font-weight: 500;
        }}

        QTabBar::tab:hover {{
            background: {GRAY_50};
            color: {TEXT_PRIMARY};
        }}

        QTabBar::tab:selected {{
            background: white;
            color: {INDIGO_600};
            border-bottom: 3px solid {INDIGO_600};
            font-weight: 600;
        }}

        /* Cards & Groups */
        QGroupBox, QFrame#ContentCard, QFrame#HeaderCard {{
            background: white;
            border: 1px solid {GRAY_200};
            border-radius: 12px;
            padding: 16px;
            margin-top: 1.25rem;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            top: -10px;
            padding: 0 10px;
            color: {INDIGO_600};
            font-weight: 700;
            background: transparent;
        }}

        /* Scrollbars – cleaner modern look */
        QScrollBar:vertical {{
            background: {GRAY_100};
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: {GRAY_400};
            border-radius: 5px;
            min-height: 40px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {GRAY_500};
        }}
        
        QLabel#card_header {{
            color: {CYAN_500};
        }}
    """