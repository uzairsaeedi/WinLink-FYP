# WinLink — Distributed Computing Platform

**WinLink is a modern distributed desktop application for Windows that enables secure, real-time task distribution between master and worker PCs.**

---

## 🌐 Official Website

Visit: [https://uzairsaeedi.github.io/WinLink-FYP/](https://uzairsaeedi.github.io/WinLink-FYP/)

---

## 🚀 Key Features

- **Easy Task Distribution:** Send Python tasks to any PC on your network
- **User-Friendly Roles:** Choose Master or Worker with a single click
- **Live Monitoring:** See real-time CPU, memory, and task progress
- **Secure by Default:** TLS encryption, authentication, and process isolation
- **Modern UI:** Beautiful PyQt5 interface with glassmorphic design
- **Templates for All:** Built-in templates for common tasks (Computation, File, Image, Video, System, Network, Text, ML, API, Custom)

---

## 🧩 Supported Task Types (for Everyone)

- **Computation** — Math and calculations
- **File Processing** — Work with files and data
- **Image Processing** — Analyze or edit images
- **Video Playback** — Play videos on remote PC
- **System Check** — Monitor PC health
- **Network Test** — Check network connectivity
- **Text Analysis** — Analyze or process text
- **Machine Learning** — Simple ML tasks
- **API Request** — Fetch data from the web
- **Custom Task** — Anything you want!

---

## 📋 System Requirements
- Windows 10/11 (x64)
- Python 3.8+ (3.9+ recommended)
- 4GB RAM minimum (8GB recommended)
- 100MB free disk space
- Windows PowerShell 5.1+ (included in Windows)

---

## ⚡ Quick Start

### 1. Clone the Repository

```powershell
git clone https://github.com/uzairsaeedi/WinLink-FYP.git
cd WinLink-FYP
```

### 2. Automated Setup (Recommended)

```powershell
.\setup_windows.bat
```

- Installs dependencies
- Generates TLS certificates
- Creates authentication tokens
- Runs security tests
- Launches the app

### 3. Manual Setup (Advanced)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python windows_setup_certificates.py
python test_windows_security.py
```

### 4. Configure Firewall (Required)

Run as Administrator on **BOTH** Master and Worker PCs:

```powershell
.\setup_firewall.bat
```

---

## 🚦 How to Use

### Master PC
1. Launch WinLink and select **Master**
2. Wait for workers to appear or add manually
3. Create a task (choose a template or write your own)
4. Submit and monitor progress

### Worker PC
1. Launch WinLink and select **Worker**
2. Set resource limits (CPU, memory)
3. Click **Start Worker**
4. Share your IP:Port with Master if needed

---

## 🗂️ Project Structure

```
WinLink-FYP/
├── core/         # Core logic (network, security, tasks, config)
├── master/       # Master UI
├── worker/       # Worker UI
├── ui/           # Shared UI components
├── assets/       # Icons, styles
├── data/         # SQLite database
├── logs/         # Application logs
├── secrets/      # Auth tokens (auto-generated)
├── ssl/          # TLS certificates (auto-generated)
├── main.py       # Main entry point
├── launch_enhanced.py  # Enhanced launcher
├── requirements.txt    # Python dependencies
├── setup_windows.bat   # Automated setup
├── setup_firewall.bat  # Firewall config
└── website/      # Official website (React)
```

---

## 🛠️ Troubleshooting

- **Firewall:** Run `setup_firewall.bat` as Administrator on both PCs
- **Certificates:** Run `python windows_setup_certificates.py` if SSL errors
- **Dependencies:** Run `pip install -r requirements.txt`
- **Logs:** Check the `logs/` folder for error details

---

## 🌍 Website & Documentation

- **Website:** [https://uzairsaeedi.github.io/WinLink-FYP/](https://uzairsaeedi.github.io/WinLink-FYP/)

---

## 🤝 Contributing

Pull requests and feedback are welcome! See the website for more info.

---

**WinLink — Distributed Computing for Everyone**
