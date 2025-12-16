import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from master.master_ui import MasterUI
from worker.worker_ui import WorkerUI
from assets.styles import STYLE_SHEET
import os

class RoleCard(QFrame):
    def __init__(self, role, title, description, icon, features=None, parent=None):
        super().__init__(parent)
        self.setObjectName("roleCard")
        self.setProperty("role", role)  # 'master' or 'worker'
        self.setMinimumSize(350, 380)
        self.setMaximumSize(500, 480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.role = role

        if role == 'master':
            self.card_accent = '#00ffe0'
            self.border_color = 'rgba(0, 255, 224, 0.3)'
            self.hover_border = 'rgba(0, 255, 224, 0.6)'
        else:
            self.card_accent = '#ff6b6b'
            self.border_color = 'rgba(255, 107, 107, 0.3)'
            self.hover_border = 'rgba(255, 107, 107, 0.6)'
        
        self.setStyleSheet(f"""
            QFrame#roleCard {{
                background: rgba(255, 255, 255, 0.12);
                border: 2px solid {self.border_color};
                border-radius: 20px;
                padding: 5px;
            }}
            QFrame#roleCard:hover {{
                background: rgba(255, 255, 255, 0.18);
                border: 2px solid {self.hover_border};
            }}
        """)
        
        self.setup_ui(title, description, icon, features)
        self.setup_shadow()
        self.setup_animations()

    def setup_ui(self, title, desc, icon, features):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("""
            font-size: 26px; 
            margin-bottom: 2px;
            color: #ffffff;
        """)
        header_layout.addWidget(self.icon_lbl, alignment=Qt.AlignCenter)

        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {self.card_accent};
            letter-spacing: 1px;
        """)
        header_layout.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignCenter)
        self.desc_lbl.setStyleSheet("""
            font-size: 16px;
            color: #e6e6fa;
            margin: 10px 15px 20px 15px;
            line-height: 1.5;
        """)
        header_layout.addWidget(self.desc_lbl)

        layout.addLayout(header_layout)

        if features:
            for feature in features:
                feature_item = QLabel(f"✓ {feature}")
                feature_item.setWordWrap(True)
                feature_item.setAlignment(Qt.AlignLeft)
                feature_item.setStyleSheet("""
                    font-size: 14px;
                    color: #b8c5d6;
                    margin: 8px 20px;
                    padding: 5px;
                """)
                layout.addWidget(feature_item)

        action_hint = QLabel("Click to select")
        action_hint.setAlignment(Qt.AlignCenter)
        action_hint.setStyleSheet(f"""
            font-size: 14px;
            color: {self.card_accent};
            margin-top: 20px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            font-weight: 500;
        """)
        layout.addWidget(action_hint)

        layout.addStretch()

    def setup_shadow(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(25)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(8)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(self.shadow)

    def setup_animations(self):
        # No size animation needed - just use hover effects
        pass

    def enterEvent(self, event):
        # Enhanced shadow on hover
        self.shadow.setBlurRadius(35)
        self.shadow.setYOffset(12)
        self.shadow.setColor(QColor(0, 245, 160, 150) if self.role == "master" else QColor(255, 107, 107, 150))
        
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Reset shadow
        self.shadow.setBlurRadius(25)
        self.shadow.setYOffset(8)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        
        super().leaveEvent(event)

class RoleSelectScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("roleSelectScreen")
        self.setWindowTitle("WinLink – Select Your Role")
        self.setMinimumSize(900, 700)
        
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "WinLink_logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(STYLE_SHEET)
        
        self.setup_ui()
        self.setup_animations()
        QTimer.singleShot(150, self.start_entrance_animations)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scrollable content area for responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 255, 224, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 255, 224, 0.5);
            }
        """)

        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(60, 40, 60, 60)
        content_layout.setSpacing(30)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.main_title = QLabel("🔗 Choose Your Role")
        self.main_title.setAlignment(Qt.AlignCenter)
        self.main_title.setWordWrap(True)
        self.main_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.main_title.setStyleSheet("""
            font-size: clamp(20px, 4vw, 32px);
            font-weight: bold;
            color: #00ffe0;
            margin: 20px;
        """)
        content_layout.addWidget(self.main_title)

        self.subtitle = QLabel(
            "Select how you want to participate in the distributed computing network"
        )
        self.subtitle.setWordWrap(True)
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.subtitle.setStyleSheet("""
            font-size: 14px;
            color: #c1d5e0;
            margin: 10px 40px 30px 40px;
        """)
        content_layout.addWidget(self.subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        cards_layout.setContentsMargins(20, 20, 20, 20)

        master = RoleCard(
            role="master",
            title="Master PC",
            description="Control and distribute computing tasks across the network",
            icon="🎯",
            features=[
                "Create and manage tasks",
                "Monitor worker performance",
                "Real-time distribution",
                "Advanced analytics"
            ]
        )
        master.mousePressEvent = lambda e: self.open_master_ui()

        worker = RoleCard(
            role="worker",
            title="Worker PC",
            description="Contribute your PC’s processing power",
            icon="⚡",
            features=[
                "Share CPU & RAM",
                "Safe task execution",
                "Monitor usage",
                "Auto load-balancing"
            ]
        )
        worker.mousePressEvent = lambda e: self.open_worker_ui()

        cards_layout.addStretch(1)
        cards_layout.addWidget(master, 3)
        cards_layout.addWidget(worker, 3)
        cards_layout.addStretch(1)

        content_layout.addLayout(cards_layout)

        content_layout.addStretch()
        
        self.back_btn = QPushButton("← Back to Welcome")
        self.back_btn.setMinimumSize(180, 40)
        self.back_btn.setMaximumSize(220, 45)
        self.back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                color: white;
                font-size: 14px;
                border: 1px solid #606060;
                border-radius: 5px;
            }
            QPushButton:hover { background: #505050; }
        """)
        content_layout.addWidget(self.back_btn, alignment=Qt.AlignCenter)

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

        app_icon = QLabel("🔗")
        app_icon.setObjectName("appIcon")
        from PyQt5.QtGui import QFont
        app_icon.setFont(QFont("Segoe UI Emoji", 16))
        app_info_layout.addWidget(app_icon)

        title_label = QLabel("WinLink - Role Selection")
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

    def setup_animations(self):

        self.title_anim = QPropertyAnimation(self.main_title, b"windowOpacity")
        self.title_anim.setDuration(800)
        self.title_anim.setStartValue(0.0)
        self.title_anim.setEndValue(1.0)
        self.title_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.sub_anim = QPropertyAnimation(self.subtitle, b"pos")
        self.sub_anim.setDuration(600)
        self.sub_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.btn_anim = QPropertyAnimation(self.back_btn, b"windowOpacity")
        self.btn_anim.setDuration(600)
        self.btn_anim.setStartValue(0.0)
        self.btn_anim.setEndValue(1.0)
        self.btn_anim.setEasingCurve(QEasingCurve.OutCubic)

    def start_entrance_animations(self):
        self.main_title.setWindowOpacity(0.0)
        self.back_btn.setWindowOpacity(0.0)

        self.title_anim.start()
        QTimer.singleShot(200, self._start_sub_anim)
        QTimer.singleShot(400, self._start_btn_anim)

    def _start_sub_anim(self):
        cp = self.subtitle.pos()
        self.subtitle.move(cp.x(), cp.y() - 30)
        self.sub_anim.setStartValue(self.subtitle.pos())
        self.sub_anim.setEndValue(cp)
        self.sub_anim.start()

    def _start_btn_anim(self):
        self.btn_anim.start()

    def open_master_ui(self):
        self.master_ui = MasterUI()
        self.master_ui.showMaximized()
        self.close()

    def open_worker_ui(self):
        self.worker_ui = WorkerUI()
        self.worker_ui.showMaximized()
        self.close()

    def go_back(self):
        from main import WelcomeScreen
        self.welcome = WelcomeScreen()
        self.welcome.showMaximized()
        self.close()

if __name__ == "__main__":
    import ctypes
    app = QApplication(sys.argv)
    
    try:
        myappid = 'winlink.fyp.distributed.2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
    
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "WinLink_logo.ico")
    if os.path.exists(icon_path):
        from PyQt5.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))
    
    win = RoleSelectScreen()
    win.showMaximized()
    sys.exit(app.exec_())
