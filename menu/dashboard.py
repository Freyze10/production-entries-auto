import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSizePolicy, QTableView)
from PyQt6.QtCore import Qt, QSize
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

import qtawesome as fa
from style.styles import AppStyles
from table_model.model import TableModel


# ── Resolved color constants ─────────────────────────────────────────────────
# Charts sit inside a white card (BG_SURFACE = "white"), so backgrounds match.
_CARD_BG     = "#FFFFFF"          # AppStyles.BG_SURFACE
_CHART_CYAN  = AppStyles.TEAL_500  # #14B8A6  — primary bar/fill color
_CHART_DARK  = AppStyles.SLATE_700 # #334155  — secondary donut slice
_TEXT_LIGHT  = AppStyles.SLATE_400 # #94A3B8  — axis labels / tick text
_TEXT_BODY   = AppStyles.TEXT_PRIMARY   # #0F172A


class MplCanvas(FigureCanvas):
    """Bridge between Matplotlib and PyQt6 — styled to match AppStyles white cards."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        # Match the white DashboardCard background
        self.fig.patch.set_facecolor(_CARD_BG)
        self.axes.set_facecolor(_CARD_BG)

        super().__init__(self.fig)


# ── Dashboard stylesheet (extends MAIN_WINDOW_STYLESHEET) ────────────────────
DASHBOARD_STYLESHEET = f"""
    /* ── Dashboard card (white surface, slate border) ──────────────────── */
    QFrame#DashboardCard {{
        background: white;
        border: 1px solid {AppStyles.SLATE_200};
        border-radius: 12px;
        padding: 16px;
    }}

    /* ── Section title inside cards ─────────────────────────────────────── */
    QLabel#DashTitle {{
        font-size: 11px;
        font-weight: 700;
        color: {AppStyles.SLATE_400};
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    /* ── Big KPI number ─────────────────────────────────────────────────── */
    QLabel#DashValue {{
        font-size: 36px;
        font-weight: 700;
        color: {AppStyles.TEXT_PRIMARY};
    }}

    /* ── Smaller supporting text beside KPI ─────────────────────────────── */
    QLabel#DashSubText {{
        font-size: 14px;
        color: {AppStyles.TEXT_SECONDARY};
    }}

    /* ── Trend badge ("↑ 12% …") ────────────────────────────────────────── */
    QLabel#DashTrend {{
        font-size: 13px;
        font-weight: 600;
        color: {AppStyles.EMERALD_600};
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 3px 10px;
    }}

    /* ── Dashboard table — inherits QTableView base, overrides for dash ── */
    QTableView#DashTable {{
        border: 1px solid {AppStyles.BG_GRAY};
        border-radius: 8px;
        gridline-color: {AppStyles.BG_BASE};
        background-color: {AppStyles.SLATE_200};
        alternate-background-color: {AppStyles.BG_BASE};
        font-size: 13px;
    }}

    QTableView#DashTable::item {{
        padding-left: 5px;
        border: none;
        color: {AppStyles.TEXT_PRIMARY};
    }}

    QTableView#DashTable::item:selected {{
        background-color: {AppStyles.TEAL_400};
        color: {AppStyles.SLATE_900};
    }}

    QTableView#DashTable::item:hover {{
        background-color: rgba(20, 184, 166, 0.07);
    }}
"""


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        # Apply dashboard-specific styles on top of the main window stylesheet
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # ── TOP SECTION: SUMMARY HIGHLIGHT ──────────────────────────────────
        top_card = QFrame()
        top_card.setObjectName("DashboardCard")
        top_card.setFixedHeight(110)
        top_layout = QHBoxLayout(top_card)

        v_box = QVBoxLayout()
        v_box.setSpacing(4)

        title = QLabel("Completed Samples This Week")
        title.setObjectName("DashTitle")

        val_box = QHBoxLayout()
        val_box.setSpacing(6)
        samples_val = QLabel("34")
        samples_val.setObjectName("DashValue")

        samples_text = QLabel("samples")
        samples_text.setObjectName("DashSubText")
        samples_text.setAlignment(Qt.AlignmentFlag.AlignBottom)

        val_box.addWidget(samples_val)
        val_box.addWidget(samples_text)
        val_box.addStretch()

        v_box.addWidget(title)
        v_box.addLayout(val_box)

        top_layout.addLayout(v_box)
        top_layout.addStretch()

        trend_label = QLabel("↑ 12% from last week")
        trend_label.setObjectName("DashTrend")
        top_layout.addWidget(trend_label, alignment=Qt.AlignmentFlag.AlignTop)

        self.main_layout.addWidget(top_card)

        # ── MIDDLE SECTION: ANALYTICS (MATPLOTLIB + SEABORN) ────────────────
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)

        # 1. Horizontal Bar Chart
        rematch_container = self._create_card("Monthly Rematches")
        self.bar_canvas = MplCanvas(self)
        rematch_container.layout().addWidget(self.bar_canvas)
        self.plot_horizontal_bar()

        # 2. Donut Chart
        donut_container = self._create_card("Sample vs Order Generated")
        self.donut_canvas = MplCanvas(self)
        donut_container.layout().addWidget(self.donut_canvas)
        self.plot_donut_chart()

        charts_layout.addWidget(rematch_container, stretch=2)
        charts_layout.addWidget(donut_container, stretch=1)
        self.main_layout.addLayout(charts_layout, stretch=3)

        # ── BOTTOM SECTION: TABLE & STATS ───────────────────────────────────
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        # Table card
        table_card = self._create_card("Recent Matches Record")
        self.table_headers = ["Employee", "Matched", "Rematches", "Success %"]
        self.table_data = [
            ["Person 1", "60", "15", "75%"],
            ["Person 2", "45", "5",  "88%"],
            ["Person 3", "30", "12", "60%"],
        ]

        self.table_view = QTableView()
        self.table_view.setObjectName("DashTable")
        self.table_model = TableModel(self.table_data, self.table_headers)
        self.table_view.setModel(self.table_model)

        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(
            QTableView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(False)

        table_card.layout().addWidget(self.table_view)
        bottom_layout.addWidget(table_card, stretch=3)

        # Stat sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(15)
        self.pending_card, self.lbl_pending_val = self._create_stat_card(
            "Pending Samples", "32", "fa5s.clock")
        self.conv_card, self.lbl_conv_val = self._create_stat_card(
            "Conversion Rate", "77%", "fa5s.percentage")

        sidebar.addWidget(self.pending_card)
        sidebar.addWidget(self.conv_card)
        bottom_layout.addLayout(sidebar, stretch=1)

        self.main_layout.addLayout(bottom_layout, stretch=2)

    # ── HELPERS ─────────────────────────────────────────────────────────────

    def _create_card(self, title: str) -> QFrame:
        """White DashboardCard with an uppercase section title."""
        card = QFrame()
        card.setObjectName("DashboardCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setObjectName("DashTitle")
        layout.addWidget(lbl)
        return card

    def _create_stat_card(self, title: str, val: str, icon_name: str):
        """Stat card with a large KPI value and a teal icon."""
        card = self._create_card(title)
        row = QHBoxLayout()
        row.setSpacing(8)

        value_lbl = QLabel(val)
        value_lbl.setObjectName("DashValue")

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            fa.icon(icon_name, color=AppStyles.TEAL_500).pixmap(QSize(28, 28))
        )
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        row.addWidget(value_lbl)
        row.addStretch()
        row.addWidget(icon_lbl)
        card.layout().addLayout(row)
        return card, value_lbl

    # ── PLOTTING ────────────────────────────────────────────────────────────

    def plot_horizontal_bar(self):
        df = pd.DataFrame({
            "Month":   ["Jan", "Feb", "Mar", "Apr", "May"],
            "Samples": [34, 72, 103, 64, 34],
        })

        ax = self.bar_canvas.axes
        ax.clear()

        sns.barplot(x="Samples", y="Month", data=df, ax=ax, color=_CHART_CYAN)

        ax.set_title("Monthly Rematches",
                     color=_TEXT_BODY, fontsize=10, fontweight="bold", pad=8)
        ax.tick_params(colors=_TEXT_LIGHT, labelsize=9)
        ax.set_xlabel("Total Rematch", color=_TEXT_LIGHT, fontsize=8)
        ax.set_ylabel("", color=_TEXT_LIGHT)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(axis="x", color=_TEXT_LIGHT, linestyle="--", alpha=0.15)
        self.bar_canvas.draw()

    def plot_donut_chart(self):
        labels = ["Samples", "Orders"]
        sizes  = [25, 75]
        colors = [_CHART_CYAN, _CHART_DARK]

        ax = self.donut_canvas.axes
        ax.clear()

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            pctdistance=0.75,
            textprops={"color": _TEXT_BODY, "fontsize": 10},
        )

        # Donut hole — must match the card background
        centre_circle = plt.Circle((0, 0), 0.60, fc=_CARD_BG)
        ax.add_artist(centre_circle)

        ax.axis("equal")
        self.donut_canvas.draw()

    # ── PUBLIC API ───────────────────────────────────────────────────────────

    def refresh_stats(self, pending_val, conversion_val):
        """Update sidebar KPI values dynamically."""
        self.lbl_pending_val.setText(str(pending_val))
        self.lbl_conv_val.setText(str(conversion_val))