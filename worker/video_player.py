"""
Video Player Window for Worker PC
Plays videos from URLs using VLC backend
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QStyle, QSizePolicy, QMessageBox, QFrame, QDesktopWidget
)
from core.ui import show_error, show_info, show_warning
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont
import sys
import os

# Try to import VLC, fallback to basic web player
VLC_AVAILABLE = False
try:
    # Add VLC paths for Windows
    if sys.platform == 'win32':
        # Common VLC installation paths
        vlc_paths = [
            r'C:\Program Files\VideoLAN\VLC',
            r'C:\Program Files (x86)\VideoLAN\VLC',
        ]
        for vlc_path in vlc_paths:
            if os.path.exists(vlc_path):
                try:
                    os.add_dll_directory(vlc_path)
                except:
                    pass
                os.environ['PATH'] = vlc_path + os.pathsep + os.environ.get('PATH', '')
                break
    
    import vlc
    VLC_AVAILABLE = True
except (ImportError, OSError) as e:
    VLC_AVAILABLE = False
    # VLC is optional - only show message if debugging
    pass
except Exception as e:
    VLC_AVAILABLE = False
    pass


class VideoPlayerWindow(QWidget):
    """Standalone video player window"""
    
    closed = pyqtSignal()  # Signal emitted when window is closed
    
    def __init__(self, video_url, title="Video Player", parent=None):
        super().__init__(parent)
        self.video_url = video_url
        self.video_title = title
        self.vlc_instance = None
        self.media_player = None
        self.media = None
        self.timer = None
        
        self.setWindowTitle(f"🎬 {title}")
        self.setMinimumSize(800, 500)
        
        # Set responsive default size (80% of screen)
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        default_width = int(screen_rect.width() * 0.8)
        default_height = int(screen_rect.height() * 0.8)
        self.resize(default_width, default_height)
        
        # Center window on screen
        self.move(
            (screen_rect.width() - default_width) // 2,
            (screen_rect.height() - default_height) // 2
        )
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: white;
            }
        """)
        
        self.setup_ui()
        self.load_video()
        
    def setup_ui(self):
        """Setup the video player UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #00f5a0);
                padding: 10px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        
        title_label = QLabel(f"🎬 {self.video_title}")
        title_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold; background: transparent;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        url_label = QLabel(f"📡 {self.video_url[:50]}..." if len(self.video_url) > 50 else f"📡 {self.video_url}")
        url_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 9pt; background: transparent;")
        title_layout.addWidget(url_label)
        
        layout.addWidget(title_bar)
        
        # Video frame
        if VLC_AVAILABLE:
            self.video_frame = QFrame()
            self.video_frame.setStyleSheet("background-color: black;")
            palette = self.video_frame.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0))
            self.video_frame.setPalette(palette)
            self.video_frame.setAutoFillBackground(True)
            self.video_frame.setMinimumHeight(400)
            layout.addWidget(self.video_frame)
        else:
            # Fallback: Show message that VLC is not available
            fallback_frame = QFrame()
            fallback_frame.setStyleSheet("background-color: #2a2a2a; border: 2px dashed #667eea;")
            fallback_layout = QVBoxLayout(fallback_frame)
            
            icon_label = QLabel("🎬")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("font-size: 72pt; background: transparent;")
            fallback_layout.addWidget(icon_label)
            
            msg_label = QLabel("Video Player Not Available")
            msg_label.setAlignment(Qt.AlignCenter)
            msg_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #667eea; background: transparent;")
            fallback_layout.addWidget(msg_label)
            
            url_display = QLabel(f"URL: {self.video_url}")
            url_display.setAlignment(Qt.AlignCenter)
            url_display.setStyleSheet("font-size: 10pt; color: #00f5a0; background: transparent; padding: 10px;")
            url_display.setWordWrap(True)
            fallback_layout.addWidget(url_display)
            
            info_label = QLabel("To enable video playback:\n\n1. Install VLC media player\n2. Install python-vlc: pip install python-vlc")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("font-size: 11pt; color: rgba(255,255,255,0.7); background: transparent; padding: 20px;")
            fallback_layout.addWidget(info_label)
            
            open_browser_btn = QPushButton("🌐 Open in Browser")
            open_browser_btn.setStyleSheet("""
                QPushButton {
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 12pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #5568d3;
                }
            """)
            open_browser_btn.clicked.connect(self.open_in_browser)
            fallback_layout.addWidget(open_browser_btn, alignment=Qt.AlignCenter)
            
            fallback_layout.addStretch()
            layout.addWidget(fallback_frame)
        
        # Control bar
        control_bar = QFrame()
        control_bar.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-top: 1px solid #444;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout(control_bar)
        
        # Play/Pause button
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_btn.setFixedSize(48, 48)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                border: none;
                border-radius: 24px;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:pressed {
                background-color: #4457bb;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        control_layout.addWidget(self.play_pause_btn)
        
        # Stop button
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5252;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #ff3838;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_video)
        control_layout.addWidget(self.stop_btn)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 11pt; padding: 0 10px; background: transparent;")
        control_layout.addWidget(self.time_label)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #444;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00f5a0;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #667eea;
                border-radius: 3px;
            }
        """)
        self.position_slider.sliderMoved.connect(self.set_position)
        control_layout.addWidget(self.position_slider, 1)
        
        # Volume slider
        volume_icon = QLabel("🔊")
        volume_icon.setStyleSheet("font-size: 14pt; padding: 0 5px; background: transparent;")
        control_layout.addWidget(volume_icon)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet(self.position_slider.styleSheet())
        self.volume_slider.valueChanged.connect(self.set_volume)
        control_layout.addWidget(self.volume_slider)
        
        # Close button
        close_btn = QPushButton("✖ Close")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_btn.clicked.connect(self.close)
        control_layout.addWidget(close_btn)
        
        layout.addWidget(control_bar)
        
    def load_video(self):
        """Load and play the video"""
        if not VLC_AVAILABLE:
            print(f"[VIDEO] VLC not available, cannot play video: {self.video_url}")
            return
        
        try:
            # Create VLC instance
            self.vlc_instance = vlc.Instance('--no-xlib')
            self.media_player = self.vlc_instance.media_player_new()
            
            # Set video output to the frame
            if sys.platform.startswith('linux'):
                self.media_player.set_xwindow(int(self.video_frame.winId()))
            elif sys.platform == "win32":
                self.media_player.set_hwnd(int(self.video_frame.winId()))
            elif sys.platform == "darwin":
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            # Create media
            self.media = self.vlc_instance.media_new(self.video_url)
            self.media_player.set_media(self.media)
            
            # Set initial volume
            self.media_player.audio_set_volume(50)
            
            # Start playback
            self.media_player.play()
            
            # Start timer to update UI
            self.timer = QTimer()
            self.timer.setInterval(100)  # Update every 100ms
            self.timer.timeout.connect(self.update_ui)
            self.timer.start()
            
            # Update play button icon
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            
            print(f"[VIDEO] ✅ Playing video: {self.video_url}")
            
        except Exception as e:
            print(f"[VIDEO] ❌ Error loading video: {e}")
            show_error(self, "Error", f"Failed to load video:\n{str(e)}", details=str(e))
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.media_player:
            return
        
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            print("[VIDEO] ⏸️  Video paused")
        else:
            self.media_player.play()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            print("[VIDEO] ▶️  Video playing")
    
    def stop_video(self):
        """Stop video playback"""
        if self.media_player:
            self.media_player.stop()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            print("[VIDEO] ⏹️  Video stopped")
    
    def set_position(self, position):
        """Set video position from slider"""
        if self.media_player:
            self.media_player.set_position(position / 1000.0)
    
    def set_volume(self, volume):
        """Set volume from slider"""
        if self.media_player:
            self.media_player.audio_set_volume(volume)
    
    def update_ui(self):
        """Update UI elements (time, position slider)"""
        if not self.media_player:
            return
        
        # Update position slider
        position = self.media_player.get_position()
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(int(position * 1000))
        self.position_slider.blockSignals(False)
        
        # Update time label
        current_time = self.media_player.get_time() // 1000  # milliseconds to seconds
        total_time = self.media_player.get_length() // 1000
        
        current_str = f"{current_time // 60:02d}:{current_time % 60:02d}"
        total_str = f"{total_time // 60:02d}:{total_time % 60:02d}"
        self.time_label.setText(f"{current_str} / {total_str}")
    
    def open_in_browser(self):
        """Open video URL in default browser"""
        import webbrowser
        webbrowser.open(self.video_url)
        print(f"[VIDEO] 🌐 Opened in browser: {self.video_url}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.media_player:
            self.media_player.stop()
        if self.timer:
            self.timer.stop()
        
        print(f"[VIDEO] 🔒 Video player closed")
        self.closed.emit()
        event.accept()


if __name__ == "__main__":
    # Test the video player
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test URL (Big Buck Bunny sample video)
    test_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    player = VideoPlayerWindow(test_url, "Test Video")
    player.show()
    
    sys.exit(app.exec_())
