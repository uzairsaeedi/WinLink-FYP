import sys, os, json, threading, time
from typing import Optional
from collections import deque
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QHeaderView, QSplitter, QPushButton, QComboBox, QListWidget, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPainter, QPen, QBrush, QColor, QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))

from assets.styles import STYLE_SHEET
from core.task_manager import TaskManager, TASK_TEMPLATES, TaskStatus, TaskType
from core.network import MasterNetwork, MessageType

class MasterUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("WinLink – Master PC")

        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        ROOT = os.path.abspath(os.path.join(__file__, "..", ".."))
        icon_path = os.path.join(ROOT, "assets", "WinLink_logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.task_manager = TaskManager()
        self.network = MasterNetwork()
        self.worker_resources = {}
        self.worker_resources_lock = threading.Lock()
        self.monitoring_active = True
        self.debug = False  # Set True for verbose UI debug prints
        
        # Visualization data structures
        self.task_history = deque(maxlen=50)  # Last 50 tasks
        self.task_completion_times = deque(maxlen=30)  # Last 30 completion times
        self.network_activity = deque(maxlen=100)  # Last 100 network events
        self.worker_load_history = {}  # Worker ID -> deque of load percentages
        self.task_stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0}

        self.network.register_handler(MessageType.PROGRESS_UPDATE, self.handle_progress_update)
        self.network.register_handler(MessageType.TASK_RESULT, self.handle_task_result)
        self.network.register_handler(MessageType.RESOURCE_DATA, self.handle_resource_data)
        self.network.register_handler(MessageType.READY, self.handle_worker_ready)
        self.network.register_handler(MessageType.ERROR, self.handle_worker_error)
        self.network.start()

        self.setup_ui()
        self.start_monitoring_thread()
        
        # Start timers AFTER UI is fully set up
        # Use QTimer.singleShot to delay the first update
        self.viz_timer = QTimer()
        self.viz_timer.timeout.connect(self.update_visualizations)
        QTimer.singleShot(2000, self.viz_timer.start)  # Start after 2 second delay
        self.viz_timer.setInterval(3000)  # Then update every 3 seconds for better performance

        self.discovery_timer = QTimer()
        self.discovery_timer.timeout.connect(self.refresh_discovered_workers)
        QTimer.singleShot(1000, self.discovery_timer.start)  # Start after 1 second delay
        self.discovery_timer.setInterval(3000)  # Then refresh every 3 seconds

    def setup_ui(self):
        """Setup modern, clean, and responsive UI"""
        # Add global scroll bar styling and modern effects
        self.setStyleSheet("""
            /* Modern Scrollbars */
            QScrollBar:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(20, 25, 35, 0.8),
                    stop:1 rgba(30, 35, 45, 0.8));
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 160, 0.6),
                    stop:1 rgba(102, 126, 234, 0.6));
                border-radius: 7px;
                min-height: 30px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 160, 0.8),
                    stop:1 rgba(102, 126, 234, 0.8));
            }
            QScrollBar:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 25, 35, 0.8),
                    stop:1 rgba(30, 35, 45, 0.8));
                height: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 160, 0.6),
                    stop:1 rgba(102, 126, 234, 0.6));
                border-radius: 7px;
                min-width: 30px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 160, 0.8),
                    stop:1 rgba(102, 126, 234, 0.8));
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
            
            /* Modern GroupBox */
            QGroupBox {
                font-size: 11pt;
                font-weight: bold;
                color: white;
                background: rgba(102, 126, 234, 0.1);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                background: rgba(102, 126, 234, 0.2);
                border-radius: 4px;
            }
        """)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main content area
        content_widget = QtWidgets.QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Header
        header = self._create_header()
        content_layout.addWidget(header)

        # Create tab widget for better organization
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid rgba(102, 126, 234, 0.4);
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 30, 42, 0.6),
                    stop:1 rgba(20, 25, 37, 0.6));
                padding: 15px;
                margin-top: 2px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 45, 60, 0.8),
                    stop:1 rgba(30, 35, 50, 0.8));
                color: rgba(255, 255, 255, 0.7);
                padding: 12px 32px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 2px solid rgba(102, 126, 234, 0.2);
                border-bottom: none;
                font-size: 10.5pt;
                font-weight: 600;
                min-width: 200px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.7),
                    stop:1 rgba(88, 153, 234, 0.7));
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.6);
                border-bottom: 3px solid #667eea;
                padding-bottom: 14px;
                margin-top: 0px;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 70, 90, 0.9),
                    stop:1 rgba(50, 60, 80, 0.9));
                color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.4);
            }
        """)

        # Tab 1: Dashboard (NEW)
        dashboard_tab = self.create_dashboard_tab()

        # Tab 2: Workers & Tasks
        main_tab = QtWidgets.QWidget()
        main_tab_layout = QtWidgets.QHBoxLayout(main_tab)
        main_tab_layout.setSpacing(15)
        main_tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left: Worker Management (35%) with scroll area
        worker_scroll = QtWidgets.QScrollArea()
        worker_scroll.setWidgetResizable(True)
        worker_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        worker_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        worker_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        worker_panel = self.create_worker_panel()
        worker_panel.setMinimumWidth(380)
        worker_panel.setMaximumWidth(500)
        worker_scroll.setWidget(worker_panel)
        main_tab_layout.addWidget(worker_scroll, 1)
        
        # Right: Task Management (65%) with scroll area
        task_scroll = QtWidgets.QScrollArea()
        task_scroll.setWidgetResizable(True)
        task_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        task_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        task_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        task_panel = self.create_task_panel()
        task_panel.setMinimumWidth(550)
        task_scroll.setWidget(task_panel)
        main_tab_layout.addWidget(task_scroll, 3)

        # Tab 1: Dashboard
        dashboard_tab = self.create_dashboard_tab()

        # Tab 2: Analytics
        analytics_tab = self.create_analytics_tab()

        # Add tabs
        tab_widget.addTab(dashboard_tab, "📊 Dashboard")
        tab_widget.addTab(main_tab, "🖥️ Workers and Tasks")
        tab_widget.addTab(analytics_tab, "📈 Analytics")
        
        # Set default tab to Workers and Tasks
        tab_widget.setCurrentIndex(1)

        content_layout.addWidget(tab_widget, 1)
        main_layout.addWidget(content_widget, 1)
        
        # Set responsive window size with better defaults
        self.setMinimumSize(1024, 700)
        self.resize(1400, 900)
        
        # Center window on screen
        screen_geometry = QtWidgets.QApplication.desktop().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def _create_header(self):
        """Create clean header bar"""
        header = QtWidgets.QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.4),
                    stop:0.5 rgba(75, 180, 200, 0.35),
                    stop:1 rgba(0, 245, 160, 0.4));
                border: 2px solid rgba(0, 245, 160, 0.3);
                border-radius: 12px;
            }
        """)
        header.setMinimumHeight(65)
        header.setMaximumHeight(80)
        header.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        layout.setAlignment(QtCore.Qt.AlignVCenter)  # Center all items vertically
        
        # Left side - Title
        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QtWidgets.QLabel("🎯 WinLink Master Control")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15pt;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        subtitle = QtWidgets.QLabel("Distributed Computing Management System")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 9pt;
                background: transparent;
                font-weight: 500;
                border: none;
            }
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Center - Quick stats (centered horizontally)
        stats_layout = QtWidgets.QHBoxLayout()
        stats_layout.setSpacing(10)
        
        self.header_workers_label = QtWidgets.QLabel("🖥️ 0")
        self.header_workers_label.setToolTip("Connected Workers")
        self.header_workers_label.setAlignment(QtCore.Qt.AlignCenter)
        self.header_workers_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10pt;
                font-weight: 600;
                background: rgba(0, 245, 160, 0.25);
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid rgba(0, 245, 160, 0.4);
                min-width: 60px;
            }
        """)
        
        self.header_tasks_label = QtWidgets.QLabel("📋 0")
        self.header_tasks_label.setToolTip("Total Tasks")
        self.header_tasks_label.setAlignment(QtCore.Qt.AlignCenter)
        self.header_tasks_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10pt;
                font-weight: 600;
                background: rgba(102, 126, 234, 0.3);
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid rgba(102, 126, 234, 0.5);
                min-width: 60px;
            }
        """)
        
        stats_layout.addWidget(self.header_workers_label)
        stats_layout.addWidget(self.header_tasks_label)
        layout.addLayout(stats_layout)
        
        layout.addStretch()
        
        # Right side - Status
        self.status_indicator = QtWidgets.QLabel("● Ready")
        self.status_indicator.setAlignment(QtCore.Qt.AlignCenter)
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #00f5a0;
                font-size: 10pt;
                font-weight: bold;
                background: rgba(0, 245, 160, 0.15);
                padding: 6px 12px;
                border-radius: 6px;
                border: none;
            }
        """)
        layout.addWidget(self.status_indicator)
        
        return header

    def _create_title_bar(self):
        """Create modern custom title bar with controls"""
        self.title_bar = QtWidgets.QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(50)
        
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 10, 0)
        title_layout.setSpacing(10)

        app_info_layout = QtWidgets.QHBoxLayout()
        app_info_layout.setSpacing(12)

        app_icon = QtWidgets.QLabel("🎯")
        app_icon.setObjectName("appIcon")
        app_icon.setFont(QtGui.QFont("Segoe UI Emoji", 16))
        app_info_layout.addWidget(app_icon)

        title_label = QtWidgets.QLabel("WinLink - Master PC (Enhanced)")
        title_label.setObjectName("titleLabel")
        title_font = QtGui.QFont("Segoe UI", 11, QtGui.QFont.DemiBold)
        title_label.setFont(title_font)
        app_info_layout.addWidget(title_label)
        
        title_layout.addLayout(app_info_layout)
        title_layout.addStretch()

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(0)

        self.minimize_btn = QPushButton("-")
        self.minimize_btn.setFixedSize(45, 35)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #777777;
                border-radius: 4px;
                padding: 5px;
                margin-right: 5px;
            }
            QPushButton:hover { 
                background: #666666;
                border: 1px solid #888888;
            }
        """)
        controls_layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(45, 35)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setToolTip("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #c0392b;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background: #c0392b;
                border: 1px solid #a93226;
            }
        """)
        controls_layout.addWidget(self.close_btn)
        
        title_layout.addLayout(controls_layout)

    def create_worker_panel(self):
        panel = QtWidgets.QFrame()
        panel.setProperty("glass", True)
        lay = QtWidgets.QVBoxLayout(panel)
        lay.setSpacing(12)
        lay.setContentsMargins(10, 15, 10, 10)

        hdr = QtWidgets.QLabel("🖥️ Worker Management", panel)
        hdr.setObjectName("headerLabel")
        hdr.setAlignment(QtCore.Qt.AlignCenter)
        hf = hdr.font()
        hf.setPointSize(13)
        hf.setBold(True)
        hdr.setFont(hf)
        hdr.setMargin(6)
        lay.addWidget(hdr)

        grp = QtWidgets.QGroupBox("Add Worker", panel)
        g_l = QtWidgets.QVBoxLayout(grp)
        g_l.setSpacing(12)
        g_l.setContentsMargins(15, 25, 15, 15)

        disco_label = QtWidgets.QLabel("🔍 Select Workers:")
        disco_label.setStyleSheet("font-size: 9pt; font-weight: 600; color: #00f5a0; margin-bottom: 3px;")
        g_l.addWidget(disco_label)

        help_text = QtWidgets.QLabel("Click dropdown to select multiple workers • Auto-refreshes every 2s")
        help_text.setStyleSheet("font-size: 8pt; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px;")
        g_l.addWidget(help_text)

        self.discovered_combo = QComboBox()
        self.discovered_combo.setMinimumHeight(36)

        combo_model = QtGui.QStandardItemModel()
        self.discovered_combo.setModel(combo_model)

        list_view = QtWidgets.QListView()
        list_view.setStyleSheet("""
            QListView::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            QListView::item:hover {
                background: rgba(0, 245, 160, 0.15);
            }
        """)
        self.discovered_combo.setView(list_view)

        # Ensure clicking items toggles checkbox state and persists selection
        try:
            list_view.clicked.connect(self._on_discovered_item_clicked)
        except Exception:
            pass

        combo_model.dataChanged.connect(self._on_combo_selection_changed)
        
        self.discovered_combo.setStyleSheet("""
            QComboBox {
                background: rgba(15, 20, 30, 0.95);
                color: #e6e6fa;
                border: 2px solid rgba(0, 245, 160, 0.25);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
            }
            QComboBox:hover {
                border: 2px solid rgba(0, 245, 160, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00f5a0;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: rgba(20, 25, 35, 0.98);
                color: #e6e6fa;
                selection-background-color: rgba(0, 245, 160, 0.25);
                border: 2px solid rgba(0, 245, 160, 0.4);
                border-radius: 6px;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 10px;
                border-radius: 4px;
                margin: 1px 2px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(0, 245, 160, 0.15);
            }
        """)
        
        g_l.addWidget(self.discovered_combo)

        connect_btns_layout = QtWidgets.QHBoxLayout()
        connect_btns_layout.setSpacing(6)
        
        self.connect_discovered_btn = QtWidgets.QPushButton("Connect Selected")
        self.connect_discovered_btn.setObjectName("startBtn")
        self.connect_discovered_btn.setMinimumHeight(36)
        self.connect_discovered_btn.setEnabled(False)
        self.connect_discovered_btn.clicked.connect(self.connect_from_list)
        self.connect_discovered_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 245, 160, 0.7);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(0, 245, 160, 0.85);
            }
            QPushButton:pressed {
                background: rgba(0, 245, 160, 0.6);
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.3);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        self.connect_all_btn = QtWidgets.QPushButton("Connect All")
        self.connect_all_btn.setMinimumHeight(36)
        self.connect_all_btn.setEnabled(False)
        self.connect_all_btn.clicked.connect(self.connect_all_discovered)
        self.connect_all_btn.setStyleSheet("""
            QPushButton {
                background: rgba(102, 126, 234, 0.7);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.85);
            }
            QPushButton:pressed {
                background: rgba(102, 126, 234, 0.6);
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.3);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        connect_btns_layout.addWidget(self.connect_discovered_btn, 1)
        connect_btns_layout.addWidget(self.connect_all_btn, 1)
        g_l.addLayout(connect_btns_layout)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background: rgba(255, 255, 255, 0.15); margin: 12px 0px 10px 0px; max-height: 1px;")
        g_l.addWidget(sep)

        manual_label = QtWidgets.QLabel("✏️ Manual Entry:")
        manual_label.setStyleSheet("font-size: 9pt; font-weight: 600; color: #667eea; margin-bottom: 5px;")
        g_l.addWidget(manual_label)

        manual_input_layout = QtWidgets.QHBoxLayout()
        manual_input_layout.setSpacing(6)
        
        self.ip_input = QtWidgets.QLineEdit()
        self.ip_input.setPlaceholderText("IP Address")
        self.ip_input.setMinimumHeight(34)
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background: rgba(25, 30, 40, 0.9);
                color: #e6e6fa;
                border: 2px solid rgba(102, 126, 234, 0.25);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid rgba(102, 126, 234, 0.5);
                background: rgba(25, 30, 40, 1);
            }
            QLineEdit:hover {
                border: 2px solid rgba(102, 126, 234, 0.35);
            }
        """)
        
        self.port_input = QtWidgets.QLineEdit()
        self.port_input.setPlaceholderText("Port")
        self.port_input.setValidator(QtGui.QIntValidator(1, 65535))
        self.port_input.setMinimumHeight(34)
        self.port_input.setFixedWidth(90)
        self.port_input.setStyleSheet(self.ip_input.styleSheet())
        
        manual_input_layout.addWidget(self.ip_input, 2)
        manual_input_layout.addWidget(self.port_input, 0)
        g_l.addLayout(manual_input_layout)
        
        self.connect_btn = QtWidgets.QPushButton("🔌 Connect")
        self.connect_btn.setObjectName("startBtn")
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.clicked.connect(self.connect_to_worker)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.8),
                    stop:1 rgba(88, 153, 234, 0.8));
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 8pt;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120, 140, 250, 0.9),
                    stop:1 rgba(100, 165, 250, 0.9));
                border: 2px solid rgba(120, 140, 250, 0.7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(85, 105, 200, 0.7),
                    stop:1 rgba(70, 130, 200, 0.7));
            }
        """)
        
        g_l.addWidget(self.connect_btn)
        lay.addWidget(grp)

        wgrp = QtWidgets.QGroupBox("Connected Workers", panel)
        w_l = QtWidgets.QVBoxLayout(wgrp)
        w_l.setSpacing(12)
        w_l.setContentsMargins(15, 25, 15, 15)
        self.workers_list = QtWidgets.QListWidget()
        self.workers_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.workers_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.workers_list.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        self.disconnect_btn = QtWidgets.QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("stopBtn")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setMinimumHeight(36)
        self.disconnect_btn.clicked.connect(self.disconnect_selected_worker)
        
        self.refresh_workers_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_workers_btn.setMinimumHeight(36)
        self.refresh_workers_btn.clicked.connect(self.refresh_workers)
        
        w_l.addWidget(self.workers_list)
        btn_h = QtWidgets.QHBoxLayout()
        btn_h.setSpacing(8)
        btn_h.addWidget(self.disconnect_btn)
        btn_h.addWidget(self.refresh_workers_btn)
        w_l.addLayout(btn_h)
        lay.addWidget(wgrp)

        rgrp = QtWidgets.QGroupBox("Live Worker Resources", panel)
        r_l = QtWidgets.QVBoxLayout(rgrp)
        r_l.setSpacing(10)
        r_l.setContentsMargins(15, 25, 15, 15)
        self.resource_display = QtWidgets.QTextEdit()
        self.resource_display.setReadOnly(True)
        self.resource_display.setMinimumHeight(150)

        font = self.resource_display.font()
        font.setPointSize(9)  # Comfortable font size
        font.setFamily("Consolas")  # Monospace font for alignment
        self.resource_display.setFont(font)

        self.resource_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 40, 0.8);
                color: #f0f0f0;
                border: 1px solid rgba(100, 255, 160, 0.5);
                border-radius: 8px;
                padding: 10px;
                font-size: 9pt;
            }
        """)
        self.resource_display.setPlainText("⏳ Waiting for worker resources...\n\nConnect a worker and resources will appear here.")
        r_l.addWidget(self.resource_display)

        refresh_res_btn = QtWidgets.QPushButton("🔄 Refresh Resources")
        refresh_res_btn.clicked.connect(self.refresh_all_worker_resources)
        r_l.addWidget(refresh_res_btn)
        lay.addWidget(rgrp)

        self.workers_list.itemSelectionChanged.connect(self.on_worker_selection_changed)
        return panel

    def create_task_panel(self):
        """Create simplified, clean task management panel"""
        panel = QtWidgets.QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: rgba(20, 25, 35, 0.5);
                border-radius: 8px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Task Creation Section
        create_section = QtWidgets.QGroupBox("Create New Task")
        
        create_layout = QtWidgets.QVBoxLayout(create_section)
        create_layout.setSpacing(10)

        # Task type and template in horizontal layout
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.setSpacing(10)
        
        type_col = QtWidgets.QVBoxLayout()
        type_col.addWidget(QtWidgets.QLabel("Task Type:"))
        self.task_type_combo = QtWidgets.QComboBox()
        self.task_type_combo.addItems([t.name for t in TaskType])
        self.task_type_combo.setMinimumHeight(36)
        self.task_type_combo.currentTextChanged.connect(self.on_task_type_changed)
        type_col.addWidget(self.task_type_combo)
        
        template_col = QtWidgets.QVBoxLayout()
        template_col.addWidget(QtWidgets.QLabel("Template:"))
        self.template_combo = QtWidgets.QComboBox()
        self.template_combo.setMinimumHeight(36)
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_col.addWidget(self.template_combo)
        
        type_layout.addLayout(type_col, 1)
        type_layout.addLayout(template_col, 1)
        create_layout.addLayout(type_layout)

        # Description
        self.task_description = QtWidgets.QLabel()
        self.task_description.setWordWrap(True)
        self.task_description.setStyleSheet("""
            QLabel {
                color: #c1d5e0;
                background-color: rgba(50, 50, 70, 0.5);
                border-radius: 6px;
                padding: 10px;
                font-size: 9pt;
            }
        """)
        create_layout.addWidget(self.task_description)

        # Code and Data editors (increased height and font for readability)
        self.task_code_edit = QtWidgets.QTextEdit()
        self.task_code_edit.setMaximumHeight(260)
        self.task_code_edit.setPlaceholderText("Task code will appear here...")
        self.task_code_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 40, 0.9);
                color: #f0f0f0;
                border: 2px solid rgba(100, 255, 160, 0.3);
                border-radius: 6px;
                padding: 10px;
                font-size: 11pt;
                font-family: 'Consolas';
            }
        """)
        code_font = self.task_code_edit.font()
        code_font.setPointSize(11)
        code_font.setFamily('Consolas')
        self.task_code_edit.setFont(code_font)
        create_layout.addWidget(QtWidgets.QLabel("Code:"))
        create_layout.addWidget(self.task_code_edit)

        self.task_data_edit = QtWidgets.QTextEdit()
        self.task_data_edit.setMaximumHeight(180)
        self.task_data_edit.setPlaceholderText("Task data (JSON)...")
        self.task_data_edit.setStyleSheet(self.task_code_edit.styleSheet())
        data_font = self.task_data_edit.font()
        data_font.setPointSize(11)
        data_font.setFamily('Consolas')
        self.task_data_edit.setFont(data_font)
        create_layout.addWidget(QtWidgets.QLabel("Data:"))
        create_layout.addWidget(self.task_data_edit)

        # Submit button
        self.submit_task_btn = QtWidgets.QPushButton("🚀 Submit Task")
        self.submit_task_btn.setMinimumHeight(20)
        self.submit_task_btn.setMaximumWidth(300)
        self.submit_task_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 1),
                    stop:1 rgba(88, 153, 234, 1));
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.8);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 10pt;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120, 145, 255, 1),
                    stop:1 rgba(100, 170, 250, 1));
                border: 2px solid rgba(120, 145, 255, 0.9);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(85, 105, 200, 1),
                    stop:1 rgba(70, 130, 200, 1));
                border: 2px solid rgba(85, 105, 200, 0.9);
                padding: 13px 24px 11px 24px;
            }
        """)
        self.submit_task_btn.clicked.connect(self.submit_task)
        
        # Center the button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_task_btn)
        button_layout.addStretch()
        create_layout.addLayout(button_layout)

        layout.addWidget(create_section)
        
        # Initialize templates
        self.on_task_type_changed()

        # Task Queue Section
        queue_section = QtWidgets.QGroupBox("📋 Task Queue")
        queue_layout = QtWidgets.QVBoxLayout(queue_section)
        queue_layout.setSpacing(10)

        # Task table (includes Output column)
        self.tasks_table = QtWidgets.QTableWidget(0, 7)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Type", "Status", "Worker", "Progress", "Result", "Output"])
        self.tasks_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tasks_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setMinimumHeight(420)
        self.tasks_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # Smooth scrolling and word wrap for better UX
        try:
            self.tasks_table.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.tasks_table.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        except Exception:
            pass
        self.tasks_table.setWordWrap(True)
        
        # Set column widths
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # Make worker column tighter and result column resize to contents
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        self.tasks_table.setStyleSheet("""
            QTableWidget {
                background: rgba(15, 20, 30, 0.95);
                color: #e6e6fa;
                border: 2px solid rgba(100, 255, 160, 0.25);
                border-radius: 6px;
                gridline-color: rgba(255, 255, 255, 0.08);
                font-size: 10.5pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: rgba(0, 245, 160, 0.3);
            }
            QHeaderView::section {
                background: rgba(30, 35, 45, 0.95);
                color: #00f5a0;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        queue_layout.addWidget(self.tasks_table)

        # Action buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)

        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_task_table_async)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.8),
                    stop:1 rgba(88, 153, 234, 0.8));
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120, 145, 255, 0.9),
                    stop:1 rgba(100, 165, 250, 0.9));
                border: 2px solid rgba(120, 145, 255, 0.7);
            }
        """)

        clear_btn = QtWidgets.QPushButton("🗑️ Clear Completed")
        clear_btn.setMinimumHeight(40)
        clear_btn.clicked.connect(self.clear_completed_tasks)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 100, 100, 0.8),
                    stop:1 rgba(255, 130, 130, 0.8));
                color: white;
                border: 2px solid rgba(255, 100, 100, 0.5);
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 120, 120, 0.9),
                    stop:1 rgba(255, 150, 150, 0.9));
                border: 2px solid rgba(255, 120, 120, 0.7);
            }
        """)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        queue_layout.addLayout(btn_layout)

        # Show full task details on double-click
        try:
            self.tasks_table.cellDoubleClicked.connect(self._on_task_cell_double_clicked)
        except Exception:
            pass

        layout.addWidget(queue_section, 1)

        return panel
    
    def create_dashboard_tab(self):
        """Create overview dashboard with real-time graphs and quick actions"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        plt.style.use('dark_background')
        
        tab = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top row: Quick stats cards
        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(15)
        
        # Card 1: Active Workers
        workers_card = self.create_stat_card("👥 Active Workers", "0", "🟢 Online")
        self.dashboard_workers_label = workers_card.findChild(QtWidgets.QLabel, "value")
        self.dashboard_workers_status = workers_card.findChild(QtWidgets.QLabel, "status")
        
        # Card 2: Total Tasks
        tasks_card = self.create_stat_card("📋 Total Tasks", "0", "✓ Completed")
        self.dashboard_tasks_label = tasks_card.findChild(QtWidgets.QLabel, "value")
        
        # Card 3: Success Rate
        success_card = self.create_stat_card("✅ Success Rate", "0%", "Last Hour")
        self.dashboard_success_label = success_card.findChild(QtWidgets.QLabel, "value")
        
        # Card 4: Avg Response Time
        time_card = self.create_stat_card("⚡ Avg Response", "0ms", "Network Latency")
        self.dashboard_latency_label = time_card.findChild(QtWidgets.QLabel, "value")
        
        stats_row.addWidget(workers_card)
        stats_row.addWidget(tasks_card)
        stats_row.addWidget(success_card)
        stats_row.addWidget(time_card)
        
        main_layout.addLayout(stats_row)
        
        # Middle row: Real-time graphs
        graphs_row = QtWidgets.QHBoxLayout()
        graphs_row.setSpacing(15)
        
        # Graph 1: Worker Resource Usage
        resource_graph_widget = QtWidgets.QGroupBox("📊 Worker Resource Usage")
        resource_graph_widget.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 10pt;
                font-weight: bold;
                border: 2px solid rgba(102, 126, 234, 0.4);
                border-radius: 8px;
                padding: 15px;
                background: rgba(25, 30, 42, 0.5);
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        resource_layout = QtWidgets.QVBoxLayout(resource_graph_widget)
        
        self.resource_figure = Figure(figsize=(6, 4), facecolor='#1a1e2a')
        self.resource_canvas = FigureCanvas(self.resource_figure)
        self.resource_ax = self.resource_figure.add_subplot(111)
        resource_layout.addWidget(self.resource_canvas)
        
        # Graph 2: Task Distribution
        task_graph_widget = QtWidgets.QGroupBox("📈 Task Distribution")
        task_graph_widget.setStyleSheet(resource_graph_widget.styleSheet())
        task_layout = QtWidgets.QVBoxLayout(task_graph_widget)
        
        self.task_figure = Figure(figsize=(6, 4), facecolor='#1a1e2a')
        self.task_canvas = FigureCanvas(self.task_figure)
        self.task_ax = self.task_figure.add_subplot(111)
        task_layout.addWidget(self.task_canvas)
        
        graphs_row.addWidget(resource_graph_widget)
        graphs_row.addWidget(task_graph_widget)
        
        main_layout.addLayout(graphs_row)
        
        # Bottom row: Quick Actions
        actions_group = QtWidgets.QGroupBox("⚡ Quick Actions")
        actions_group.setStyleSheet(resource_graph_widget.styleSheet())
        actions_layout = QtWidgets.QHBoxLayout(actions_group)
        actions_layout.setSpacing(10)
        
        quick_ping_btn = QtWidgets.QPushButton("🔍 Discover Workers")
        quick_ping_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 160, 0.7),
                    stop:1 rgba(102, 126, 234, 0.7));
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 160, 0.9),
                    stop:1 rgba(102, 126, 234, 0.9));
            }
        """)
        quick_ping_btn.clicked.connect(self.refresh_discovered_workers)
        
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh Resources")
        refresh_btn.setStyleSheet(quick_ping_btn.styleSheet())
        refresh_btn.clicked.connect(self.refresh_task_table_async)
        
        clear_tasks_btn = QtWidgets.QPushButton("🗑️ Clear Completed Tasks")
        clear_tasks_btn.setStyleSheet(quick_ping_btn.styleSheet())
        clear_tasks_btn.clicked.connect(lambda: self.clear_completed_tasks())
        
        export_btn = QtWidgets.QPushButton("📥 Export Report")
        export_btn.setStyleSheet(quick_ping_btn.styleSheet())
        export_btn.clicked.connect(lambda: self.export_dashboard_report())
        
        actions_layout.addWidget(quick_ping_btn)
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(clear_tasks_btn)
        actions_layout.addWidget(export_btn)
        
        main_layout.addWidget(actions_group)
        
        # Start dashboard update timer
        self.dashboard_timer = QtCore.QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(2000)  # Update every 2 seconds
        
        return tab
    
    def create_stat_card(self, title, value, subtitle):
        """Create a stat card for the dashboard"""
        card = QtWidgets.QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(102, 126, 234, 0.3),
                    stop:1 rgba(88, 153, 234, 0.2));
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(8)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 9pt;
            font-weight: 600;
        """)
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet("""
            color: white;
            font-size: 24pt;
            font-weight: bold;
        """)
        
        status_label = QtWidgets.QLabel(subtitle)
        status_label.setObjectName("status")
        status_label.setStyleSheet("""
            color: rgba(0, 245, 160, 0.9);
            font-size: 8pt;
            font-weight: 500;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(status_label)
        
        return card
    
    def update_dashboard(self):
        """Update dashboard metrics and graphs"""
        try:
            # Update stat cards
            connected_count = len(self.network.get_connected_workers())
            self.dashboard_workers_label.setText(str(connected_count))
            
            total_tasks = len(self.task_manager.tasks)
            self.dashboard_tasks_label.setText(str(total_tasks))
            
            # Calculate success rate
            completed_tasks = [t for t in self.task_manager.tasks.values() 
                             if t.status.value == 'completed']
            failed_tasks = [t for t in self.task_manager.tasks.values() 
                          if t.status.value == 'failed']
            
            if completed_tasks or failed_tasks:
                success_rate = (len(completed_tasks) / (len(completed_tasks) + len(failed_tasks))) * 100
                self.dashboard_success_label.setText(f"{success_rate:.1f}%")
            
            # Calculate average latency
            latencies = list(self.network.worker_latencies.values())
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                self.dashboard_latency_label.setText(f"{avg_latency:.0f}ms")
            
            # Update resource usage graph
            self.update_resource_graph()
            
            # Update task distribution graph
            self.update_task_distribution_graph()
            
        except Exception as e:
            print(f"Dashboard update error: {e}")
    
    def update_resource_graph(self):
        """Update the worker resource usage graph"""
        try:
            self.resource_ax.clear()
            
            workers = self.network.get_connected_workers()
            if not workers:
                self.resource_ax.text(0.5, 0.5, 'No workers connected', 
                                     ha='center', va='center', color='gray', fontsize=12)
                self.resource_canvas.draw()
                return
            
            worker_names = []
            cpu_usage = []
            mem_usage = []
            
            for worker_id, info in workers.items():
                resources = info.get('resources', {})
                worker_names.append(worker_id[:8])  # Show first 8 chars
                cpu_usage.append(resources.get('cpu_percent', 0))
                mem_usage.append(resources.get('memory_percent', 0))
            
            x = range(len(worker_names))
            width = 0.35
            
            bars1 = self.resource_ax.bar([i - width/2 for i in x], cpu_usage, width, 
                                        label='CPU %', color='#667eea', alpha=0.8)
            bars2 = self.resource_ax.bar([i + width/2 for i in x], mem_usage, width,
                                        label='Memory %', color='#00f5a0', alpha=0.8)
            
            self.resource_ax.set_xlabel('Worker', color='white')
            self.resource_ax.set_ylabel('Usage (%)', color='white')
            self.resource_ax.set_title('Real-time Resource Usage', color='white', fontsize=11, weight='bold')
            self.resource_ax.set_xticks(x)
            self.resource_ax.set_xticklabels(worker_names, rotation=45, ha='right')
            self.resource_ax.legend()
            self.resource_ax.set_ylim(0, 100)
            self.resource_ax.tick_params(colors='white')
            self.resource_ax.spines['bottom'].set_color('gray')
            self.resource_ax.spines['left'].set_color('gray')
            self.resource_ax.spines['top'].set_visible(False)
            self.resource_ax.spines['right'].set_visible(False)
            
            try:
                self.resource_figure.tight_layout()
            except Exception:
                pass
            self.resource_canvas.draw()
            
        except Exception as e:
            print(f"Resource graph error: {e}")
    
    def update_task_distribution_graph(self):
        """Update the task distribution pie chart"""
        try:
            self.task_ax.clear()
            
            # Count tasks by status
            status_counts = {}
            for task in self.task_manager.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if not status_counts:
                self.task_ax.text(0.5, 0.5, 'No tasks yet', 
                                ha='center', va='center', color='gray', fontsize=12)
                self.task_canvas.draw()
                return
            
            labels = []
            sizes = []
            colors_map = {
                'pending': '#f39c12',
                'running': '#667eea',
                'completed': '#00f5a0',
                'failed': '#e74c3c'
            }
            colors = []
            
            for status, count in status_counts.items():
                labels.append(f'{status.title()} ({count})')
                sizes.append(count)
                colors.append(colors_map.get(status, '#95a5a6'))
            
            wedges, texts, autotexts = self.task_ax.pie(sizes, labels=labels, colors=colors,
                                                        autopct='%1.1f%%', startangle=90)
            
            for text in texts:
                text.set_color('white')
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
            
            self.task_ax.set_title('Task Status Distribution', color='white', fontsize=11, weight='bold')
            
            self.task_figure.tight_layout()
            self.task_canvas.draw()
            
        except Exception as e:
            print(f"Task distribution graph error: {e}")
    
    def clear_completed_tasks(self):
        """Clear all completed tasks from the queue"""
        try:
            tasks_to_remove = [tid for tid, task in self.task_manager.tasks.items() 
                             if task.status.value == 'completed']
            
            for task_id in tasks_to_remove:
                del self.task_manager.tasks[task_id]
            
            self.update_task_queue()
            QtWidgets.QMessageBox.information(self, "Success", f"Cleared {len(tasks_to_remove)} completed tasks")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error clearing tasks: {e}")
    
    def export_dashboard_report(self):
        """Export dashboard statistics to a file"""
        try:
            import datetime
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"winlink_report_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("WinLink Dashboard Report\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"Active Workers: {len(self.network.get_connected_workers())}\n")
                f.write(f"Total Tasks: {len(self.task_manager.tasks)}\n\n")
                
                f.write("Worker Details:\n")
                for worker_id, info in self.network.get_connected_workers().items():
                    f.write(f"\n  {worker_id}:\n")
                    resources = info.get('resources', {})
                    f.write(f"    CPU: {resources.get('cpu_percent', 0):.1f}%\n")
                    f.write(f"    Memory: {resources.get('memory_percent', 0):.1f}%\n")
                    f.write(f"    GPU: {resources.get('gpu_info', 'N/A')}\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            QtWidgets.QMessageBox.information(self, "Success", f"Report exported to {filename}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error exporting report: {e}")
    
    def create_analytics_tab(self):
        """Create analytics and visualization tab"""
        tab = QtWidgets.QWidget()
        
        # Add scroll area for analytics content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        scroll_content = QtWidgets.QWidget()
        scroll_content.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        layout = QtWidgets.QVBoxLayout(scroll_content)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Metrics Dashboard Section Header
        metrics_header = QtWidgets.QLabel("📊 Performance Metrics")
        metrics_header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                background: rgba(0, 245, 160, 0.15);
                padding: 8px 14px;
                border-radius: 6px;
                border-left: 3px solid #00f5a0;
            }
        """)
        layout.addWidget(metrics_header)
        
        # Metrics Dashboard
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(18)
        
        self.metrics_cards = {}
        metrics_data = [
            ("total_tasks", "📋 Total Tasks", "0", "#667eea"),
            ("active_workers", "🖥️ Active Workers", "0", "#00f5a0"),
            ("completed_rate", "✅ Completion Rate", "0%", "#4CAF50"),
            ("avg_time", "⏱️ Avg Task Time", "0s", "#ff9800")
        ]
        
        for idx, (key, label, default, color) in enumerate(metrics_data):
            card = self._create_metric_card(label, default, color)
            self.metrics_cards[key] = card
            row, col = divmod(idx, 2)  # 2x2 grid instead of 1x4
            metrics_layout.addWidget(card, row, col)
        
        # Set column stretch for equal width
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        
        layout.addLayout(metrics_layout)
        
        # Add spacing
        layout.addSpacing(15)
        
        # Charts Section Header
        charts_header = QtWidgets.QLabel("📈 Data Visualizations")
        charts_header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                background: rgba(102, 126, 234, 0.15);
                padding: 8px 14px;
                border-radius: 6px;
                border-left: 3px solid #667eea;
            }
        """)
        layout.addWidget(charts_header)
        
        # Charts Grid
        charts_layout = QGridLayout()
        charts_layout.setSpacing(18)
        
        # Task Distribution Pie Chart
        self.task_pie_canvas = self._create_pie_chart()
        self.task_pie_canvas.setMinimumSize(400, 320)
        self.task_pie_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        charts_layout.addWidget(self.task_pie_canvas, 0, 0)
        
        # Task Completion Timeline
        self.timeline_canvas = self._create_timeline_chart()
        self.timeline_canvas.setMinimumSize(400, 320)
        self.timeline_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        charts_layout.addWidget(self.timeline_canvas, 0, 1)
        
        # Worker Load Chart
        self.worker_load_canvas = self._create_worker_load_chart()
        self.worker_load_canvas.setMinimumSize(800, 280)
        self.worker_load_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        charts_layout.addWidget(self.worker_load_canvas, 1, 0, 1, 2)
        
        # Set stretch factors for responsive behavior
        charts_layout.setColumnStretch(0, 1)
        charts_layout.setColumnStretch(1, 1)
        charts_layout.setRowStretch(0, 1)
        charts_layout.setRowStretch(1, 1)
        
        layout.addLayout(charts_layout, 1)
        
        scroll_area.setWidget(scroll_content)
        tab_layout = QtWidgets.QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        
        return tab

    def start_monitoring_thread(self):
        def monitor():
            while self.monitoring_active:
                workers = self.network.get_connected_workers()
                if workers:
                    for worker_id in workers.keys():
                        self.network.request_resources_from_worker(worker_id)
                time.sleep(10)
        threading.Thread(target=monitor, daemon=True).start()

    def on_worker_selection_changed(self):
        self.disconnect_btn.setEnabled(bool(self.workers_list.selectedItems()))
    
    def refresh_discovered_workers(self):
        """Update the dropdown with newly discovered workers"""
        discovered = self.network.get_discovered_workers()

        # Preserve checked selections by worker_id
        checked_ids = set()
        for i in range(self.discovered_combo.count()):
            item = self.discovered_combo.model().item(i)
            if item and item.checkState() == QtCore.Qt.Checked:
                worker_info_json = item.data(Qt.UserRole)
                if worker_info_json:
                    try:
                        info = json.loads(worker_info_json)
                        wid = f"{info.get('ip')}:{info.get('port')}"
                        checked_ids.add(wid)
                    except (json.JSONDecodeError, TypeError):
                        pass

        model = self.discovered_combo.model()
        model.clear()
        
        if not discovered:
            item = QtGui.QStandardItem("🔍 Searching for workers...")
            item.setEnabled(False)
            model.appendRow(item)
            self.discovered_combo.setEnabled(False)
            self.connect_discovered_btn.setEnabled(False)
            self.connect_all_btn.setEnabled(False)
            return
        
        self.discovered_combo.setEnabled(True)
        selected_count = 0
        has_unconnected = False

        for worker_id, info in discovered.items():
            hostname = info.get('hostname', 'Unknown')
            ip = info.get('ip', '')
            port = info.get('port', '')

            connected = worker_id in self.network.get_connected_workers()
            
            if connected:
                display_text = f"✅ {hostname} ({ip}:{port})"
            else:
                display_text = f"🖥️ {hostname} ({ip}:{port})"
                has_unconnected = True

            item = QtGui.QStandardItem(display_text)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckable(True)

            # Store struct as JSON for later retrieval
            item.setData(json.dumps(info), Qt.UserRole)
            wid = f"{ip}:{port}"
            if wid in checked_ids:
                item.setCheckState(QtCore.Qt.Checked)
                selected_count += 1
            else:
                item.setCheckState(QtCore.Qt.Unchecked)

            if connected:
                item.setEnabled(False)
            
            model.appendRow(item)

        self._update_combo_text()

        self._update_connect_button_states()
        self.connect_all_btn.setEnabled(has_unconnected)
    
    def _on_combo_selection_changed(self):
        """Handle when checkbox states change in the combo box"""
        if self.debug:
            print("[MASTER] _on_combo_selection_changed called")

        self._update_combo_text()

        self._update_connect_button_states()

    def _on_task_cell_double_clicked(self, row, col):
        """Open a dialog showing full task result/output when a row is double-clicked."""
        try:
            id_item = self.tasks_table.item(row, 0)
            if not id_item:
                return
            task_id_short = id_item.text()
            # Find full task id from task_manager by matching prefix
            full_task = None
            for t in self.task_manager.get_all_tasks():
                if t.id.startswith(task_id_short):
                    full_task = t
                    break
            if not full_task:
                QtWidgets.QMessageBox.information(self, "Task Not Found", "Could not find task details")
                return

            details = []
            details.append(f"ID: {full_task.id}")
            details.append(f"Type: {full_task.type.name}")
            details.append(f"Status: {full_task.status.name}")
            details.append(f"Worker: {full_task.worker_id or 'N/A'}")
            details.append("\n--- Result / Output ---\n")
            if getattr(full_task, 'output', None):
                details.append(full_task.output)
            elif full_task.result is not None:
                try:
                    details.append(json.dumps(full_task.result, indent=2))
                except Exception:
                    details.append(str(full_task.result))
            elif full_task.error:
                details.append(f"ERROR:\n{full_task.error}")
            else:
                details.append("No output available yet")

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Task Details")
            dialog.resize(1000, 700)
            layout = QtWidgets.QVBoxLayout(dialog)

            # Styled read-only text area with monospace font and wrapping
            text = QtWidgets.QTextEdit()
            text.setReadOnly(True)
            text.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
            text.setPlainText("\n".join(details))
            font = text.font()
            font.setFamily("Consolas")
            font.setPointSize(12)
            font.setWeight(QtGui.QFont.Normal)
            font.setPointSize(14)
            text.setFont(font)
            text.setStyleSheet("QTextEdit { background: #0f1620; color: #e6e6fa; padding: 8px; border-radius: 6px; }")
            layout.addWidget(text)

            # Buttons: Copy and Close
            btn_row = QtWidgets.QHBoxLayout()
            btn_row.addStretch()
            copy_btn = QtWidgets.QPushButton("Copy Output")
            def _copy():
                try:
                    QtWidgets.QApplication.clipboard().setText(text.toPlainText())
                except Exception:
                    pass
            copy_btn.clicked.connect(_copy)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            for b in (copy_btn, close_btn):
                b.setMinimumWidth(110)
                b.setMinimumHeight(36)
            btn_row.addWidget(copy_btn)
            btn_row.addWidget(close_btn)
            layout.addLayout(btn_row)
            dialog.exec_()
        except Exception as e:
            if self.debug:
                print(f"[MASTER] Error opening task details: {e}")

    def _on_discovered_item_clicked(self, index):
        """Toggle the checkbox state when an item in the discovered dropdown is clicked."""
        try:
            model = self.discovered_combo.model()
            item = model.itemFromIndex(index)
            if not item or not item.isEnabled():
                return
            # Toggle check state
            new_state = QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked
            item.setCheckState(new_state)
            # Trigger update handlers
            self._on_combo_selection_changed()
            # Keep popup open briefly to avoid losing selection when cursor leaves
            QtCore.QTimer.singleShot(60, lambda: self.discovered_combo.showPopup() if self.discovered_combo.view().isVisible() else None)
        except Exception:
            pass
    
    def _update_connect_button_states(self):
        """Update the enabled state of connect buttons based on checked items"""
        checked_count = 0
        for i in range(self.discovered_combo.count()):
            item = self.discovered_combo.model().item(i)
            if item and item.checkState() == QtCore.Qt.Checked and item.isEnabled():
                checked_count += 1
        
        if self.debug:
            print(f"[MASTER] _update_connect_button_states: {checked_count} items checked")

        self.connect_discovered_btn.setEnabled(checked_count > 0)
        if self.debug:
            print(f"[MASTER] Connect button enabled: {checked_count > 0}")
    
    def _update_combo_text(self):
        """Update combo box display text based on selections"""
        checked_count = 0
        for i in range(self.discovered_combo.count()):
            item = self.discovered_combo.model().item(i)
            if item and item.checkState() == QtCore.Qt.Checked:
                checked_count += 1
        
        if checked_count == 0:
            self.discovered_combo.setCurrentIndex(0)
        elif checked_count == 1:

            for i in range(self.discovered_combo.count()):
                item = self.discovered_combo.model().item(i)
                if item and item.checkState() == QtCore.Qt.Checked:
                    self.discovered_combo.setCurrentIndex(i)
                    break
        else:

            self.discovered_combo.setCurrentText(f"✅ {checked_count} workers selected")
    
    def connect_from_list(self):
        """Connect to selected workers from discovered dropdown"""
        selected_workers = []
        model = self.discovered_combo.model()
        
        for i in range(self.discovered_combo.count()):
            item = model.item(i)
            if item:
                is_checked = item.checkState() == QtCore.Qt.Checked
                is_enabled = item.isEnabled()
                if self.debug:
                    print(f"[MASTER] Item {i}: checked={is_checked}, enabled={is_enabled}, text={item.text()}")
                
                if is_checked:
                    worker_info_json = item.data(Qt.UserRole)
                    if worker_info_json:
                        try:
                            worker_info = json.loads(worker_info_json)
                            selected_workers.append(worker_info)
                            if self.debug:
                                print(f"[MASTER] Added worker: {worker_info.get('hostname', 'Unknown')}")
                        except (json.JSONDecodeError, TypeError) as e:
                            if self.debug:
                                print(f"[MASTER] Error parsing worker info: {e}")
        
        if self.debug:
            print(f"[MASTER] Total selected workers: {len(selected_workers)}")
        
        if not selected_workers:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please check at least one worker from the dropdown")
            return
        
        success_count = 0
        fail_count = 0
        already_connected = 0
        
        for worker_info in selected_workers:
            ip = worker_info.get('ip')
            port = worker_info.get('port')
            hostname = worker_info.get('hostname', 'Unknown')
            worker_id = f"{ip}:{port}"

            if worker_id in self.network.get_connected_workers():
                already_connected += 1
                continue
            
            connected = self.network.connect_to_worker(worker_id, ip, int(port))
            if connected:
                success_count += 1

                QtCore.QTimer.singleShot(300, lambda wid=worker_id: self.network.request_resources_from_worker(wid))
            else:
                fail_count += 1

        msg_parts = []
        if success_count > 0:
            msg_parts.append(f"✅ Connected: {success_count}")
        if already_connected > 0:
            msg_parts.append(f"ℹ️ Already connected: {already_connected}")
        if fail_count > 0:
            msg_parts.append(f"❌ Failed: {fail_count}")
        
        if msg_parts:
            QtWidgets.QMessageBox.information(self, "Connection Results", "\n".join(msg_parts))
        
        self.refresh_workers_async()
        self.refresh_discovered_workers()
    
    def connect_all_discovered(self):
        """Connect to all discovered workers"""
        discovered = self.network.get_discovered_workers()
        
        if not discovered:
            QtWidgets.QMessageBox.warning(self, "No Workers", "No workers discovered yet")
            return
        
        success_count = 0
        fail_count = 0
        already_connected = 0
        
        for worker_id, info in discovered.items():

            if worker_id in self.network.get_connected_workers():
                already_connected += 1
                continue
            
            ip = info.get('ip')
            port = info.get('port')
            
            connected = self.network.connect_to_worker(worker_id, ip, int(port))
            if connected:
                success_count += 1

                QtCore.QTimer.singleShot(300, lambda wid=worker_id: self.network.request_resources_from_worker(wid))
            else:
                fail_count += 1

        msg_parts = []
        if success_count > 0:
            msg_parts.append(f"✅ Connected: {success_count}")
        if already_connected > 0:
            msg_parts.append(f"ℹ️ Already connected: {already_connected}")
        if fail_count > 0:
            msg_parts.append(f"❌ Failed: {fail_count}")
        
        if msg_parts:
            QtWidgets.QMessageBox.information(self, "Bulk Connection Results", "\n".join(msg_parts))
        
        self.refresh_workers_async()
        self.refresh_discovered_workers()

    def connect_to_worker(self):
        """Connect to worker using manual IP and port entry"""
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        if not ip or not port:
            QtWidgets.QMessageBox.warning(self, "Missing Info", "Enter both IP and Port")
            return
        worker_id = f"{ip}:{port}"

        if worker_id in self.network.get_connected_workers():
            QtWidgets.QMessageBox.information(self, "Already Connected", 
                f"Already connected to {worker_id}")
            return

        self.resource_display.setPlainText(f"🔄 Connecting to {worker_id}...\n\nRetrying up to 3 times if needed...")
        QtWidgets.QApplication.processEvents()
        
        connected = self.network.connect_to_worker(worker_id, ip, int(port))
        if not connected:
            error_msg = (
                f"Failed to connect to {worker_id} after 3 attempts\n\n"
                "Common fixes:\n"
                "1. Ensure Worker app is running and 'Start Worker' is clicked\n"
                "2. Check Worker's console shows: '✅ Server started successfully'\n"
                "3. Verify both PCs are on the same network\n"
                "4. Try waiting 10 more seconds and retry\n\n"
                "Check console output for detailed error messages."
            )
            QtWidgets.QMessageBox.critical(self, "Connection Failed", error_msg)
            self.resource_display.setPlainText("❌ Connection failed. See error message.")
        else:
            QtWidgets.QMessageBox.information(self, "Connected", f"✅ Connected to {worker_id}")

            self.resource_display.setPlainText(f"✅ Connected to {worker_id}\n\n⏳ Waiting for resource data...")
            QtCore.QTimer.singleShot(300, lambda: self.network.request_resources_from_worker(worker_id))
            QtCore.QTimer.singleShot(1000, lambda: self.network.request_resources_from_worker(worker_id))
            QtCore.QTimer.singleShot(2000, lambda: self.network.request_resources_from_worker(worker_id))
        self.refresh_workers_async()

    def refresh_workers(self):
        # Save currently selected worker
        current_selection = None
        current_item = self.workers_list.currentItem()
        if current_item:
            current_selection = current_item.text()
        
        self.workers_list.clear()

        workers = self.network.get_connected_workers()
        selected_row = -1
        for idx, (worker_id, info) in enumerate(workers.items()):
            entry = f"{info['ip']}:{info['port']}"
            list_item = QtWidgets.QListWidgetItem(entry)
            # Store worker_id for robust lookup later
            list_item.setData(Qt.UserRole, worker_id)
            # Ensure item is selectable and enabled
            try:
                list_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            except Exception:
                pass
            self.workers_list.addItem(list_item)

            # Check if this was the previously selected worker
            if current_selection and entry == current_selection:
                selected_row = idx
        
        # Restore selection if worker still exists
        if selected_row >= 0:
            self.workers_list.setCurrentRow(selected_row)
        # Ensure disconnect button state matches selection
        self.on_worker_selection_changed()

    def disconnect_selected_worker(self):
        sel = self.workers_list.currentItem()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a worker to disconnect")
            return

        # Prefer stored worker_id from the list item's data for robust lookup
        worker_id = sel.data(Qt.UserRole)
        ip_port = sel.text()

        # Fallback: try resolving by matching display text if UserRole not present
        if not worker_id:
            for wid, info in self.network.get_connected_workers().items():
                if f"{info['ip']}:{info['port']}" == ip_port:
                    worker_id = wid
                    break

        if self.debug:
            print(f"[MASTER] Attempting disconnect: sel_text={ip_port}, resolved_worker_id={worker_id}")
        
        if not worker_id:
            QtWidgets.QMessageBox.warning(self, "Worker Not Found", 
                f"Could not find worker {ip_port}")
            return

        reply = QtWidgets.QMessageBox.question(
            self, 
            "Confirm Disconnect",
            f"Disconnect from worker {ip_port}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                # Perform network disconnect
                self.network.disconnect_worker(worker_id)
                print(f"[MASTER] 🔌 Disconnected from worker: {ip_port} (worker_id={worker_id})")

                # Clear cached resources
                with self.worker_resources_lock:
                    self.worker_resources.pop(worker_id, None)

                # Requeue any tasks that were assigned to this worker
                try:
                    self.task_manager.requeue_tasks_for_worker(worker_id)
                except Exception:
                    pass

                # Refresh UI promptly
                QtCore.QTimer.singleShot(100, self.refresh_workers)
                self.refresh_workers_async()
                self.refresh_discovered_workers()
                self.update_resource_display()
                self.refresh_task_table_async()

                QtWidgets.QMessageBox.information(self, "Disconnected", f"Successfully disconnected from {ip_port}")
                self.disconnect_btn.setEnabled(False)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to disconnect: {str(e)}")
                print(f"[MASTER] ❌ Error disconnecting: {e}")

    def on_task_type_changed(self):
        """Update template dropdown based on selected task type"""
        selected_type_name = self.task_type_combo.currentText()
        try:
            selected_type = TaskType[selected_type_name]
        except KeyError:
            return

        self.template_combo.clear()
        for template_key, template_data in TASK_TEMPLATES.items():
            if template_data.get("type") == selected_type:
                self.template_combo.addItem(template_key)

        if self.template_combo.count() == 0:
            self.template_combo.addItem("Custom")

        if self.template_combo.count() > 0:
            self.on_template_changed(self.template_combo.currentText())
    
    def on_template_changed(self, name):
        if not name or name == "Custom":
            self.task_description.setText("Enter custom task code")
            self.task_code_edit.clear()
            self.task_data_edit.setPlainText("{}")
            return
            
        desc = TASK_TEMPLATES.get(name, {}).get("description", "")
        code = TASK_TEMPLATES.get(name, {}).get("code", "")
        sample_data = TASK_TEMPLATES.get(name, {}).get("sample_data")
        self.task_description.setText(desc)
        self.task_code_edit.setPlainText(code)
        if sample_data is not None:
            self.task_data_edit.setPlainText(json.dumps(sample_data, indent=2))
        else:
            self.task_data_edit.setPlainText("{}")

    def submit_task(self):
        code = self.task_code_edit.toPlainText()
        if not code.strip():
            QtWidgets.QMessageBox.warning(self, "Missing Code", "Task code cannot be empty.")
            return
        
        try:
            data = json.loads(self.task_data_edit.toPlainText() or "{}")
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.critical(self, "Invalid JSON", "Task data must be valid JSON.")
            return

        try:
            selected_type = TaskType[self.task_type_combo.currentText()]
        except KeyError:
            QtWidgets.QMessageBox.critical(self, "Invalid Task Type", "Selected task type is not valid.")
            return

        connected_workers = self.network.get_connected_workers()
        if not connected_workers:
            QtWidgets.QMessageBox.warning(self, "No Workers", "Connect at least one worker before submitting tasks.")
            return

        task_id = self.task_manager.create_task(selected_type, code, data)
        print(f"[MASTER] 📤 Task submitted: {task_id[:8]}... Type: {selected_type.name}")
        print(f"[MASTER] 🔄 Available workers: {len(connected_workers)}")
        print(f"[MASTER] ⚠️  MASTER WILL NOT EXECUTE - Only dispatching to worker")
        
        assigned_worker = self.dispatch_task_to_worker(task_id, code, data)
        if not assigned_worker:
            QtWidgets.QMessageBox.critical(self, "Dispatch Failed", "Failed to dispatch task to any worker.")
            print(f"[MASTER] ❌ Task {task_id[:8]}... dispatch failed - no available workers")
        else:
            worker_short = assigned_worker[:20] + "..." if len(assigned_worker) > 20 else assigned_worker
            print(f"[MASTER] ✅ Task {task_id[:8]}... dispatched to worker {worker_short}")
            print(f"[MASTER] ⏳ Waiting for worker '{worker_short}' to execute and return results...")
        self.refresh_task_table_async()
    
    def send_video_to_worker(self):
        """Send video streaming request to selected worker"""
        video_url = self.video_url_input.text().strip()
        if not video_url:
            QtWidgets.QMessageBox.warning(self, "Missing URL", "Please enter a video URL.")
            return
        
        # Validate URL format
        if not (video_url.startswith('http://') or video_url.startswith('https://')):
            QtWidgets.QMessageBox.warning(self, "Invalid URL", 
                "Video URL must start with http:// or https://")
            return
        
        # Get selected worker
        selected_index = self.video_worker_combo.currentIndex()
        if selected_index < 0:
            QtWidgets.QMessageBox.warning(self, "No Worker", 
                "No worker selected. Please connect a worker first.")
            return
        
        worker_id = self.video_worker_combo.itemData(selected_index)
        worker_name = self.video_worker_combo.currentText()
        
        # Get video title
        video_title = self.video_title_input.text().strip() or "Video Stream"
        
        # Create video playback task
        try:
            task_id = self.task_manager.create_task(
                TaskType.VIDEO_PLAYBACK,
                TASK_TEMPLATES["video_playback"]["code"],
                {
                    "video_url": video_url,
                    "title": video_title
                }
            )
            
            print(f"[MASTER] 🎬 Video streaming task created: {task_id[:8]}...")
            print(f"[MASTER] 📺 URL: {video_url}")
            print(f"[MASTER] 🎯 Target worker: {worker_name}")
            
            # Send task to specific worker
            payload = {
                'task_id': task_id,
                'code': TASK_TEMPLATES["video_playback"]["code"],
                'data': {
                    "video_url": video_url,
                    "title": video_title
                },
                'name': 'VIDEO_PLAYBACK'
            }
            
            sent = self.network.send_task_to_worker(worker_id, payload)
            if sent:
                self.task_manager.assign_task_to_worker(task_id, worker_id)
                print(f"[MASTER] ✅ Video task sent successfully to {worker_name}")
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Video Sent",
                    f"Video streaming request sent to worker:\n{worker_name}\n\n"
                    f"The video player will open on the worker PC shortly."
                )
                
                # Clear inputs
                self.video_url_input.clear()
                self.video_title_input.clear()
                
                # Refresh task table
                self.refresh_task_table_async()
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Send Failed",
                    f"Failed to send video request to worker {worker_name}"
                )
                print(f"[MASTER] ❌ Failed to send video task to {worker_name}")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Error creating video task: {str(e)}"
            )
            print(f"[MASTER] ❌ Error creating video task: {e}")

    def dispatch_task_to_worker(self, task_id: str, code: str, data: dict) -> Optional[str]:
        """Dispatch task to best available worker using intelligent selection. Returns worker_id if successful, None otherwise."""
        workers = self.network.get_connected_workers()
        if not workers:
            return None

        # Get task type for capability matching
        task = self.task_manager.get_task(task_id)
        task_type = task.type.name.lower() if task else None
        
        # Use intelligent worker selection
        target_worker = self.network.select_best_worker(task_type=task_type, strategy="intelligent")
        if not target_worker:
            return None

        task_name = task.type.name if task else "Unknown Task"
        
        payload = {
            'task_id': task_id,
            'code': code,
            'data': data,
            'name': task_name
        }
        
        sent = self.network.send_task_to_worker(target_worker, payload)
        if sent:
            self.task_manager.assign_task_to_worker(task_id, target_worker)
            self.network.increment_task_count(target_worker)
            return target_worker
        return None

    def _select_worker(self, workers: dict) -> str:
        """Intelligently select the best worker based on available resources and load"""
        resources = self._get_worker_resources_snapshot()
        
        if not resources:

            return list(workers.keys())[0] if workers else None
        
        best_worker = None
        best_score = -1
        
        print(f"[MASTER] 🎯 Load Balancing - Evaluating {len(workers)} workers")
        
        for worker_id in workers.keys():
            stats = resources.get(worker_id, {})

            cpu_available = 100 - stats.get('cpu_percent', 100)  # Available CPU %
            mem_available = stats.get('memory_available_mb', 0) or 0  # Available memory MB
            disk_free = stats.get('disk_free_gb', 0) or 0  # Free disk GB

            active_tasks = 0
            for task_id, task in self.task_manager.tasks.items():
                if task.worker_id == worker_id and task.status.value in ['pending', 'running']:
                    active_tasks += 1

            cpu_score = cpu_available * 0.3
            mem_score = min(mem_available / 1024, 100) * 0.4  # Normalize to 0-100 scale
            task_score = max(0, 100 - (active_tasks * 20)) * 0.2  # Penalty for each task
            disk_score = min(disk_free * 10, 100) * 0.1  # Normalize to 0-100 scale
            
            total_score = cpu_score + mem_score + task_score + disk_score
            
            print(f"[MASTER]   Worker {worker_id[:15]}... Score: {total_score:.1f} "
                  f"(CPU: {cpu_available:.0f}%, Mem: {mem_available:.0f}MB, "
                  f"Tasks: {active_tasks}, Disk: {disk_free:.1f}GB)")
            
            if total_score > best_score:
                best_score = total_score
                best_worker = worker_id
        
        if best_worker:
            print(f"[MASTER] ✅ Selected worker: {best_worker[:15]}... (score: {best_score:.1f})")
        else:

            best_worker = list(workers.keys())[0] if workers else None
            print(f"[MASTER] ⚠️ Using fallback worker selection: {best_worker[:15] if best_worker else 'None'}...")
        
        return best_worker

    def refresh_task_table(self):
        tasks = sorted(self.task_manager.get_all_tasks(), key=lambda t: t.created_at, reverse=True)
        self.tasks_table.setRowCount(len(tasks))
        for row, t in enumerate(tasks):

            id_item = QtWidgets.QTableWidgetItem(t.id[:8])
            self.tasks_table.setItem(row, 0, id_item)

            type_item = QtWidgets.QTableWidgetItem(t.type.name)
            self.tasks_table.setItem(row, 1, type_item)

            status_item = QtWidgets.QTableWidgetItem(t.status.name)
            self.tasks_table.setItem(row, 2, status_item)

            worker_text = ""
            if t.worker_id:
                worker_text = t.worker_id.split(":")[0] if ":" in t.worker_id else t.worker_id
            worker_item = QtWidgets.QTableWidgetItem(worker_text)
            self.tasks_table.setItem(row, 3, worker_item)

            progress_widget = QtWidgets.QProgressBar()
            try:
                prog_val = int(getattr(t, 'progress', 0) or 0)
            except Exception:
                prog_val = 0
            progress_widget.setRange(0, 100)
            progress_widget.setValue(max(0, min(100, prog_val)))
            # Show percentage text inside the progress bar (was hidden previously)
            progress_widget.setTextVisible(True)
            progress_widget.setToolTip(f"{progress_widget.value()}%")
            # Use Qt's %p placeholder so the displayed text updates correctly
            try:
                progress_widget.setFormat("%p%")
            except Exception:
                progress_widget.setFormat(f"{progress_widget.value()}%")
            # Keep progress bar visually compact
            try:
                progress_widget.setFixedHeight(18)
            except Exception:
                pass
            progress_widget.setAlignment(QtCore.Qt.AlignCenter)
            self.tasks_table.setCellWidget(row, 4, progress_widget)

            # Create a concise but informative result preview (up to 300 chars)
            result_text = ""
            if t.result is not None:
                try:
                    if isinstance(t.result, (dict, list, tuple)):
                        full = json.dumps(t.result, indent=2)
                    else:
                        full = str(t.result)
                except Exception:
                    full = str(t.result)

                # Show full result text in the table (large results may still be visible via tooltip)
                # Limit extremely long strings to avoid UI freeze, but keep a generous cap
                preview_limit = 5000
                if len(full) > preview_limit:
                    result_text = full[:preview_limit].rstrip() + "..."
                else:
                    result_text = full
            elif t.error:
                result_text = f"Error: {t.error[:80]}"
            else:
                result_text = "Pending..."
            result_item = QtWidgets.QTableWidgetItem(result_text)
            result_item.setToolTip(result_text)  # Show full text on hover
            result_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            result_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.tasks_table.setItem(row, 5, result_item)

            output_text = ""
            if hasattr(t, 'output') and t.output:
                output_text = str(t.output)
            elif t.error:
                output_text = f"ERROR:\n{t.error}"
            elif t.result is not None:

                if isinstance(t.result, dict):
                    output_lines = []
                    for key, val in t.result.items():
                        if isinstance(val, (dict, list)):
                            output_lines.append(f"{key}: {json.dumps(val, indent=2)}")
                        else:
                            output_lines.append(f"{key}: {val}")
                    output_text = "\n".join(output_lines)
                elif isinstance(t.result, (list, tuple)):
                    output_text = json.dumps(list(t.result) if isinstance(t.result, tuple) else t.result, indent=2)
                else:
                    output_text = str(t.result)
            else:
                output_text = "No output yet"
            
            output_item = QtWidgets.QTableWidgetItem(output_text)
            output_item.setToolTip(output_text)  # Show full text on hover
            output_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            output_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            # Allow full text to be copied from item
            output_item.setData(QtCore.Qt.UserRole, output_text)
            self.tasks_table.setItem(row, 6, output_item)

            status_item = self.tasks_table.item(row, 2)
            if status_item:
                st = status_item.text().upper()
                try:
                    if st.startswith('COMPLETED') or 'SUCCESS' in st:
                        color = QtGui.QColor(200, 255, 200)
                    elif st.startswith('RUNNING') or st.startswith('IN_PROGRESS'):
                        color = QtGui.QColor(255, 250, 200)
                    elif st.startswith('FAILED') or 'ERROR' in st or st.startswith('CANCEL'):
                        color = QtGui.QColor(255, 200, 200)
                    else:
                        color = QtGui.QColor(230, 230, 250)
                    status_item.setBackground(QtGui.QBrush(color))
                except Exception:
                    pass

            # Calculate reasonable row height based on output lines but keep compact
            lines = output_text.count('\n') + 1
            estimated = max(36, min(220, lines * 16))
            self.tasks_table.setRowHeight(row, estimated)

    def refresh_task_table_async(self):
        QtCore.QTimer.singleShot(0, self.refresh_task_table)

    def handle_progress_update(self, worker_id, data):
        task_id = data.get("task_id")
        progress = data.get("progress", 0)

        if progress in [0, 25, 50, 75, 100]:
            print(f"[MASTER] ⏳ Task {task_id[:8] if task_id else 'unknown'}... progress: {progress}%")
        self.task_manager.update_task_progress(task_id, progress)
        self.refresh_task_table_async()

    def handle_task_result(self, worker_id, data):
        task_id = data.get("task_id")
        result_payload = data.get("result", {})
        
        # Decrement task count for worker
        self.network.decrement_task_count(worker_id)
        
        worker_short = worker_id[:20] + "..." if len(worker_id) > 20 else worker_id
        print(f"[MASTER] 📥 Received result from worker {worker_short}")
        print(f"[MASTER] 📊 VERIFICATION: Task {task_id[:8] if task_id else 'unknown'}... was executed on worker, NOT on master")

        if result_payload.get("success"):
            print(f"[MASTER] ✅ Task {task_id[:8] if task_id else 'unknown'}... completed successfully")
        else:
            error = result_payload.get("error", "Unknown error")
            print(f"[MASTER] ❌ Task {task_id[:8] if task_id else 'unknown'}... failed: {error[:50]}")

        task = self.task_manager.get_task(task_id)
        if task:
            output_parts = []
            if result_payload.get("stdout"):
                output_parts.append(f"STDOUT:\n{result_payload['stdout']}")
            if result_payload.get("stderr"):
                output_parts.append(f"STDERR:\n{result_payload['stderr']}")
            if result_payload.get("result") is not None:
                output_parts.append(f"RESULT:\n{json.dumps(result_payload['result'], indent=2) if isinstance(result_payload['result'], dict) else str(result_payload['result'])}")
            
            task.output = "\n\n".join(output_parts) if output_parts else None
        
        self.task_manager.update_task(task_id, worker_id, result_payload)
        self.refresh_task_table_async()

    def handle_resource_data(self, worker_id, data):
        """Handle incoming resource data from workers"""
        with self.worker_resources_lock:
            self.worker_resources[worker_id] = data.copy()
        
        # Update network's resource tracking
        self.network.update_worker_resources(worker_id, data)

        QtCore.QTimer.singleShot(0, self.update_resource_display)
    
    def update_resource_display(self):
        """Update the resource display with current worker data"""

        snapshot = self._get_worker_resources_snapshot()

        if not snapshot:
            connected_workers = self.network.get_connected_workers()
            if not connected_workers:
                self.resource_display.setPlainText(
                    "⏳ Waiting for worker resources...\n\nConnect a worker and resources will appear here."
                )
            else:
                self.resource_display.setPlainText(
                    f"✅ Connected to {len(connected_workers)} worker(s)\n\n⏳ Loading resource data..."
                )
            return

        output = []
        output.append(f"📊 LIVE WORKER RESOURCES - {len(snapshot)} Connected")
        output.append(f"🕐 Updated: {time.strftime('%H:%M:%S')}")
        output.append("=" * 50)
        output.append("")
        
        for wid, stats in snapshot.items():

            worker_ip = wid.split(":")[0] if ":" in wid else wid

            cpu = stats.get("cpu_percent", 0.0)
            mem_percent = stats.get("memory_percent", 0.0)
            mem_total_mb = stats.get("memory_total_mb", 0.0)
            mem_avail_mb = stats.get("memory_available_mb", 0.0)
            mem_used_mb = mem_total_mb - mem_avail_mb if mem_total_mb > 0 else 0
            disk_percent = stats.get("disk_percent", 0.0)
            disk_free_gb = stats.get("disk_free_gb", 0.0)
            battery = stats.get("battery_percent")
            plugged = stats.get("battery_plugged")

            def status(val):
                return "🟢" if val < 50 else "🟡" if val < 75 else "🔴"
            
            output.append(f"🖥️  WORKER: {worker_ip}")
            output.append("-" * 50)

            output.append(f"{status(cpu)} CPU Usage:          {cpu:5.1f}%")

            mem_total_gb = mem_total_mb / 1024
            mem_used_gb = mem_used_mb / 1024
            mem_avail_gb = mem_avail_mb / 1024
            output.append(f"{status(mem_percent)} Memory Usage:       {mem_percent:5.1f}%")
            output.append(f"   • Total RAM:        {mem_total_gb:6.2f} GB")
            output.append(f"   • Used RAM:         {mem_used_gb:6.2f} GB")
            output.append(f"   💚 UNUTILIZED RAM:  {mem_avail_gb:6.2f} GB ⭐")

            output.append(f"{status(disk_percent)} Disk Usage:         {disk_percent:5.1f}%")
            output.append(f"   • Free Space:       {disk_free_gb:6.1f} GB")

            if battery is not None:
                icon = "🔌" if plugged else "🔋"
                status_text = "Charging" if plugged else "On Battery"
                output.append(f"{icon} Battery:            {battery:5.0f}% ({status_text})")
            else:
                output.append("⚡ Power:              AC (No Battery)")
            
            output.append("")
        
        final_text = "\n".join(output)

        self.resource_display.setPlainText(final_text)

    def handle_worker_ready(self, worker_id, data):
        self.network.request_resources_from_worker(worker_id)
        self.refresh_workers_async()

    def handle_worker_error(self, worker_id, data):
        task_id = data.get("task_id")
        error = data.get("error", "Unknown error")
        if task_id:
            self.task_manager.update_task(task_id, worker_id, {
                "success": False,
                "result": None,
                "error": error
            })
            self.refresh_task_table_async()
        QtCore.QTimer.singleShot(
            0,
            lambda: QtWidgets.QMessageBox.critical(
                self,
                "Worker Error",
                f"Worker {worker_id} reported an error:\n{error}"
            )
        )

    def clear_completed_tasks(self):
        self.task_manager.clear_tasks(status=TaskStatus.COMPLETED)
        self.refresh_task_table()

    def refresh_workers_async(self):
        QtCore.QTimer.singleShot(0, self.refresh_workers)

    def refresh_all_worker_resources(self):
        """Manually request resources from all connected workers"""
        workers = self.network.get_connected_workers()
        if not workers:
            self.resource_display.setPlainText("⚠️  No workers connected.\n\nPlease connect a worker first.")
            return

        for worker_id in workers.keys():
            self.network.request_resources_from_worker(worker_id)

    def _get_worker_resources_snapshot(self):
        with self.worker_resources_lock:
            print(f"[DEBUG] 📸 Creating snapshot from {len(self.worker_resources)} stored workers")
            print(f"[DEBUG] 📸 Worker IDs in resources: {list(self.worker_resources.keys())}")
            snapshot = {wid: data.copy() for wid, data in self.worker_resources.items()}
            for wid, data in snapshot.items():
                print(f"[DEBUG]    ✓ Worker {wid}: {len(data)} data fields - CPU: {data.get('cpu_percent', 'N/A')}")
            return snapshot
    
    def _create_metric_card(self, title, value, color):
        """Create a metric card widget"""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 35, 45, 0.95),
                    stop:1 rgba(25, 30, 40, 0.95));
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(90)
        card.setMaximumHeight(120)
        card.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 10, 12, 10)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 9pt;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22pt;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        value_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        return card
    
    def _create_pie_chart(self):
        """Create task distribution pie chart"""
        fig = Figure(figsize=(5, 4), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(260)
        canvas.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 30, 40, 0.95),
                    stop:1 rgba(20, 25, 35, 0.95));
                border: 2px solid rgba(0, 245, 160, 0.3);
                border-radius: 8px;
            }
        """)
        
        self.pie_ax = fig.add_subplot(111)
        self.pie_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def _create_timeline_chart(self):
        """Create task completion timeline chart"""
        fig = Figure(figsize=(5, 4), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(260)
        canvas.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 30, 40, 0.95),
                    stop:1 rgba(20, 25, 35, 0.95));
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
            }
        """)
        
        self.timeline_ax = fig.add_subplot(111)
        self.timeline_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def _create_worker_load_chart(self):
        """Create worker load distribution chart"""
        fig = Figure(figsize=(10, 3), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(220)
        canvas.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 30, 40, 0.95),
                    stop:1 rgba(20, 25, 35, 0.95));
                border: 2px solid rgba(255, 152, 0, 0.3);
                border-radius: 8px;
            }
        """)
        
        self.worker_load_ax = fig.add_subplot(111)
        self.worker_load_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def update_visualizations(self):
        """Update all visualizations with current data"""
        try:
            # Safety check: ensure UI is fully initialized
            if not hasattr(self, 'metrics_cards') or not self.metrics_cards:
                return
            
            # Update task statistics
            tasks = self.task_manager.get_all_tasks()
            self.task_stats = {
                "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
                "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED)
            }
            
            # Update metric cards
            total_tasks = len(tasks)
            active_workers = len(self.network.get_connected_workers())
            completion_rate = (self.task_stats["completed"] / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate average task time
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED and hasattr(t, 'completion_time')]
            avg_time = sum(getattr(t, 'completion_time', 0) for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0
            
            # Update metric card values - with safety checks
            for key in ['total_tasks', 'active_workers', 'completed_rate', 'avg_time']:
                if key not in self.metrics_cards:
                    continue
                    
                metric_label = self.metrics_cards[key].findChild(QtWidgets.QLabel, "metricValue")
                if not metric_label:
                    continue
                
                if key == "total_tasks":
                    metric_label.setText(str(total_tasks))
                elif key == "active_workers":
                    metric_label.setText(str(active_workers))
                elif key == "completed_rate":
                    metric_label.setText(f"{completion_rate:.1f}%")
                elif key == "avg_time":
                    metric_label.setText(f"{avg_time:.1f}s")
            
            # Update header stats if they exist
            if hasattr(self, 'header_workers_label'):
                self.header_workers_label.setText(f"🖥️ {active_workers}")
            if hasattr(self, 'header_tasks_label'):
                self.header_tasks_label.setText(f"📋 {total_tasks}")
            
            # Update charts if they exist
            if hasattr(self, 'pie_ax'):
                self._update_pie_chart()
            if hasattr(self, 'timeline_ax'):
                self._update_timeline_chart()
            if hasattr(self, 'worker_load_ax'):
                self._update_worker_load_chart()
            
        except Exception as e:
            print(f"[DEBUG] Error updating visualizations: {e}")
    
    def _update_pie_chart(self):
        """Update task distribution pie chart"""
        try:
            self.pie_ax.clear()
            
            sizes = [
                self.task_stats["pending"],
                self.task_stats["running"],
                self.task_stats["completed"],
                self.task_stats["failed"]
            ]
            labels = ['Pending', 'Running', 'Completed', 'Failed']
            colors = ['#ffb74d', '#667eea', '#00f5a0', '#ff5252']
            
            # Only plot if there's data
            if sum(sizes) > 0:
                wedges, texts, autotexts = self.pie_ax.pie(
                    sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                    startangle=90, textprops={'color': 'white', 'fontsize': 9}
                )
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                self.pie_ax.set_title('Task Distribution', color='white', fontsize=11, fontweight='bold', pad=10)
            else:
                self.pie_ax.text(0.5, 0.5, 'No Tasks Yet', ha='center', va='center', 
                               color='white', fontsize=12, transform=self.pie_ax.transAxes)
                self.pie_ax.set_title('Task Distribution', color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.pie_ax.axis('equal')
            self.task_pie_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating pie chart: {e}")
    
    def _update_timeline_chart(self):
        """Update task completion timeline"""
        try:
            self.timeline_ax.clear()
            
            if len(self.task_completion_times) > 0:
                times = list(range(len(self.task_completion_times)))
                values = list(self.task_completion_times)
                
                self.timeline_ax.plot(times, values, color='#00f5a0', linewidth=2, marker='o', markersize=4)
                self.timeline_ax.fill_between(times, values, alpha=0.3, color='#00f5a0')
                self.timeline_ax.set_title('Task Completion Timeline', color='white', fontsize=11, fontweight='bold', pad=10)
                self.timeline_ax.set_xlabel('Task Number', color='white', fontsize=9)
                self.timeline_ax.set_ylabel('Time (s)', color='white', fontsize=9)
                self.timeline_ax.tick_params(colors='white', labelsize=8)
                self.timeline_ax.grid(True, alpha=0.2, color='white')
                self.timeline_ax.spines['bottom'].set_color('white')
                self.timeline_ax.spines['left'].set_color('white')
                self.timeline_ax.spines['top'].set_visible(False)
                self.timeline_ax.spines['right'].set_visible(False)
            else:
                self.timeline_ax.text(0.5, 0.5, 'No Completed Tasks', ha='center', va='center',
                                     color='white', fontsize=12, transform=self.timeline_ax.transAxes)
                self.timeline_ax.set_title('Task Completion Timeline', color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.timeline_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating timeline chart: {e}")
    
    def _update_worker_load_chart(self):
        """Update worker load distribution chart"""
        try:
            self.worker_load_ax.clear()
            
            workers = self.network.get_connected_workers()
            if workers:
                worker_names = []
                cpu_loads = []
                mem_loads = []
                
                for worker_id, _ in workers.items():
                    worker_names.append(f"Worker {worker_id[:8]}")
                    
                    # Get resource data
                    with self.worker_resources_lock:
                        res = self.worker_resources.get(worker_id, {})
                        cpu_loads.append(res.get('cpu_percent', 0))
                        mem_loads.append(res.get('mem_percent', 0))
                
                x = range(len(worker_names))
                width = 0.35
                
                bars1 = self.worker_load_ax.bar([i - width/2 for i in x], cpu_loads, width, 
                                                label='CPU %', color='#667eea', alpha=0.8)
                bars2 = self.worker_load_ax.bar([i + width/2 for i in x], mem_loads, width,
                                                label='Memory %', color='#00f5a0', alpha=0.8)
                
                self.worker_load_ax.set_title('Worker Resource Usage', color='white', fontsize=11, fontweight='bold', pad=10)
                self.worker_load_ax.set_ylabel('Usage %', color='white', fontsize=9)
                self.worker_load_ax.set_xticks(x)
                self.worker_load_ax.set_xticklabels(worker_names, rotation=45, ha='right', color='white', fontsize=8)
                self.worker_load_ax.tick_params(colors='white', labelsize=8)
                self.worker_load_ax.legend(facecolor='#1a1f2e', edgecolor='white', labelcolor='white', fontsize=9)
                self.worker_load_ax.grid(True, alpha=0.2, color='white', axis='y')
                self.worker_load_ax.set_ylim(0, 100)
                self.worker_load_ax.spines['bottom'].set_color('white')
                self.worker_load_ax.spines['left'].set_color('white')
                self.worker_load_ax.spines['top'].set_visible(False)
                self.worker_load_ax.spines['right'].set_visible(False)
                
                # Add value labels on bars
                for bar in bars1:
                    height = bar.get_height()
                    self.worker_load_ax.text(bar.get_x() + bar.get_width()/2., height,
                                           f'{height:.0f}%', ha='center', va='bottom', 
                                           color='white', fontsize=7)
                for bar in bars2:
                    height = bar.get_height()
                    self.worker_load_ax.text(bar.get_x() + bar.get_width()/2., height,
                                           f'{height:.0f}%', ha='center', va='bottom',
                                           color='white', fontsize=7)
            else:
                self.worker_load_ax.text(0.5, 0.5, 'No Workers Connected', ha='center', va='center',
                                       color='white', fontsize=12, transform=self.worker_load_ax.transAxes)
                self.worker_load_ax.set_title('Worker Resource Usage', color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.worker_load_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating worker load chart: {e}")

    def _get_worker_resources_snapshot(self):
        with self.worker_resources_lock:
            print(f"[DEBUG] 📸 Creating snapshot from {len(self.worker_resources)} stored workers")
            print(f"[DEBUG] 📸 Worker IDs in resources: {list(self.worker_resources.keys())}")
            snapshot = {wid: data.copy() for wid, data in self.worker_resources.items()}
            for wid, data in snapshot.items():
                print(f"[DEBUG]    ✓ Worker {wid}: {len(data)} data fields - CPU: {data.get('cpu_percent', 'N/A')}")
            return snapshot

    def closeEvent(self, event: QtGui.QCloseEvent):
        """Handle window close event - cleanup resources"""
        try:
            self.monitoring_active = False

            if hasattr(self, 'discovery_timer'):
                self.discovery_timer.stop()

            time.sleep(0.1)
            self.network.stop()
        except Exception as ex:
            print(f"Error during cleanup: {ex}")
        finally:
            super().closeEvent(event)

if __name__ == "__main__":
    import ctypes
    app = QtWidgets.QApplication(sys.argv)
    
    # Set app ID for Windows taskbar
    try:
        myappid = 'winlink.fyp.master.2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
    
    # Set app icon
    ROOT = os.path.abspath(os.path.join(__file__, "..", ".."))
    icon_path = os.path.join(ROOT, "assets", "WinLink_logo.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Apply stylesheet
    app.setStyleSheet(STYLE_SHEET)
    
    win = MasterUI()
    win.showMaximized()
    sys.exit(app.exec_())
