

import sys, os, socket, threading, psutil, time, json
from collections import deque
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QTextEdit, QGroupBox, QCheckBox, QSpinBox,
    QFormLayout, QLineEdit, QGraphicsDropShadowEffect, QMessageBox,
    QFileDialog, QSizePolicy, QSplitter, QGridLayout, QScrollArea, QDesktopWidget, QTabWidget
)
from PyQt5.QtGui import QColor, QIntValidator, QTextCursor, QIcon, QPainter, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5 import QtWidgets, QtCore
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.task_executor import TaskExecutor
from core.network import WorkerNetwork, MessageType, NetworkMessage
from assets.styles import STYLE_SHEET
from worker.task_thread import TaskExecutionThread

# Import VideoPlayerWindow only when needed (VLC is optional)
try:
    from worker.video_player import VideoPlayerWindow
    VIDEO_PLAYER_AVAILABLE = True
except Exception as e:
    VIDEO_PLAYER_AVAILABLE = False
    print(f"[WORKER] Video player not available: {e}")

class LogSignals(QObject):
    """Signals for thread-safe logging"""
    log_message = pyqtSignal(str)

class WorkerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("WinLink – Worker PC")

        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        icon_path = os.path.join(ROOT, "assets", "WinLink_logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.network = WorkerNetwork()
        self.task_executor = TaskExecutor()
        self.current_tasks = {}
        self.tasks_lock = threading.Lock()
        self.monitoring_active = True
        self.last_output_text = "No task output yet."
        self.task_log_initialized = False  # Track if we've written first real log
        self.startup_logs_shown = False  # Track if startup logs have been shown
        
        # Track active task threads to prevent UI blocking
        self.active_task_threads = {}  # task_id -> TaskExecutionThread
        
        # Visualization data structures
        self.cpu_history = deque(maxlen=60)  # Last 60 seconds of CPU
        self.mem_history = deque(maxlen=60)  # Last 60 seconds of Memory
        self.disk_history = deque(maxlen=60)  # Last 60 seconds of Disk
        self.network_history = deque(maxlen=60)  # Last 60 seconds of Network
        self.task_count_history = deque(maxlen=60)  # Task count over time
        self.task_performance = []  # List of task completion times

        self.log_signals = LogSignals()
        self.log_signals.log_message.connect(self._append_log_to_ui)

        self.network.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)
        self.network.register_handler(MessageType.RESOURCE_REQUEST, self.handle_resource_request)
        self.network.register_handler(MessageType.HEARTBEAT, self.handle_heartbeat)
        self.network.set_connection_callback(self.handle_master_connected)

        self.setup_ui()
        self.update_ip()
        self.start_monitoring_thread()
        
        # Start visualization update timer
        self.viz_timer = QTimer()
        self.viz_timer.timeout.connect(self.update_visualization_data)
        self.viz_timer.start(1000)  # Update every second

        QTimer.singleShot(100, self.update_resources_now)

    def handle_master_connected(self, addr):
        """Handle when master connects to worker"""
        connect_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log("─" * 60)
        self.log(f"🔗 Master connected from {addr[0]}:{addr[1]}")
        self.log(f"   ⏱️  Connected at: {connect_time}")
        self.log(f"   ✓ Worker ready to receive tasks")
        self.log("─" * 60)

    def handle_resource_request(self, data):
        try:
            resource_data = self.task_executor.get_system_resources()
            self.network.send_resource_data(resource_data)
        except Exception as e:
            pass

    def handle_heartbeat(self, data):
        msg = NetworkMessage(MessageType.HEARTBEAT_RESPONSE, {
            "timestamp": time.time()
        })
        self.network.send_message_to_master(msg)

    def position_spinbox_arrows(self):
        """Position arrow labels on top of spinbox buttons"""
        # Position CPU spinbox arrows
        width = self.cpu_limit.width()
        height = self.cpu_limit.height()
        button_width = 20
        x_pos = width - button_width
        
        self.cpu_up_arrow.setGeometry(x_pos, 0, button_width, height // 2)
        self.cpu_down_arrow.setGeometry(x_pos, height // 2, button_width, height // 2)
        
        # Position Memory spinbox arrows
        width = self.mem_limit.width()
        height = self.mem_limit.height()
        x_pos = width - button_width
        
        self.mem_up_arrow.setGeometry(x_pos, 0, button_width, height // 2)
        self.mem_down_arrow.setGeometry(x_pos, height // 2, button_width, height // 2)

    def showEvent(self, event):
        """Called when window is shown"""
        super().showEvent(event)
        # Position arrows after window is shown
        QTimer.singleShot(50, self.position_spinbox_arrows)

    def setup_ui(self):
        # Modern global styling matching master UI
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
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main content area
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Modern header
        header = self._create_header()
        content_layout.addWidget(header)

        # Create tab widget matching master UI
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

        # Tab 1: Worker Configuration & Tasks
        main_tab = QWidget()
        main_tab_layout = QHBoxLayout(main_tab)
        main_tab_layout.setSpacing(15)
        main_tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left: Connection panel
        connection_panel = self.create_connection_panel()
        main_tab_layout.addWidget(connection_panel, 1)
        
        # Right: Task panel (without visualizations)
        task_panel = self.create_task_panel()
        main_tab_layout.addWidget(task_panel, 2)

        # Tab 2: Analytics & Visualizations
        analytics_tab = self.create_analytics_tab()

        # Add tabs
        tab_widget.addTab(main_tab, "⚡ Worker & Tasks")
        tab_widget.addTab(analytics_tab, "📊 Analytics")

        content_layout.addWidget(tab_widget, 1)

        main_layout.addWidget(content_widget, 1)
        
        # Set responsive window size
        self.setMinimumSize(1024, 700)
        self.resize(1400, 900)
        
        # Center window on screen
        from PyQt5.QtWidgets import QDesktopWidget
        screen_geometry = QDesktopWidget().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def _create_header(self):
        """Create modern header matching master UI"""
        header = QFrame()
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
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignVCenter)
        
        # Left - Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("⚡ WinLink Worker")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15pt;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        subtitle = QLabel("Distributed Task Execution Node")
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
        
        # Right - Status
        self.status_indicator = QLabel("● Ready")
        self.status_indicator.setAlignment(Qt.AlignCenter)
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
    
    def create_analytics_tab(self):
        """Create analytics and visualization tab matching master UI"""
        tab = QWidget()
        
        # Add scroll area for analytics content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Metrics Dashboard Section Header
        metrics_header = QLabel("📊 Performance Metrics")
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
        metrics_layout.setContentsMargins(0, 10, 0, 10)
        metrics_layout.setAlignment(Qt.AlignTop)
        
        self.metrics_cards = {}
        self.metrics_values = {}  # Store value labels for updates
        metrics_data = [
            ("tasks_completed", "📋 Tasks Done", "0", "#00f5a0"),
            ("avg_cpu", "💻 Avg CPU", "0%", "#667eea"),
            ("avg_mem", "🧠 Avg Memory", "0%", "#ff9800"),
            ("uptime", "⏱️ Uptime", "0m", "#4CAF50")
        ]
        
        for idx, (key, label, default, color) in enumerate(metrics_data):
            card, value_label = self._create_metric_card(label, default, color)
            self.metrics_cards[key] = card
            self.metrics_values[key] = value_label
            row, col = divmod(idx, 2)
            metrics_layout.addWidget(card, row, col)
        
        # Set column stretch for equal width
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        # Set row stretch
        metrics_layout.setRowStretch(0, 0)
        metrics_layout.setRowStretch(1, 0)
        
        layout.addLayout(metrics_layout)
        
        # Add spacing
        layout.addSpacing(15)
        
        # Charts Section Header
        charts_header = QLabel("📈 Data Visualizations")
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
        
        # Resource History Chart
        self.resource_history_canvas = self._create_resource_history_chart()
        self.resource_history_canvas.setMinimumSize(800, 320)
        self.resource_history_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.resource_history_canvas, 0, 0, 1, 2)
        
        # Network Activity Chart
        self.network_activity_canvas = self._create_network_activity_chart()
        self.network_activity_canvas.setMinimumSize(400, 280)
        self.network_activity_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.network_activity_canvas, 1, 0)
        
        # Task Performance Chart
        self.task_performance_canvas = self._create_task_performance_chart()
        self.task_performance_canvas.setMinimumSize(400, 280)
        self.task_performance_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.task_performance_canvas, 1, 1)
        
        # Set stretch factors for responsive behavior
        charts_layout.setColumnStretch(0, 1)
        charts_layout.setColumnStretch(1, 1)
        charts_layout.setRowStretch(0, 1)
        charts_layout.setRowStretch(1, 1)
        
        layout.addLayout(charts_layout, 1)
        
        scroll_area.setWidget(scroll_content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        
        return tab

    def _create_title_bar(self):
        """Create modern custom title bar with controls"""
        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(50)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 10, 0)
        title_layout.setSpacing(10)

        app_info_layout = QHBoxLayout()
        app_info_layout.setSpacing(12)

        app_icon = QLabel("⚡")
        app_icon.setObjectName("appIcon")
        from PyQt5.QtGui import QFont
        app_icon.setFont(QFont("Segoe UI Emoji", 16))
        app_info_layout.addWidget(app_icon)

        title_label = QLabel("WinLink - Worker PC (Enhanced)")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Segoe UI", 11, QFont.DemiBold)
        title_label.setFont(title_font)
        app_info_layout.addWidget(title_label)
        
        title_layout.addLayout(app_info_layout)
        title_layout.addStretch()

        controls_layout = QHBoxLayout()
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

    def create_connection_panel(self):
        # Scroll area wrapper for responsiveness
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        panel = QFrame()
        panel.setProperty("glass", True)
        panel.setMinimumWidth(350)
        panel.setMaximumWidth(500)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 15, 10, 10)

        # Header label
        hdr = QLabel("⚡ Worker Configuration", panel)
        hdr.setObjectName("headerLabel")
        hdr.setAlignment(Qt.AlignCenter)
        hf = hdr.font()
        hf.setPointSize(13)
        hf.setBold(True)
        hdr.setFont(hf)
        hdr.setMargin(6)
        layout.addWidget(hdr)

        conn_gb = QGroupBox("Connection Settings")
        conn_layout = QVBoxLayout(conn_gb)
        conn_layout.setContentsMargins(15, 25, 15, 15)
        conn_layout.setSpacing(10)

        self.ip_label = QLabel("IP Address: –")
        self.ip_label.setStyleSheet("font-size: 9pt; font-weight: 600; color: #00f5a0;")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port (e.g. 5001)")
        self.port_input.setValidator(QIntValidator(1, 65535))
        self.port_input.setObjectName("portInput")

        self.port_input.setFixedHeight(36)
        p_font = self.port_input.font()
        p_font.setPointSize(max(10, p_font.pointSize()))
        self.port_input.setFont(p_font)
        self.port_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                color: #e6e6fa;
                background: rgba(25, 30, 40, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.25);
                border-radius: 6px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid rgba(102, 126, 234, 0.5);
                background: rgba(25, 30, 40, 1);
            }
        """)

        conn_layout.addWidget(self.ip_label)
        conn_layout.addWidget(self.port_input)
        layout.addWidget(conn_gb)

        share_gb = QGroupBox("Share Resources")
        share_gb.setMinimumHeight(250)
        share_gb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        share_layout = QVBoxLayout(share_gb)
        share_layout.setContentsMargins(15, 25, 15, 15)
        share_layout.setSpacing(12)

        checkbox_style = """
        QCheckBox {
            color: white;
            font-size: 8pt;
            font-weight: 600;
            spacing: 8px;
            padding: 2px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(102, 126, 234, 0.6);
            border-radius: 3px;
            background: rgba(25, 30, 40, 0.9);
        }
        QCheckBox::indicator:checked {
            background: rgba(102, 126, 234, 1);
            border: 2px solid rgba(102, 126, 234, 1);
            image: url(none);
        }
        QCheckBox::indicator:checked:hover {
            background: rgba(120, 145, 255, 1);
        }
        QCheckBox::indicator:hover {
            border: 2px solid rgba(102, 126, 234, 0.9);
            background: rgba(35, 40, 50, 1);
        }
        """

        for text, default in [
            ("CPU Processing", True),
            ("Memory (RAM)", True),
            ("Storage Access", False)
        ]:
            cb = QCheckBox(text)
            cb.setChecked(default)
            cb.setStyleSheet(checkbox_style)
            cb.setMinimumHeight(24)
            cb.setMaximumHeight(28)
            share_layout.addWidget(cb)

        # Resource Limits Section with compact layout
        share_layout.addSpacing(8)
        
        # CPU Limit Row
        cpu_row = QHBoxLayout()
        cpu_row.setSpacing(10)
        
        lbl_cpu = QLabel("Max CPU:")
        lbl_cpu.setStyleSheet("color: white; font-size: 8pt; font-weight: 600;")
        lbl_cpu.setFixedWidth(80)
        
        self.cpu_limit = QSpinBox()
        self.cpu_limit.setRange(10, 100)
        self.cpu_limit.setValue(90)
        self.cpu_limit.setSuffix("%")
        self.cpu_limit.setAlignment(Qt.AlignCenter)
        self.cpu_limit.setFixedHeight(30)
        self.cpu_limit.setStyleSheet("""
            QSpinBox {
                color: white;
                background: rgba(40, 45, 60, 1);
                border: 2px solid rgba(102, 126, 234, 0.7);
                border-radius: 5px;
                font-size: 9.5pt;
                font-weight: 600;
                padding-right: 20px;
                padding-left: 8px;
            }
            QSpinBox:focus {
                border: 2px solid rgba(102, 126, 234, 1);
            }
            QSpinBox:hover {
                border: 2px solid rgba(102, 126, 234, 0.9);
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                background: rgba(102, 126, 234, 0.6);
                border-left: 1px solid rgba(80, 100, 200, 0.5);
                border-top-right-radius: 3px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
            }
            QSpinBox::up-button:hover {
                background: rgba(102, 126, 234, 0.9);
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                background: rgba(102, 126, 234, 0.6);
                border-left: 1px solid rgba(80, 100, 200, 0.5);
                border-bottom-right-radius: 3px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
            }
            QSpinBox::down-button:hover {
                background: rgba(102, 126, 234, 0.9);
            }
        """)
        
        cpu_row.addWidget(lbl_cpu)
        cpu_row.addWidget(self.cpu_limit)
        
        # Add arrow labels for CPU spinbox
        self.cpu_up_arrow = QLabel("▲", self.cpu_limit)
        self.cpu_up_arrow.setStyleSheet("color: white; background: transparent; font-size: 8pt;")
        self.cpu_up_arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.cpu_up_arrow.setAlignment(Qt.AlignCenter)
        
        self.cpu_down_arrow = QLabel("▼", self.cpu_limit)
        self.cpu_down_arrow.setStyleSheet("color: white; background: transparent; font-size: 8pt;")
        self.cpu_down_arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.cpu_down_arrow.setAlignment(Qt.AlignCenter)
        
        share_layout.addLayout(cpu_row)
        
        # Memory Limit Row
        mem_row = QHBoxLayout()
        mem_row.setSpacing(10)
        
        lbl_mem = QLabel("Max RAM:")
        lbl_mem.setStyleSheet("color: white; font-size: 8pt; font-weight: 600;")
        lbl_mem.setFixedWidth(80)
        
        self.mem_limit = QSpinBox()
        self.mem_limit.setRange(256, 8192)
        self.mem_limit.setValue(1024)
        self.mem_limit.setSuffix(" MB")
        self.mem_limit.setAlignment(Qt.AlignCenter)
        self.mem_limit.setFixedHeight(30)
        self.mem_limit.setStyleSheet("""
            QSpinBox {
                color: white;
                background: rgba(40, 45, 60, 1);
                border: 2px solid rgba(102, 126, 234, 0.7);
                border-radius: 5px;
                font-size: 9.5pt;
                font-weight: 600;
                padding-right: 20px;
                padding-left: 8px;
            }
            QSpinBox:focus {
                border: 2px solid rgba(102, 126, 234, 1);
            }
            QSpinBox:hover {
                border: 2px solid rgba(102, 126, 234, 0.9);
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                background: rgba(102, 126, 234, 0.6);
                border-left: 1px solid rgba(80, 100, 200, 0.5);
                border-top-right-radius: 3px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
            }
            QSpinBox::up-button:hover {
                background: rgba(102, 126, 234, 0.9);
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                background: rgba(102, 126, 234, 0.6);
                border-left: 1px solid rgba(80, 100, 200, 0.5);
                border-bottom-right-radius: 3px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
            }
            QSpinBox::down-button:hover {
                background: rgba(102, 126, 234, 0.9);
            }
        """)
        
        mem_row.addWidget(lbl_mem)
        mem_row.addWidget(self.mem_limit)
        
        # Add arrow labels for Memory spinbox
        self.mem_up_arrow = QLabel("▲", self.mem_limit)
        self.mem_up_arrow.setStyleSheet("color: white; background: transparent; font-size: 8pt;")
        self.mem_up_arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.mem_up_arrow.setAlignment(Qt.AlignCenter)
        
        self.mem_down_arrow = QLabel("▼", self.mem_limit)
        self.mem_down_arrow.setStyleSheet("color: white; background: transparent; font-size: 8pt;")
        self.mem_down_arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.mem_down_arrow.setAlignment(Qt.AlignCenter)
        
        share_layout.addLayout(mem_row)
        layout.addWidget(share_gb)

        status_gb = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_gb)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(8)

        self.status_label = QLabel("Status: 🔴 Idle")
        self.status_label.setObjectName("infoLabel")

        self.conn_str = QLineEdit("N/A")
        self.conn_str.setReadOnly(True)
        self.conn_str.setStyleSheet("background: transparent; border: none; color: white;")

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setFixedSize(60, 30)
        self.copy_btn.clicked.connect(self.on_copy_clicked)

        hbox = QHBoxLayout()
        hbox.addWidget(self.conn_str)
        hbox.addWidget(self.copy_btn)

        status_layout.addWidget(self.status_label)
        status_layout.addLayout(hbox)
        layout.addWidget(status_gb)

        self.start_btn = QPushButton("Start Worker")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_worker)
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setMaximumHeight(120)
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet("""
            QPushButton#startBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5B7EEA,
                    stop:1 #5899EA);
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.9);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 9pt;
                font-weight: 600;
                text-align: center;
            }
            QPushButton#startBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6F91FF,
                    stop:1 #6AAAFF);
                border: 2px solid rgba(111, 145, 255, 1);
            }
            QPushButton#startBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A6BC8,
                    stop:1 #4781C8);
                border: 2px solid rgba(74, 107, 200, 1);
            }
            QPushButton#startBtn:disabled {
                background: rgba(80, 90, 110, 0.4);
                color: rgba(255, 255, 255, 0.4);
                border: 2px solid rgba(80, 90, 110, 0.3);
            }
        """)

        self.stop_btn = QPushButton("Stop Worker")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_worker)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setMaximumHeight(120)
        self.stop_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop_btn.setStyleSheet("""
            QPushButton#stopBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E63946,
                    stop:1 #F55A64);
                color: white;
                border: 2px solid rgba(230, 57, 70, 0.9);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 9pt;
                font-weight: 600;
                text-align: center;
            }
            QPushButton#stopBtn:hover:enabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF4D5A,
                    stop:1 #FF6B78);
                border: 2px solid rgba(255, 77, 90, 1);
            }
            QPushButton#stopBtn:pressed:enabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #C22E3A,
                    stop:1 #D13E4C);
                border: 2px solid rgba(194, 46, 58, 1);
            }
            QPushButton#stopBtn:disabled {
                background: rgba(80, 80, 90, 0.35);
                color: rgba(255, 255, 255, 0.35);
                border: 2px solid rgba(80, 80, 90, 0.25);
            }
        """)

        btn_container = QFrame()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 15, 0, 0)
        btn_layout.setSpacing(12)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addWidget(btn_container)

        layout.addStretch()
        scroll.setWidget(panel)
        return scroll

    def create_task_panel(self):
        # Scroll area wrapper for responsiveness
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        panel = QFrame()
        panel.setProperty("glass", True)
        panel.setStyleSheet("""
            QFrame {
                background: rgba(20, 25, 35, 0.5);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        panel.setMinimumWidth(500)

        tasks_gb = QGroupBox("Current Tasks")
        v = QVBoxLayout(tasks_gb)
        v.setContentsMargins(8, 20, 8, 8)
        self.tasks_display = QTextEdit()
        self.tasks_display.setObjectName("tasksDisplay")
        self.tasks_display.setReadOnly(True)
        self.tasks_display.setPlainText("No active tasks.")
        self.tasks_display.setMinimumHeight(70)
        self.tasks_display.setMaximumHeight(100)

        tasks_font = self.tasks_display.font()
        tasks_font.setFamily("Segoe UI")
        tasks_font.setBold(True)  # Make it bold for better visibility
        self.tasks_display.setFont(tasks_font)

        self.tasks_display.setStyleSheet("""
            QTextEdit#tasksDisplay {
                background-color: rgba(30, 30, 40, 0.8);
                color: #f0f0f0;
                border: 2px solid rgba(100, 255, 160, 0.4);
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.3;
            }
        """)
        v.addWidget(self.tasks_display)
        layout.addWidget(tasks_gb)

        output_gb = QGroupBox("Task Output")
        ov = QVBoxLayout(output_gb)
        ov.setContentsMargins(8, 20, 8, 8)
        self.task_output_display = QTextEdit()
        self.task_output_display.setObjectName("tasksDisplay")
        self.task_output_display.setReadOnly(True)
        self.task_output_display.setPlainText("No task output yet.")
        self.task_output_display.setMinimumHeight(80)
        self.task_output_display.setMaximumHeight(120)

        output_font = self.task_output_display.font()
        output_font.setFamily("Consolas")  # Monospace for better code/output readability
        self.task_output_display.setFont(output_font)

        self.task_output_display.setStyleSheet("""
            QTextEdit#tasksDisplay {
                background-color: rgba(30, 30, 40, 0.8);
                color: #f0f0f0;
                border: 2px solid rgba(100, 255, 160, 0.4);
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.3;
            }
        """)
        ov.addWidget(self.task_output_display)
        layout.addWidget(output_gb)

        res_gb = QGroupBox("System Resources (Real-time)")
        rv = QVBoxLayout(res_gb)
        rv.setContentsMargins(10, 15, 10, 10)
        rv.setSpacing(8)

        self.cpu_bar_layout  = self._make_bar("CPU Usage:",    "#00f5a0")
        self.mem_bar_layout  = self._make_bar("Memory Usage:", "#667eea")
        self.disk_bar_layout = self._make_bar("Disk Usage:",   "#ffb74d")

        rv.addLayout(self.cpu_bar_layout)
        rv.addLayout(self.mem_bar_layout)
        rv.addLayout(self.disk_bar_layout)

        self.cpu_bar    = self.cpu_bar_layout .itemAt(1).widget()
        self.cpu_label  = self.cpu_bar_layout .itemAt(2).widget()
        self.mem_bar    = self.mem_bar_layout .itemAt(1).widget()
        self.mem_label  = self.mem_bar_layout .itemAt(2).widget()
        self.disk_bar   = self.disk_bar_layout.itemAt(1).widget()
        self.disk_label = self.disk_bar_layout.itemAt(2).widget()

        self.res_details = QTextEdit()
        self.res_details.setReadOnly(True)
        self.res_details.setMinimumHeight(120)
        self.res_details.setMaximumHeight(120)
        res_font = self.res_details.font()
        res_font.setPointSize(9)
        res_font.setFamily("Consolas")
        self.res_details.setFont(res_font)
        self.res_details.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 25, 35, 0.9);
                color: #e8e8e8;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
                padding: 10px;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
        rv.addWidget(self.res_details)

        layout.addWidget(res_gb)

        log_gb = QGroupBox("Task Execution Log")
        lv = QVBoxLayout(log_gb)
        lv.setContentsMargins(12, 15, 12, 12)  # Better margins
        lv.setSpacing(10)  # Increased spacing

        self.task_log = QTextEdit()
        self.task_log.setReadOnly(True)

        self.task_log.setMinimumHeight(150)
        self.task_log.setMaximumHeight(250)
        self.task_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.task_log.setPlainText("=== TASK EXECUTION LOG ===\n\nWaiting for logs...")

        log_font = self.task_log.font()
        log_font.setPointSize(9)  # Slightly larger font
        log_font.setFamily("Consolas")  # Monospace for log readability
        self.task_log.setFont(log_font)

        self.task_log.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 30, 0.9);
                color: #e8e8e8;
                border: 2px solid rgba(100, 255, 160, 0.3);
                border-radius: 10px;
                padding: 12px;
                font-size: 9pt;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 2px solid rgba(100, 255, 160, 0.6);
            }
        """)

        lv.addWidget(self.task_log)
        layout.addWidget(log_gb)

        btns = QHBoxLayout()
        btns.setContentsMargins(0, 10, 0, 0)
        btns.setSpacing(12)

        c = QPushButton("🗑️ Clear Log")
        c.clicked.connect(self.clear_task_log)
        c.setMinimumHeight(42)
        c.setMinimumWidth(110)
        c.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255, 120, 120, 0.9);
            }
        """)

        e = QPushButton("📤 Export Log")
        e.clicked.connect(self.export_log)
        e.setMinimumHeight(42)
        e.setMinimumWidth(110)
        e.setStyleSheet("""
            QPushButton {
                background: rgba(100, 150, 255, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(120, 170, 255, 0.9);
            }
        """)
        
        btns.addWidget(c)
        btns.addWidget(e)
        btns.addStretch()

        layout.addLayout(btns)

        scroll.setWidget(panel)
        return scroll

    def _make_bar(self, text, color):
        h = QHBoxLayout()
        h.setSpacing(8)

        lbl = QLabel(text)
        lbl.setMinimumWidth(100)
        lbl.setObjectName("infoLabel")
        lbl_font = lbl.font()
        lbl_font.setPointSize(9)
        lbl_font.setBold(True)
        lbl.setFont(lbl_font)
        lbl.setStyleSheet("color: #e6e6fa; font-size: 9pt;")

        bar = QProgressBar()
        bar.setTextVisible(False)
        bar.setMaximumHeight(18)
        bar.setMinimumHeight(18)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 9px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color}, stop:1 {color}CC);
                border-radius: 7px;
            }}
        """)

        val = QLabel("0%")
        val.setMinimumWidth(100)
        val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        val_font = val.font()
        val_font.setPointSize(9)
        val_font.setBold(True)
        val.setFont(val_font)
        val.setStyleSheet("color: #ffffff; font-size: 9pt; padding-left: 5px;")

        h.addWidget(lbl)
        h.addWidget(bar, 1)  # Bar stretches
        h.addWidget(val)
        return h

    def apply_shadow(self, w):
        shadow = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=6, color=QColor(0,0,0,150))
        w.setGraphicsEffect(shadow)

    def update_ip(self):
        try:
            ip = socket.gethostbyname(socket.gethostname())
            self.ip_label.setText(f"IP Address: {ip}")
        except:
            self.ip_label.setText("IP Address: Unavailable")

    def start_worker(self):
        port = self.port_input.text().strip()
        if not port:
            QMessageBox.warning(self, "Missing Port", "Enter port to start.")
            return

        if self.network.start_server(int(port)):
            self.status_label.setText("Status: 🟢 Running")
            self.conn_str.setText(f"{self.network.ip}:{port}")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            start_time = time.strftime("%Y-%m-%d %H:%M:%S")
            hostname = socket.gethostname()
            print(f"[WORKER] " + "─" * 60)
            print(f"[WORKER] 🚀 Worker started at {start_time}")
            print(f"[WORKER]    💻 Hostname: {hostname}")
            print(f"[WORKER]    🌐 IP Address: {self.network.ip}")
            print(f"[WORKER]    🔌 Port: {port}")
            print(f"[WORKER]    ✓ Status: Ready to accept tasks")
            print(f"[WORKER] " + "─" * 60)

            if not self.startup_logs_shown:
                self.startup_logs_shown = True
                self.task_log_initialized = True  # Mark as initialized so first task log doesn't clear this
                self.task_log.setPlainText(
                    "=== TASK EXECUTION LOG ===\n\n"
                    f"Worker started: {start_time}\n"
                    f"Status: Ready to receive tasks from Master\n\n"
                    "Task execution details will appear here when tasks are received..."
                )
        else:
            QMessageBox.critical(self, "Error", "Failed to start.")

    def stop_worker(self):
        self.network.stop()
        self.status_label.setText("Status: 🔴 Idle")
        self.conn_str.setText("N/A")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        stop_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[WORKER] " + "─" * 60)
        print(f"[WORKER] 🛑 Worker stopped at {stop_time}")
        print(f"[WORKER]    ✓ All connections closed")
        print(f"[WORKER]    ✓ Server shutdown complete")
        print(f"[WORKER] " + "─" * 60)

    def on_copy_clicked(self):
        QApplication.clipboard().setText(self.conn_str.text())
        prev = self.status_label.text()
        self.status_label.setText("✅ Copied!")
        QTimer.singleShot(2000, lambda: self.status_label.setText(prev))

    def handle_task_request(self, data):
        task_id = data.get("task_id")
        code = data.get("code", "")
        payload = data.get("data", {})

        if not task_id or not code:
            self._send_error_to_master(task_id or "unknown", "Invalid task payload received by worker.")
            return

        task_name = data.get("name", "Unnamed Task")
        
        # Special handling for VIDEO_PLAYBACK tasks
        if task_name == "VIDEO_PLAYBACK":
            self.handle_video_playback_task(task_id, payload, task_name)
            return
        
        receive_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"📥 Task received: '{task_name}' [ID: {task_id[:8]}...] at {receive_time}")
        self.log(f"   📋 Task queued for execution")

        with self.tasks_lock:
            self.current_tasks[task_id] = {
                "status": "received",
                "progress": 0,
                "started_at": None,
                "memory_used_mb": 0,
                "output": None,
                "name": task_name
            }

        QTimer.singleShot(0, self._refresh_tasks_display)
        QTimer.singleShot(0, self._refresh_output_display)

        # Get current resource limits from UI
        cpu_limit = int(self.cpu_limit.value())
        mem_limit = int(self.mem_limit.value())
        
        # Apply resource limits to task executor
        self.task_executor.set_resource_limits(cpu_percent=cpu_limit, memory_mb=mem_limit)

        # Create and start background task thread (prevents UI freezing)
        task_thread = TaskExecutionThread(
            task_id=task_id,
            task_name=task_name,
            code=code,
            payload=payload,
            task_executor=self.task_executor,
            network=self.network,
            worker_ip=self.network.ip
        )
        
        # Connect signals for thread-safe UI updates
        task_thread.log_signal.connect(self.log)
        task_thread.progress_signal.connect(self._handle_progress_update)
        task_thread.state_update_signal.connect(self._handle_state_update)
        task_thread.refresh_display_signal.connect(self._refresh_tasks_display)
        task_thread.task_complete_signal.connect(self._handle_task_completion)
        
        # Track the thread
        self.active_task_threads[task_id] = task_thread
        
        # Start execution in background
        task_thread.start()
    
    def handle_video_playback_task(self, task_id, payload, task_name):
        """Handle video playback task by opening video player window"""
        video_url = payload.get("video_url", "")
        video_title = payload.get("title", "Video Player")
        
        receive_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"🎬 Video playback task received: '{task_name}' [ID: {task_id[:8]}...]")
        self.log(f"   📺 URL: {video_url}")
        self.log(f"   ⏰ Received at: {receive_time}")
        
        if not video_url:
            error_msg = "No video URL provided"
            self.log(f"   ❌ Error: {error_msg}")
            self._send_error_to_master(task_id, error_msg)
            return
        
        # Check if video player is available
        if not VIDEO_PLAYER_AVAILABLE:
            error_msg = "Video player not available. VLC is not installed. Please install VLC media player and python-vlc package."
            self.log(f"   ⚠️  Warning: {error_msg}")
            
            # Show error message to user
            QMessageBox.warning(
                self,
                "Video Player Not Available",
                f"{error_msg}\n\n"
                f"To enable video playback:\n"
                f"1. Install VLC Media Player from https://www.videolan.org/\n"
                f"2. Run: pip install python-vlc\n"
                f"3. Restart the application\n\n"
                f"For now, opening video URL in browser..."
            )
            
            # Open in browser as fallback
            try:
                import webbrowser
                webbrowser.open(video_url)
                self.log(f"   🌐 Opened video URL in browser as fallback")
                
                # Send success response
                with self.tasks_lock:
                    self.current_tasks[task_id] = {
                        "status": "done",
                        "progress": 100,
                        "started_at": time.time(),
                        "completed_at": time.time(),
                        "memory_used_mb": 0,
                        "output": f"Video opened in browser (VLC not available): {video_title}\nURL: {video_url}",
                        "name": task_name
                    }
                
                result_payload = {
                    "success": True,
                    "result": {
                        "status": "opened_in_browser",
                        "video_url": video_url,
                        "title": video_title,
                        "note": "VLC not available, opened in browser"
                    },
                    "error": None,
                    "stdout": f"Opened in browser: {video_url}",
                    "stderr": None,
                    "execution_time": 0.1,
                    "memory_used": 0
                }
                self.network.send_task_result(task_id, result_payload)
                
            except Exception as e:
                self.log(f"   ❌ Failed to open in browser: {e}")
                self._send_error_to_master(task_id, str(e))
            
            QTimer.singleShot(0, self._refresh_tasks_display)
            return
        
        # Track task
        with self.tasks_lock:
            self.current_tasks[task_id] = {
                "status": "playing",
                "progress": 100,
                "started_at": time.time(),
                "memory_used_mb": 0,
                "output": f"Playing video: {video_title}\nURL: {video_url}",
                "name": task_name
            }
        
        QTimer.singleShot(0, self._refresh_tasks_display)
        QTimer.singleShot(0, self._refresh_output_display)
        
        def open_player():
            """Open video player in main thread"""
            try:
                self.log(f"   🎬 Opening video player window...")
                
                # Create and show video player window
                player = VideoPlayerWindow(video_url, video_title, parent=self)
                
                # Track the player window
                if not hasattr(self, 'video_players'):
                    self.video_players = []
                self.video_players.append(player)
                
                # Connect close signal to cleanup
                def on_player_closed():
                    if player in self.video_players:
                        self.video_players.remove(player)
                    
                    end_time = time.time()
                    start_time = self.current_tasks.get(task_id, {}).get("started_at", end_time)
                    duration = end_time - start_time
                    
                    self.log(f"   🔒 Video player closed after {duration:.1f}s")
                    
                    # Send completion result to master
                    result_payload = {
                        "success": True,
                        "result": {
                            "status": "completed",
                            "video_url": video_url,
                            "title": video_title,
                            "duration": duration
                        },
                        "error": None,
                        "stdout": f"Video played for {duration:.1f} seconds",
                        "stderr": None,
                        "execution_time": duration,
                        "memory_used": 0
                    }
                    self.network.send_task_result(task_id, result_payload)
                    
                    # Update task status
                    with self.tasks_lock:
                        if task_id in self.current_tasks:
                            self.current_tasks[task_id]["status"] = "done"
                            self.current_tasks[task_id]["completed_at"] = end_time
                    
                    QTimer.singleShot(0, self._refresh_tasks_display)
                    QTimer.singleShot(5000, lambda: self._schedule_task_cleanup(task_id))
                
                player.closed.connect(on_player_closed)
                player.show()
                
                self.log(f"   ✅ Video player opened successfully")
                
                # Send initial success message to master
                msg = NetworkMessage(MessageType.PROGRESS_UPDATE, {
                    'task_id': task_id,
                    'progress': 100
                })
                self.network.send_message_to_master(msg)
                
            except Exception as e:
                error_msg = f"Failed to open video player: {str(e)}"
                self.log(f"   ❌ Error: {error_msg}")
                self._send_error_to_master(task_id, error_msg)
                
                # Update task status to failed
                with self.tasks_lock:
                    if task_id in self.current_tasks:
                        self.current_tasks[task_id]["status"] = "failed"
                        self.current_tasks[task_id]["output"] = error_msg
                
                QTimer.singleShot(0, self._refresh_tasks_display)
        
        # Schedule player opening on main thread
        QTimer.singleShot(100, open_player)
    
    def _handle_progress_update(self, task_id: str, progress: int):
        """Handle progress update from task thread (thread-safe)"""
        self.send_progress_update(task_id, progress)
    
    def _handle_state_update(self, task_id: str, state_dict: dict):
        """Handle state update from task thread (thread-safe)"""
        with self.tasks_lock:
            if task_id in self.current_tasks:
                self.current_tasks[task_id].update(state_dict)
    
    def _handle_task_completion(self, task_id: str, result: dict, exec_time: float, memory_used: float):
        """Handle task completion from thread (thread-safe)"""
        # Clean up the thread
        if task_id in self.active_task_threads:
            thread = self.active_task_threads[task_id]
            thread.wait(100)  # Wait max 100ms for thread to finish
            del self.active_task_threads[task_id]
        
        # Schedule cleanup
        QTimer.singleShot(0, lambda: self._schedule_task_cleanup(task_id))

    def send_progress_update(self, task_id: str, progress: int):
        clamped = max(0, min(100, int(progress)))
        self._set_task_state(task_id, progress=clamped)
        msg = NetworkMessage(MessageType.PROGRESS_UPDATE, {
            'task_id': task_id,
            'progress': clamped
        })
        self.network.send_message_to_master(msg)

    def clear_task_log(self):
        """Clear the task log and reset to placeholder"""
        self.task_log_initialized = False
        self.startup_logs_shown = False
        self.task_log.clear()
        self.task_log.setPlainText("=== TASK EXECUTION LOG ===\n\nWaiting for logs...")

    def log(self, msg):
        """Add a log message to the task execution log (thread-safe)"""
        now = time.strftime("%H:%M:%S")
        formatted_msg = f"[{now}] {msg}"

        self.log_signals.log_message.emit(formatted_msg)
    
    def _append_log_to_ui(self, formatted_msg):
        """Append log to UI - runs on main thread via signal"""
        try:
            if not self.task_log_initialized:

                current_text = self.task_log.toPlainText()
                lines = current_text.splitlines()
            else:
                current_text = self.task_log.toPlainText()
                lines = current_text.splitlines()[-99:]  # Keep last 99 lines
            
            lines.append(formatted_msg)
            new_text = "\n".join(lines)

            self.task_log.setPlainText(new_text)

            self.task_log.moveCursor(QTextCursor.End)
            self.task_log.ensureCursorVisible()
            
        except Exception as e:
            print(f"[LOG ERROR] Exception in log append: {e}")
            import traceback
            traceback.print_exc()

    def export_log(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save Log", f"worker_log_{int(time.time())}.txt",
                                            "Text Files (*.txt)")
        if fn:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(self.task_log.toPlainText())
            QMessageBox.information(self, "Exported", f"Log saved to {fn}")

    def start_monitoring_thread(self):
        def monitor():
            while self.monitoring_active:
                time.sleep(3)
                try:
                    stats = self.task_executor.get_system_resources()
                    if stats:

                        from functools import partial
                        callback = partial(self._update_resources, stats.copy())
                        QTimer.singleShot(0, callback)
                except Exception as exc:
                    pass
        threading.Thread(target=monitor, daemon=True).start()

    def update_resources_now(self):
        """Force an immediate resource update"""
        try:
            stats = self.task_executor.get_system_resources()
            if stats:
                self._update_resources(stats)
        except Exception as exc:
            pass

    def _update_resources(self, r):
        """Update UI with real-time resource data"""
        if not r:
            return
            
        cpu = r.get('cpu_percent', 0.0)
        mem = r.get('memory_percent', 0.0)
        disk = r.get('disk_percent', 0.0)
        battery = r.get('battery_percent')
        plugged = r.get('battery_plugged')

        try:
            cpu_limit_val = int(self.cpu_limit.value())
        except Exception:
            cpu_limit_val = 100
        try:
            mem_limit_val = int(self.mem_limit.value())
        except Exception:
            mem_limit_val = 8192

        try:
            self.cpu_bar.setValue(int(cpu))
            self.cpu_label.setText(f"{cpu:.1f}% (limit {cpu_limit_val}%)")

            self.mem_bar.setValue(int(mem))
            self.mem_label.setText(f"{mem:.1f}% (limit {mem_limit_val} MB)")
            
            self.disk_bar.setValue(int(disk))
            self.disk_label.setText(f"{disk:.1f}%")
        except Exception as e:
            pass

        battery_str = "Unavailable"
        if battery is not None:
            battery_str = f"{battery:.0f}% {'(Charging)' if plugged else ''}"

        with self.tasks_lock:
            active_tasks = len([t for t in self.current_tasks.values() if t.get('status') == 'running'])

        task_memory_mb = 0
        with self.tasks_lock:
            for task_meta in self.current_tasks.values():
                task_memory_mb += task_meta.get('memory_used_mb', 0)

        mem_total_gb = psutil.virtual_memory().total / (1024**3)
        mem_used_gb = psutil.virtual_memory().used / (1024**3)
        mem_available_mb = r.get('memory_available_mb', 0)
        disk_free_gb = r.get('disk_free_gb', 0)

        try:
            cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)
            cpu_cores_info = ", ".join([f"{c:.0f}%" for c in cpu_per_core[:4]])  # Show first 4 cores
            if len(cpu_per_core) > 4:
                cpu_cores_info += "..."
        except:
            cpu_cores_info = "N/A"
        
        details = (
            f"💻 CPU\n"
            f"  Cores: {psutil.cpu_count(logical=False)} Physical | {psutil.cpu_count()} Logical\n"
            f"  Usage: {cpu:.1f}% | Limit: {cpu_limit_val}%\n"
            f"  Per-core: {cpu_cores_info}\n"
            f"\n"
            f"🧠 Memory\n"
            f"  Total: {mem_total_gb:.2f} GB | Used: {mem_used_gb:.2f} GB ({mem:.1f}%)\n"
            f"  Available: {mem_available_mb:.0f} MB | Limit: {mem_limit_val} MB\n"
            f"  Tasks Memory: {task_memory_mb:.1f} MB\n"
            f"\n"
            f"💾 Disk\n"
            f"  Usage: {disk:.1f}% | Free: {disk_free_gb:.1f} GB\n"
            f"\n"
            f"🔋 Battery: {battery_str}\n"
            f"⚡ Active Tasks: {active_tasks}"
        )
        self.res_details.setPlainText(details)

    def _set_task_state(self, task_id: str, **updates):
        with self.tasks_lock:
            state = self.current_tasks.setdefault(task_id, {
                "status": "pending", 
                "progress": 0,
                "memory_used_mb": 0,
                "output": None
            })
            state.update(updates)
            if updates.get("output"):
                self.last_output_text = updates["output"]

        QTimer.singleShot(0, self._refresh_tasks_display)
        QTimer.singleShot(0, self._refresh_output_display)

    def _refresh_tasks_display(self):
        with self.tasks_lock:
            if not self.current_tasks:
                display = "No active tasks.\n\nWorker is ready to accept tasks from Master."
            else:
                lines = []
                for tid, meta in sorted(self.current_tasks.items(), key=lambda x: x[1].get("started_at") or 0, reverse=True):
                    progress = meta.get("progress", 0)
                    status = meta.get("status", "pending").title()
                    mem_used = meta.get("memory_used_mb", 0)
                    started_at = meta.get("started_at")
                    task_name = meta.get("name", "Task")

                    time_info = ""
                    if started_at:
                        elapsed = time.time() - started_at
                        time_info = f" | Elapsed: {elapsed:.1f}s"
                    
                    mem_str = f" | RAM: {mem_used:.1f}MB" if mem_used > 0 else ""

                    status_icon = "▶️" if status in ["Executing", "Running"] else "✅" if status == "Done" else "❌" if status == "Failed" else "📥" if status == "Received" else "⏳"
                    status_label = "EXECUTING" if status in ["Executing", "Running"] else status.upper()
                    
                    lines.append(f"{status_icon} {task_name} [{tid[:8]}]\n   Status: {status_label} | Progress: {progress}%{mem_str}{time_info}")
                display = "\n\n".join(lines)
        QTimer.singleShot(0, lambda txt=display: self.tasks_display.setPlainText(txt))
    
    def _refresh_output_display(self):
        """Display output from the most recent or active task"""
        with self.tasks_lock:
            if not self.current_tasks:
                output_text = self.last_output_text if self.last_output_text != "No task output yet." else "No task output yet.\n\nTask output will appear here when tasks are executed."
            else:

                tasks_with_output = [
                    (tid, meta) for tid, meta in self.current_tasks.items() 
                    if meta.get("output")
                ]
                if tasks_with_output:

                    tasks_with_output.sort(
                        key=lambda x: x[1].get("completed_at") or x[1].get("started_at") or 0,
                        reverse=True
                    )
                    latest_tid, latest_meta = tasks_with_output[0]
                    task_name = latest_meta.get('name', 'Task')
                    output_text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    output_text += f"{task_name} [{latest_tid[:8]}] Output:\n"
                    output_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    output_text += latest_meta.get('output', '')
                else:

                    active = [(tid, meta) for tid, meta in self.current_tasks.items() 
                             if meta.get("status") in ["executing", "running"]]
                    if active:
                        active_tid = active[0][0]
                        active_meta = active[0][1]
                        progress = active_meta.get("progress", 0)
                        task_name = active_meta.get("name", "Task")
                        output_text = f"⚙️  {task_name} [{active_tid[:8]}] is EXECUTING...\n"
                        output_text += f"\n📊 Progress: {progress}%\n"
                        output_text += f"\n⏳ Output will appear when task completes"
                    else:

                        received = [(tid, meta) for tid, meta in self.current_tasks.items() 
                                  if meta.get("status") in ["received", "pending"]]
                        if received:
                            received_tid = received[0][0]
                            task_name = received[0][1].get("name", "Task")
                            output_text = f"📥 {task_name} [{received_tid[:8]}] received\n\n⏳ Waiting to start execution..."
                        else:
                            output_text = self.last_output_text if self.last_output_text != "No task output yet." else "No task output yet."
        QTimer.singleShot(0, lambda txt=output_text: self.task_output_display.setPlainText(txt))

    def _schedule_task_cleanup(self, task_id: str, delay_ms: int = 15000):
        def cleanup():
            with self.tasks_lock:
                state = self.current_tasks.get(task_id)
                if state and state.get("status") in {"done", "failed"}:
                    self.current_tasks.pop(task_id, None)
            self._refresh_tasks_display()
        QTimer.singleShot(delay_ms, cleanup)

    def _send_error_to_master(self, task_id: str, error_message: str):
        payload = {
            "task_id": task_id,
            "error": error_message
        }
        self.network.send_message_to_master(NetworkMessage(MessageType.ERROR, payload))

    def _get_task_progress(self, task_id: str) -> int:
        with self.tasks_lock:
            return self.current_tasks.get(task_id, {}).get("progress", 0)
    
    def _create_metric_card(self, title, value, color):
        """Create a metric card widget with proper styling and layout"""
        card = QFrame()
        card.setObjectName("metricCard")
        card.setStyleSheet(f"""
            QFrame#metricCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 42, 58, 0.95),
                    stop:1 rgba(28, 34, 48, 0.95));
                border: 2px solid {color};
                border-radius: 12px;
                padding: 0px;
            }}
            QFrame#metricCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 48, 65, 0.98),
                    stop:1 rgba(32, 38, 52, 0.98));
                border: 2px solid {color};
            }}
        """)
        card.setMinimumHeight(120)
        card.setMaximumHeight(140)
        card.setMinimumWidth(200)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setAlignment(Qt.AlignTop)
        
        # Title label with icon
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10.5pt;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        title_label.setWordWrap(False)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Value label
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.98);
                font-size: 26pt;
                font-weight: 800;
                background: transparent;
                border: none;
                padding: 4px 0px;
            }
        """)
        value_label.setWordWrap(False)
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)
        
        return card, value_label
    
    def _create_resource_history_chart(self):
        """Create resource usage history chart"""
        fig = Figure(figsize=(10, 3), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(220)
        canvas.setStyleSheet("background: transparent; border: 2px solid rgba(100, 255, 160, 0.25); border-radius: 10px;")
        
        self.resource_ax = fig.add_subplot(111)
        self.resource_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def _create_network_activity_chart(self):
        """Create network activity chart"""
        fig = Figure(figsize=(5, 3), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(180)
        canvas.setStyleSheet("background: transparent; border: 2px solid rgba(100, 255, 160, 0.25); border-radius: 10px;")
        
        self.network_ax = fig.add_subplot(111)
        self.network_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def _create_task_performance_chart(self):
        """Create task performance chart"""
        fig = Figure(figsize=(5, 3), facecolor='#1a1f2e')
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(180)
        canvas.setStyleSheet("background: transparent; border: 2px solid rgba(100, 255, 160, 0.25); border-radius: 10px;")
        
        self.task_perf_ax = fig.add_subplot(111)
        self.task_perf_ax.set_facecolor('#1a1f2e')
        fig.tight_layout(pad=2)
        
        return canvas
    
    def update_visualization_data(self):
        """Update visualization data and refresh charts"""
        try:
            # Get current resource usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update history
            self.cpu_history.append(cpu_percent)
            self.mem_history.append(mem.percent)
            self.disk_history.append(disk.percent)
            
            # Calculate network throughput
            try:
                net = psutil.net_io_counters()
                if hasattr(self, '_last_net_bytes'):
                    bytes_diff = (net.bytes_sent + net.bytes_recv) - self._last_net_bytes
                    kb_per_sec = bytes_diff / 1024  # KB/s
                    self.network_history.append(kb_per_sec)
                else:
                    self.network_history.append(0)
                self._last_net_bytes = net.bytes_sent + net.bytes_recv
            except:
                self.network_history.append(0)
            
            # Update task count history
            with self.tasks_lock:
                self.task_count_history.append(len(self.current_tasks))
            
            # Calculate uptime
            if hasattr(self, '_start_time'):
                uptime_seconds = time.time() - self._start_time
                uptime_minutes = uptime_seconds / 60
                if uptime_minutes < 60:
                    uptime_str = f"{uptime_minutes:.0f}m"
                else:
                    uptime_hours = uptime_minutes / 60
                    uptime_str = f"{uptime_hours:.1f}h"
            else:
                self._start_time = time.time()
                uptime_str = "0m"
            
            # Calculate average CPU and Memory
            avg_cpu = sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0
            avg_mem = sum(self.mem_history) / len(self.mem_history) if self.mem_history else 0
            
            # Count completed tasks
            with self.tasks_lock:
                completed_count = sum(1 for meta in self.current_tasks.values() 
                                    if meta.get("status") in ["done", "completed"])
            
            # Update metric cards using the stored value labels
            self.metrics_values["tasks_completed"].setText(str(completed_count))
            self.metrics_values["avg_cpu"].setText(f"{avg_cpu:.1f}%")
            self.metrics_values["avg_mem"].setText(f"{avg_mem:.1f}%")
            self.metrics_values["uptime"].setText(uptime_str)
            
            # Update charts
            self._update_resource_history_chart()
            self._update_network_activity_chart()
            self._update_task_performance_chart()
            
        except Exception as e:
            print(f"[DEBUG] Error updating visualizations: {e}")
    
    def _update_resource_history_chart(self):
        """Update resource usage history chart"""
        try:
            self.resource_ax.clear()
            
            if len(self.cpu_history) > 0:
                times = list(range(len(self.cpu_history)))
                
                self.resource_ax.plot(times, list(self.cpu_history), color='#00f5a0', 
                                     linewidth=2, label='CPU %', alpha=0.9)
                self.resource_ax.plot(times, list(self.mem_history), color='#667eea', 
                                     linewidth=2, label='Memory %', alpha=0.9)
                self.resource_ax.plot(times, list(self.disk_history), color='#ffb74d', 
                                     linewidth=2, label='Disk %', alpha=0.9)
                
                self.resource_ax.fill_between(times, list(self.cpu_history), alpha=0.2, color='#00f5a0')
                
                self.resource_ax.set_title('Resource Usage History (Last 60s)', 
                                          color='white', fontsize=11, fontweight='bold', pad=10)
                self.resource_ax.set_xlabel('Time (s)', color='white', fontsize=8)
                self.resource_ax.set_ylabel('Usage %', color='white', fontsize=8)
                self.resource_ax.tick_params(colors='white', labelsize=7)
                self.resource_ax.legend(facecolor='#1a1f2e', edgecolor='white', 
                                       labelcolor='white', fontsize=8, loc='upper left')
                self.resource_ax.grid(True, alpha=0.2, color='white')
                self.resource_ax.set_ylim(0, 100)
                self.resource_ax.spines['bottom'].set_color('white')
                self.resource_ax.spines['left'].set_color('white')
                self.resource_ax.spines['top'].set_visible(False)
                self.resource_ax.spines['right'].set_visible(False)
            else:
                self.resource_ax.text(0.5, 0.5, 'Collecting Data...', ha='center', va='center',
                                     color='white', fontsize=12, transform=self.resource_ax.transAxes)
                self.resource_ax.set_title('Resource Usage History', 
                                          color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.resource_history_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating resource history chart: {e}")
    
    def _update_network_activity_chart(self):
        """Update network activity chart"""
        try:
            self.network_ax.clear()
            
            if len(self.network_history) > 0:
                times = list(range(len(self.network_history)))
                values = list(self.network_history)
                
                self.network_ax.plot(times, values, color='#667eea', linewidth=2)
                self.network_ax.fill_between(times, values, alpha=0.3, color='#667eea')
                
                self.network_ax.set_title('Network Activity', 
                                         color='white', fontsize=11, fontweight='bold', pad=10)
                self.network_ax.set_xlabel('Time (s)', color='white', fontsize=8)
                self.network_ax.set_ylabel('KB/s', color='white', fontsize=8)
                self.network_ax.tick_params(colors='white', labelsize=7)
                self.network_ax.grid(True, alpha=0.2, color='white')
                self.network_ax.spines['bottom'].set_color('white')
                self.network_ax.spines['left'].set_color('white')
                self.network_ax.spines['top'].set_visible(False)
                self.network_ax.spines['right'].set_visible(False)
            else:
                self.network_ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                                    color='white', fontsize=12, transform=self.network_ax.transAxes)
                self.network_ax.set_title('Network Activity', 
                                         color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.network_activity_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating network activity chart: {e}")
    
    def _update_task_performance_chart(self):
        """Update task performance chart"""
        try:
            self.task_perf_ax.clear()
            
            if len(self.task_count_history) > 0:
                times = list(range(len(self.task_count_history)))
                values = list(self.task_count_history)
                
                self.task_perf_ax.plot(times, values, color='#00f5a0', linewidth=2, 
                                      marker='o', markersize=3)
                self.task_perf_ax.fill_between(times, values, alpha=0.3, color='#00f5a0')
                
                self.task_perf_ax.set_title('Active Tasks Over Time', 
                                           color='white', fontsize=11, fontweight='bold', pad=10)
                self.task_perf_ax.set_xlabel('Time (s)', color='white', fontsize=8)
                self.task_perf_ax.set_ylabel('Task Count', color='white', fontsize=8)
                self.task_perf_ax.tick_params(colors='white', labelsize=7)
                self.task_perf_ax.grid(True, alpha=0.2, color='white')
                self.task_perf_ax.spines['bottom'].set_color('white')
                self.task_perf_ax.spines['left'].set_color('white')
                self.task_perf_ax.spines['top'].set_visible(False)
                self.task_perf_ax.spines['right'].set_visible(False)
            else:
                self.task_perf_ax.text(0.5, 0.5, 'No Task Data', ha='center', va='center',
                                      color='white', fontsize=12, transform=self.task_perf_ax.transAxes)
                self.task_perf_ax.set_title('Active Tasks Over Time', 
                                           color='white', fontsize=11, fontweight='bold', pad=10)
            
            self.task_performance_canvas.draw()
        except Exception as e:
            print(f"[DEBUG] Error updating task performance chart: {e}")

    def closeEvent(self, e):
        """Handle window close event - cleanup resources"""
        try:
            self.monitoring_active = False

            import time
            time.sleep(0.1)
            self.network.stop()
        except Exception as ex:
            pass
        finally:
            e.accept()

if __name__ == "__main__":
    import ctypes
    app = QApplication(sys.argv)
    
    # Set app ID for Windows taskbar
    try:
        myappid = 'winlink.fyp.worker.2.0'
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
    
    win = WorkerUI()
    win.showMaximized()
    sys.exit(app.exec_())
