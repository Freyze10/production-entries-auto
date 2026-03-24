class AppStyles:
    """Tailwind-inspired design system for PyQt6/QSS — Clean Teal & Slate (Corporate)"""

    # ── Primary: Teal ──────────────────────────────────────────────────────────
    TEAL_400 = "#2DD4BF"   # primary-light
    TEAL_500 = "#14B8A6"   # primary
    TEAL_600 = "#0D9488"   # primary-hover
    TEAL_700 = "#0F766E"   # primary-dark

    # ── Accent: Steel Blue ─────────────────────────────────────────────────────
    STEEL_400 = "#60A5FA"
    STEEL_500 = "#3B82F6"

    # ── Semantic ───────────────────────────────────────────────────────────────
    EMERALD_500 = "#10B981"  # success
    EMERALD_600 = "#059669"

    AMBER_200  = "#FDECCE"   # warning
    AMBER_500  = "#F59E0B"
    AMBER_700  = "#B45309"

    RED_500    = "#EF4444"   # danger
    RED_600    = "#DC2626"

    BLUE_500   = "#3B82F6"   # info
    BLUE_600   = "#2563EB"

    # ── Slate neutrals ────────────────────────────────────────────────────────
    SLATE_50  = "#F8FAFC"
    SLATE_100 = "#F1F5F9"
    SLATE_200 = "#E2E8F0"
    SLATE_300 = "#CBD5E1"
    SLATE_400 = "#94A3B8"
    SLATE_500 = "#64748B"
    SLATE_600 = "#475569"
    SLATE_700 = "#334155"
    SLATE_800 = "#1E293B"
    SLATE_900 = "#0F172A"

    # ── Text ──────────────────────────────────────────────────────────────────
    TEXT_PRIMARY   = SLATE_900
    TEXT_SECONDARY = SLATE_500
    TEXT_TERTIARY  = SLATE_400
    TEXT_INVERSE   = SLATE_50

    # ── Backgrounds ───────────────────────────────────────────────────────────
    BG_BASE     = SLATE_50
    BG_SURFACE  = "white"
    BG_GRAY = SLATE_200
    BG_DARK     = SLATE_900

    # ── Borders & focus ───────────────────────────────────────────────────────
    BORDER       = SLATE_200
    BORDER_FOCUS = TEAL_500
    RING_FOCUS   = "0 0 0 3px rgba(20, 184, 166, 0.2)"  # teal-500/20

    # ── Shadows ───────────────────────────────────────────────────────────────
    SHADOW_SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    SHADOW    = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    SHADOW_MD = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    SHADOW_LG = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIN STYLESHEET
    # ══════════════════════════════════════════════════════════════════════════
    LOGIN_STYLESHEET = f"""
        #LoginWindow, #FormFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {SLATE_100}, stop:1 #CCFBF1);
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
            border: 1px solid {SLATE_200};
        }}

        #LoginTitle {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: {TEXT_PRIMARY};
        }}

        #InputFrame {{
            background: {SLATE_50};
            border: 2px solid {SLATE_200};
            border-radius: 12px;
            padding: 4px 8px;
        }}

        #InputFrame:focus-within {{
            border-color: {TEAL_500};
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
            color: {SLATE_400};
        }}

        QPushButton#PrimaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {TEAL_500}, stop:1 {TEAL_600});
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
                stop:0 {TEAL_600}, stop:1 {TEAL_700});
        }}

        QPushButton#PrimaryButton:pressed {{
            padding-top: 15px;
            padding-bottom: 13px;
        }}

        QPushButton#PrimaryButton:disabled {{
            background: {SLATE_300};
            color: {SLATE_100};
        }}

        #StatusLabel {{
            color: {RED_500};
            font-weight: 500;
            font-size: 13px;
        }}
    """

    # ══════════════════════════════════════════════════════════════════════════
    #  MAIN WINDOW STYLESHEET
    # ══════════════════════════════════════════════════════════════════════════
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

        /* ── Side Menu ─────────────────────────────────────────────────────── */
        QWidget#SideMenu {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {SLATE_900}, stop:1 {SLATE_800});
            color: white;
            min-width: 240px;
            border-right: 1px solid rgba(255,255,255,0.06);
        }}

        #SideMenu QLabel {{
            color: white;
            font-size: 14px;
        }}

        #SideMenu #MenuLabel {{
            font-size: 11px;
            font-weight: 700;
            color: {SLATE_400};
            padding: 16px 20px 8px 20px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        #SideMenu QPushButton {{
            background: transparent;
            color: {SLATE_300};
            border: none;
            text-align: left;
            padding: 14px 20px;
            font-size: 14px;
            font-weight: 500;
            border-radius: 10px;
            margin: 2px 12px;
        }}

        #SideMenu QPushButton:hover {{
            background: rgba(255,255,255,0.07);
            color: white;
            padding-left: 24px;
        }}

        #SideMenu QPushButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {TEAL_600}, stop:1 {TEAL_500});
            font-weight: 600;
            color: white;
        }}

        QFrame#Separator {{
            background: rgba(255,255,255,0.10);
            height: 1px;
            margin: 10px 0;
        }}

        /* ── Form fields ───────────────────────────────────────────────────── */
        QLineEdit, QComboBox, QDateEdit, QTextEdit {{
            background: white;
            border: 1px solid {SLATE_200};
            border-radius: 8px;
            padding: 4px 6px;
            min-height: 22px;
            color: {TEXT_PRIMARY};
            selection-background-color: {TEAL_400};
        }}

        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
            border-color: {TEAL_500};
            box-shadow: {RING_FOCUS};
            outline: none;
        }}

        QLineEdit:read-only {{
            background: {SLATE_100};
            color: {TEXT_SECONDARY};
        }}

        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {SLATE_400};
        }}
        
        QLabel {{
            font-size: 13px;
            color: {TEXT_PRIMARY};
        }}

        /* ── Base button reset ─────────────────────────────────────────────── */
        QPushButton {{
            background: white;
            border: 1px solid {SLATE_200};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
            color: {TEXT_PRIMARY};
        }}

        QPushButton:hover {{
            background: {SLATE_100};
            border-color: {SLATE_300};
        }}

        QPushButton:pressed {{
            background: {SLATE_200};
        }}

        QPushButton:disabled {{
            background: {SLATE_100};
            color: {SLATE_400};
            border-color: {SLATE_200};
        }}

        /* ┌──────────────────────────────────────────────────────────────────┐
           │  PRIMARY BUTTON                                                  │
           │  Solid teal — highest emphasis                                  │
           │  Use for: Save, Submit, Confirm, Add New                        │
           └──────────────────────────────────────────────────────────────────┘ */
        QPushButton#PrimaryButton {{
            background: {TEAL_500};
            color: white;
            border: none;
            font-weight: 600;
        }}

        QPushButton#PrimaryButton:hover {{
            background: {TEAL_600};
        }}

        QPushButton#PrimaryButton:pressed {{
            background: {TEAL_700};
        }}

        QPushButton#PrimaryButton:disabled {{
            background: {SLATE_300};
            color: {SLATE_50};
            border: none;
        }}

        /* ┌──────────────────────────────────────────────────────────────────┐
           │  SECONDARY BUTTON                                                │
           │  Teal-tinted slate fill + teal border — medium emphasis         │
           │  Use for: Edit, View Details, Export, Back                      │
           └──────────────────────────────────────────────────────────────────┘ */
        QPushButton#SecondaryButton {{
            background: {TEAL_700};
            color: white;
            border: 1px solid {TEAL_600};
            font-weight: 600;
        }}

        QPushButton#SecondaryButton:hover {{
            background: {TEAL_600};
            border-color: {TEAL_500};
            color: white;
        }}

        QPushButton#SecondaryButton:pressed {{
            background: {TEAL_700};
            border-color: {TEAL_600};
            color: white;
        }}

        QPushButton#SecondaryButton:disabled {{
            background: {SLATE_200};
            color: {SLATE_400};
            border-color: {SLATE_300};
        }}

        /* ┌──────────────────────────────────────────────────────────────────┐
           │  TERTIARY BUTTON                                                 │
           │  Solid slate fill — lowest emphasis                             │
           │  Use for: Cancel, Reset, Clear, Close                           │
           └──────────────────────────────────────────────────────────────────┘ */
        QPushButton#TertiaryButton {{
            background: {SLATE_600};
            color: white;
            border: 1px solid {SLATE_300};
            font-weight: 600;
        }}

        QPushButton#TertiaryButton:hover {{
            background: {SLATE_700};
            border-color: {SLATE_400};
        }}

        QPushButton#TertiaryButton:pressed {{
            background: {SLATE_400};
            color: {SLATE_900};
            border-color: {SLATE_500};
        }}

        QPushButton#TertiaryButton:disabled {{
            background: {SLATE_100};
            color: {SLATE_300};
            border-color: {SLATE_200};
        }}

        /* ── Semantic buttons ──────────────────────────────────────────────── */
        QPushButton#SuccessButton       {{ background: {EMERALD_500}; color: white; border: none; font-weight: 600; }}
        QPushButton#SuccessButton:hover {{ background: {EMERALD_600}; }}

        QPushButton#DangerButton        {{ background: {RED_500};     color: white; border: none; font-weight: 600; }}
        QPushButton#DangerButton:hover  {{ background: {RED_600};     }}

        QPushButton#WarningButton       {{ background: {AMBER_500};   color: {SLATE_900}; border: none; font-weight: 600; }}
        QPushButton#WarningButton:hover {{ background: {AMBER_700};   color: white; }}

        QPushButton#InfoButton          {{ background: {BLUE_500};    color: white; border: none; font-weight: 600; }}
        QPushButton#InfoButton:hover    {{ background: {BLUE_600};    }}

        /* ── Table ─────────────────────────────────────────────────────────── */
        QTableView {{
            background: white;
            border: 1px solid {SLATE_200};
            border-radius: 10px;
            gridline-color: {SLATE_100};
            alternate-background-color: {SLATE_200};
            font-size: 13px;
        }}

        QHeaderView::section {{
            background: {TEXT_TERTIARY};
            color: {SLATE_100};
            padding: 6px 0px;
            border-bottom: 2px solid {TEAL_600};
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            height: 18px;
        }}

        QTableView::item {{
            padding-left: 5px;
            border: none;
        }}

        QTableView::item:selected {{
            background: {TEAL_400};
            color: {SLATE_900};
        }}

        QTableView::item:hover {{
            background: rgba(20, 184, 166, 0.07);
        }}

        /* ── Tabs ──────────────────────────────────────────────────────────── */
        QTabWidget::pane {{
            border: 1px solid {SLATE_200};
            border-top: none;
            background: white;
            padding: 16px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        }}

        QTabBar::tab {{
            background: {SLATE_100};
            border: 1px solid {SLATE_200};
            border-bottom: none;
            padding: 12px 28px;
            margin-right: 2px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            color: {TEXT_SECONDARY};
            font-weight: 500;
        }}

        QTabBar::tab:hover {{
            background: {SLATE_50};
            color: {TEXT_PRIMARY};
        }}

        QTabBar::tab:selected {{
            background: white;
            color: {TEAL_600};
            border-bottom: 3px solid {TEAL_500};
            font-weight: 600;
        }}

        /* ── Cards & Groups ────────────────────────────────────────────────── */
        QGroupBox, QFrame#ContentCard, QFrame#HeaderCard {{
            background: white;
            border: 1px solid {SLATE_200};
            border-radius: 12px;
            padding: 16px;
            margin-top: 1.25rem;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            top: 6px;
            padding: 0 10px;
            color: {TEAL_600};
            font-weight: 700;
            font-size: 16px;
            background: transparent;
        }}

        /* ── Scrollbars ────────────────────────────────────────────────────── */
        QScrollBar:vertical {{
            background: {SLATE_100};
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: {SLATE_400};
            border-radius: 5px;
            min-height: 40px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {SLATE_500};
        }}

        /* ── Card header accent ────────────────────────────────────────────── */
        QLabel#card_header {{
            color: {TEAL_500};
        }}

        QLabel#table_label {{
            color: {TEXT_PRIMARY};
        }}
        QLineEdit#gray_bg{{
            background-color: {BG_GRAY};
        }}
        QLineEdit#required{{
            background-color: {AMBER_200};
        }}
        QCheckBox#RawMaterialCheck::indicator,
        QCheckBox#NonRawMaterialCheck::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {SLATE_300};
            border-radius: 4px;
            background-color: white;
        }}
    
        QCheckBox#RawMaterialCheck::indicator:checked {{
            background-color: {EMERALD_500};     /* Green for Raw Material */
            border: 2px solid {EMERALD_500};
        }}
    
        QCheckBox#NonRawMaterialCheck::indicator:checked {{
            background-color: {AMBER_500};     /* Amber for Non-Raw Material */
            border: 2px solid {AMBER_500};
        }}
    
        QCheckBox#RawMaterialCheck::indicator:hover,
        QCheckBox#NonRawMaterialCheck::indicator:hover {{
            border: 2px solid {SLATE_600};
        }}
    """