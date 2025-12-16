# 🎬 Video Streaming Feature - WinLink

## Overview
The Video Streaming feature allows you to play videos from internet URLs on worker PCs directly from the Master PC. This is perfect for sharing presentations, tutorials, or entertainment across your distributed network.

---

## 🌟 Features

### Master PC Features
- **🌐 URL Input**: Paste any video URL (YouTube, direct MP4, streaming links)
- **📝 Custom Titles**: Set custom titles for your video streams
- **🖥️ Worker Selection**: Choose specific workers to send videos to
- **⚡ Quick Test Links**: Pre-loaded sample videos for quick testing
- **✅ Real-time Status**: Track video streaming tasks in the task queue

### Worker PC Features
- **🎬 Standalone Player**: Opens a beautiful, dedicated video player window
- **⏯️ Full Controls**: Play, pause, stop, seek, volume control
- **📊 Progress Display**: Shows current time and total duration
- **🎨 Modern UI**: Dark theme with gradient accents
- **🌐 Browser Fallback**: If VLC is unavailable, can open videos in browser
- **🔒 Clean Closing**: Proper cleanup when closing the player

---

## 🚀 Getting Started

### 1. Installation

#### Install Required Packages
```bash
pip install -r requirements.txt
```

This will install:
- `python-vlc>=3.0.0` - Python bindings for VLC media player
- All other required dependencies

#### Install VLC Media Player
The video player uses VLC as its backend. You need to install VLC separately:

**Windows:**
1. Download VLC from https://www.videolan.org/vlc/
2. Install VLC (default installation path is fine)
3. VLC will be auto-detected by python-vlc

**Linux:**
```bash
sudo apt-get install vlc
# or
sudo dnf install vlc
```

**macOS:**
```bash
brew install --cask vlc
```

### 2. Using the Video Streaming Feature

#### On Master PC:

1. **Connect a Worker**
   - Connect at least one worker PC
   - The video streaming panel will become active

2. **Enter Video URL**
   - Paste a video URL in the "Video URL" field
   - Supported formats:
     - Direct video files (MP4, AVI, MKV, etc.)
     - YouTube videos
     - Streaming URLs (M3U8, etc.)
   
3. **Set Title (Optional)**
   - Add a custom title for the video
   - If left blank, defaults to "Video Stream"

4. **Select Target Worker**
   - Choose which worker PC should play the video
   - All connected workers appear in the dropdown

5. **Click "Stream Video to Worker"**
   - Video task is sent immediately
   - You'll see a confirmation message
   - Task appears in the task queue

#### On Worker PC:

1. **Automatic Playback**
   - Video player window opens automatically
   - Video starts playing immediately

2. **Use Player Controls**
   - **⏯️ Play/Pause**: Toggle playback
   - **⏹️ Stop**: Stop video completely
   - **🔊 Volume**: Adjust volume with slider
   - **⏱️ Seek**: Click on progress bar to jump to position
   - **✖ Close**: Close the player window

3. **Monitor Status**
   - Current task display shows "VIDEO_PLAYBACK"
   - Task log records all video events
   - Output display shows video details

---

## 🎥 Supported Video Formats

### Direct Video URLs
Any direct link to a video file:
- `.mp4`, `.avi`, `.mkv`, `.mov`
- `.webm`, `.flv`, `.wmv`
- `.m4v`, `.3gp`, `.ogg`

Example:
```
https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4
```

### Streaming Protocols
- **HTTP/HTTPS streaming**
- **HLS (M3U8)**
- **RTSP streams**
- **YouTube videos** (requires yt-dlp or similar)

---

## ⚡ Quick Test URLs

The Master UI includes quick test buttons with pre-loaded sample videos:

### Sample 1: Big Buck Bunny
```
https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4
```
- **Duration**: ~10 minutes
- **Format**: MP4
- **Quality**: 720p
- **Description**: Open-source animated short film

### Sample 2: Elephant's Dream
```
https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4
```
- **Duration**: ~11 minutes
- **Format**: MP4
- **Quality**: 540p
- **Description**: First Blender open movie

---

## 🎨 UI Components

### Master PC - Video Streaming Panel

```
┌─────────────────────────────────────────────┐
│ 🎬 Video Streaming                          │
├─────────────────────────────────────────────┤
│ Stream video from internet URL to worker PC │
│                                             │
│ 🌐 Video URL:                               │
│ ┌─────────────────────────────────────────┐ │
│ │ Paste video URL here...                 │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 📝 Video Title (Optional):                  │
│ ┌─────────────────────────────────────────┐ │
│ │ Video title                             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 🖥️ Target Worker:                          │
│ ┌─────────────────────────────────────────┐ │
│ │ [Select Worker]      ▼                  │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │   🎬 Stream Video to Worker             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ⚡ Quick Test Links:                        │
│ [Sample 1] [Sample 2]                       │
└─────────────────────────────────────────────┘
```

### Worker PC - Video Player Window

```
┌─────────────────────────────────────────────────┐
│ 🎬 My Video Title          📡 video-url.com    │ (Title Bar)
├─────────────────────────────────────────────────┤
│                                                 │
│                                                 │
│             [VIDEO DISPLAY AREA]                │
│                                                 │
│                                                 │
├─────────────────────────────────────────────────┤
│ ⏯️ ⏹️ 00:45 / 10:23 [═══════════] 🔊 [═══] ✖ │ (Controls)
└─────────────────────────────────────────────────┘
```

---

## 🔧 Technical Details

### Architecture

1. **Master PC**:
   - Creates VIDEO_PLAYBACK task type
   - Packages video URL and title in task data
   - Sends task to specific worker via network

2. **Worker PC**:
   - Receives VIDEO_PLAYBACK task
   - Extracts video URL and title from task data
   - Creates VideoPlayerWindow instance
   - Opens player in new window
   - Reports playback status back to master

3. **Video Player**:
   - Uses VLC media player backend
   - Embeds video in QFrame widget
   - Provides full playback controls
   - Tracks playback time and position

### Task Flow

```
Master PC                        Worker PC
    │                                │
    ├─ Create VIDEO_PLAYBACK task   │
    │                                │
    ├─ Send task to worker ─────────>│
    │                                ├─ Receive task
    │                                ├─ Extract video URL
    │                                ├─ Open VideoPlayerWindow
    │                                ├─ Start playback
    │<──── Send progress (100%) ─────┤
    │                                │
    │                                ├─ User watches video
    │                                │
    │                                ├─ User closes player
    │<──── Send completion result ───┤
    │                                │
    ├─ Mark task complete            │
```

### Code Structure

**Master UI** (`master/master_ui.py`):
- Video streaming panel UI
- `send_video_to_worker()` method
- Worker dropdown management

**Worker UI** (`worker/worker_ui.py`):
- `handle_video_playback_task()` method
- Video player instance management
- Task status tracking

**Video Player** (`worker/video_player.py`):
- `VideoPlayerWindow` class
- VLC integration
- UI controls and playback management

---

## 🐛 Troubleshooting

### Video Player Doesn't Open

**Problem**: Video player window doesn't appear
**Solutions**:
1. Check if VLC is installed: `vlc --version`
2. Reinstall python-vlc: `pip install --force-reinstall python-vlc`
3. Check worker task log for error messages
4. Try a different video URL

### No Video Display (Black Screen)

**Problem**: Player opens but shows black screen
**Solutions**:
1. Verify video URL is accessible (try in browser)
2. Check internet connection on worker PC
3. Try a direct MP4 URL instead of streaming
4. Check VLC version compatibility

### VLC Not Found Error

**Problem**: Error message "VLC not available"
**Solutions**:
1. Install VLC media player
2. Add VLC to system PATH (Windows)
3. Use browser fallback (click "Open in Browser")

### YouTube Videos Not Playing

**Problem**: YouTube URLs don't work
**Solutions**:
1. Use direct video URLs instead of YouTube
2. Install youtube-dl or yt-dlp
3. Use one of the provided sample URLs
4. Download video and host it directly

### Controls Not Responding

**Problem**: Play/pause buttons don't work
**Solutions**:
1. Wait for video to fully load
2. Check network connection
3. Try stopping and restarting playback
4. Close and reopen player

---

## 💡 Tips & Best Practices

### For Best Performance:
1. **Use Direct URLs**: Direct video files load faster than streaming
2. **Smaller Videos**: Start with smaller videos to test
3. **Stable Connection**: Ensure worker has good internet connection
4. **Close When Done**: Close player windows when not needed

### URL Recommendations:
- ✅ Use HTTPS URLs (more secure)
- ✅ Test URL in browser first
- ✅ Prefer MP4 format for compatibility
- ✅ Use sample URLs provided for testing
- ❌ Avoid very large files (>500MB)
- ❌ Avoid region-locked content

### Workflow Tips:
1. **Test Connection**: Send a simple task first
2. **Use Quick Links**: Start with provided samples
3. **Set Descriptive Titles**: Helps track multiple videos
4. **Monitor Task Log**: Check for errors in real-time

---

## 🔒 Security Considerations

### URL Validation:
- Master PC validates URL format (http/https)
- Worker PC creates isolated player window
- No automatic download or file execution

### Network Safety:
- Videos stream directly from source
- No video data stored on Master PC
- Worker PC handles all playback locally

### Recommendations:
- Only use trusted video sources
- Avoid clicking unknown URLs
- Monitor network bandwidth usage
- Use VPN if needed for privacy

---

## 🚀 Future Enhancements

Potential features for future versions:

1. **📺 Multiple Players**: Play videos on multiple workers simultaneously
2. **📊 Synchronized Playback**: Sync video across multiple workers
3. **💾 Local File Support**: Upload and stream local video files
4. **🎙️ Audio Streaming**: Stream audio-only content
5. **📹 Screen Share**: Share screen from Master to Workers
6. **🎮 Interactive Controls**: Control playback from Master PC
7. **📱 Mobile Support**: Stream to mobile worker apps
8. **☁️ Cloud Integration**: Direct streaming from cloud storage

---

## 📞 Support

### Getting Help:
- Check task logs on both Master and Worker
- Verify VLC installation
- Test with provided sample URLs
- Review error messages in UI

### Common Issues:
1. **No workers connected**: Connect worker first
2. **Invalid URL**: Check URL format
3. **VLC missing**: Install VLC media player
4. **Network error**: Check internet connection

---

## 📄 License & Credits

### Video Samples:
- Big Buck Bunny © Blender Foundation (CC BY 3.0)
- Elephant's Dream © Blender Foundation (CC BY 2.5)

### Libraries Used:
- **python-vlc**: Python bindings for VLC
- **PyQt5**: UI framework
- **VLC Media Player**: Video playback engine

---

## 🎯 Quick Reference

### Master PC Commands:
| Action | Steps |
|--------|-------|
| Send Video | Enter URL → Select Worker → Click "Stream Video" |
| Use Sample | Click "Sample 1" or "Sample 2" → Send |
| Change Worker | Select from dropdown → Send |

### Worker PC Controls:
| Control | Function |
|---------|----------|
| ⏯️ | Play / Pause |
| ⏹️ | Stop playback |
| 🔊 | Adjust volume |
| Progress Bar | Seek to position |
| ✖ Close | Exit player |

### Keyboard Shortcuts (in player):
| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Esc | Close player |
| ↑ | Volume up |
| ↓ | Volume down |
| → | Seek forward |
| ← | Seek backward |

---

**Enjoy streaming videos across your WinLink network! 🎬✨**
