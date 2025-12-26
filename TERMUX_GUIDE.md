# DemonX Nuker - Complete Termux Setup & Usage Guide

## 📱 Overview

This guide provides step-by-step instructions for installing and using DemonX Nuker on Termux (Android). The application is designed to work on Android devices through the Termux terminal emulator.

**Important Notes:**
- ✅ CLI version (`demonx_complete.py`) works on Termux
- ❌ GUI version (`demonx_gui.py`) does NOT work on Termux (requires desktop environment)
- ✅ All core features are available in CLI version
- ✅ Background execution supported via tmux

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Android Device** (Android 7.0+ recommended)
2. **Termux App** installed from:
   - [F-Droid](https://f-droid.org/packages/com.termux/) (recommended)
   - [GitHub Releases](https://github.com/termux/termux-app/releases)
3. **Internet Connection** (for downloading packages and dependencies)
4. **Discord Bot Token** (from [Discord Developer Portal](https://discord.com/developers/applications))
5. **Storage Permission** (granted to Termux)

---

## 🚀 Step-by-Step Installation

### Step 1: Install Termux

1. Download Termux from F-Droid or GitHub
2. Install the APK on your Android device
3. Open Termux app
4. Grant storage permission when prompted:
   ```bash
   termux-setup-storage
   ```

### Step 2: Update Termux Packages

```bash
pkg update -y
pkg upgrade -y
```

This ensures you have the latest package repositories and system updates.

### Step 3: Install Required System Packages

```bash
pkg install -y python python-pip git
```

**What this installs:**
- `python` - Python 3 interpreter
- `python-pip` - Python package manager
- `git` - Version control (if you need to clone the repository)

### Step 4: Navigate to Project Directory

**First, check what's in your storage directory:**

```bash
# Navigate to storage
cd ~/storage/shared

# List all files and directories
ls -la
```

**Option A: If project is already in storage/shared**

If you see `DemonX-Nuker-main` folder:
```bash
cd ~/storage/shared/DemonX-Nuker-main
```

**Option B: If project is in Downloads or elsewhere**

```bash
# Check Downloads folder
ls ~/storage/shared/Download

# Or check DCIM (some file managers put files here)
ls ~/storage/shared/DCIM

# Navigate to where you find it
cd ~/storage/shared/Download/DemonX-Nuker-main
# (adjust path based on where you find it)
```

**Option C: Copy project to Termux home directory (Recommended)**

This is the easiest approach - copy the project to Termux's home:

```bash
# Go to storage
cd ~/storage/shared

# Find the project (check common locations)
find . -name "DemonX-Nuker-main" -type d 2>/dev/null

# Once found, copy to Termux home
cp -r /path/to/DemonX-Nuker-main ~/

# Navigate to it
cd ~/DemonX-Nuker-main
```

**Option D: Clone from GitHub (if you have the repository URL)**

```bash
cd ~
git clone <repository-url>
cd DemonX-Nuker-main
```

**Option E: Transfer files manually**

1. Use a file manager app to locate `DemonX-Nuker-main` folder
2. Copy it to: `Internal Storage/Download/` or `Internal Storage/Documents/`
3. Then in Termux:
   ```bash
   cd ~/storage/shared/Download/DemonX-Nuker-main
   # or
   cd ~/storage/shared/Documents/DemonX-Nuker-main
   ```

### Step 5: Run the Setup Script

The project includes an automated setup script specifically for Termux:

```bash
# Make the script executable
chmod +x setup_termux.sh

# Run the setup script
bash setup_termux.sh
```

**What the setup script does:**
1. ✅ Verifies you're running on Termux
2. ✅ Updates Termux packages (`pkg update && pkg upgrade`)
3. ✅ Installs Python, pip, and git
4. ✅ Upgrades pip to latest version
5. ✅ Installs Python dependencies from `requirements.txt`
6. ✅ Creates default `config.json` if it doesn't exist
7. ✅ Verifies Python installation
8. ✅ Checks critical dependencies

**Manual Setup (if script doesn't work):**

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Or install core dependencies manually
pip install discord.py==2.3.2 httpx==0.25.0 colorama==0.4.6 aiohttp==3.9.0 rich pyfiglet
```

### Step 6: Verify Installation

Test that everything is installed correctly:

```bash
# Check Python version (should be 3.8+)
python3 --version

# Test critical imports
python3 -c "import discord; import aiohttp; import colorama; print('All dependencies OK')"
```

If you see "All dependencies OK", you're ready to proceed!

---

## ⚙️ Configuration

### Create/Edit config.json

The setup script should have created `config.json`, but you can verify/edit it:

```bash
# View current config
cat config.json

# Edit config (using nano editor)
nano config.json
```

**Default config.json:**
```json
{
  "proxy": false,
  "dry_run": false,
  "verbose": true,
  "version": "2.3"
}
```

**Configuration Options:**
- `proxy` (boolean) - Enable proxy support (requires `proxies.txt`)
- `dry_run` (boolean) - Test mode (operations logged but not executed)
- `verbose` (boolean) - Enable detailed output
- `version` (string) - Configuration version

### Optional: Setup Proxies

If you want to use proxies:

1. Create `proxies.txt` file:
   ```bash
   nano proxies.txt
   ```

2. Add proxies in format (one per line):
   ```
   IP:PORT:USERNAME:PASSWORD
   192.168.1.1:8080:user:pass
   10.0.0.1:3128:proxyuser:proxypass
   ```

3. Set `"proxy": true` in `config.json`

---

## 🎮 Running DemonX Nuker

### Method 1: Direct Execution (Foreground)

```bash
python3 demonx_complete.py
```

**Note:** This runs in the foreground. If you close Termux or the app is killed, the process will stop.

### Method 2: Background Execution with tmux (Recommended)

tmux allows you to run the application in the background and detach/reattach to the session.

#### Install tmux:
```bash
pkg install -y tmux
```

#### Start a tmux session:
```bash
tmux
```

#### Run DemonX in tmux:
```bash
python3 demonx_complete.py
```

#### Detach from tmux session:
- Press `Ctrl+B`, then press `D`
- The application continues running in the background

#### Reattach to tmux session:
```bash
# List sessions
tmux ls

# Attach to session (if only one session)
tmux attach

# Or attach to specific session
tmux attach -t 0
```

#### Kill tmux session:
```bash
# From inside tmux: Press Ctrl+B, then X, then Y
# Or from terminal:
tmux kill-session
```

### Method 3: Background Execution with nohup

Alternative method for background execution:

```bash
nohup python3 demonx_complete.py > output.log 2>&1 &
```

**Check if running:**
```bash
ps aux | grep python3
```

**View output:**
```bash
tail -f output.log
```

**Stop the process:**
```bash
# Find process ID
ps aux | grep python3

# Kill process (replace PID with actual process ID)
kill PID
```

---

## 📖 Usage Instructions

### Initial Setup in Application

1. **Start the Application**
   ```bash
   python3 demonx_complete.py
   ```

2. **Enter Bot Token**
   - Get your bot token from [Discord Developer Portal](https://discord.com/developers/applications)
   - Navigate to: Your Application → Bot → Reset Token
   - Copy the token and paste when prompted
   - **Security:** Tokens are stored in memory and never logged

3. **Enter Guild ID (Server ID)**
   - Enable Developer Mode in Discord:
     - User Settings → Advanced → Developer Mode
   - Right-click on target server → Copy Server ID
   - Paste the Guild ID when prompted

4. **Verify Permissions**
   - Bot must have Administrator role in target server
   - Enable "Server Members Intent" in Discord Developer Portal:
     - Your Application → Bot → Privileged Gateway Intents → Server Members Intent

5. **Select Operation**
   - Choose from numbered menu (01-39)
   - Follow on-screen prompts for operation-specific parameters

### Available Operations

The CLI version supports all 39 operations:

**Member Management (9 operations):**
- `[01]` Ban All Members
- `[03]` Kick All Members
- `[04]` Prune Members
- `[14]` Unban All
- `[15]` Unban Member
- `[16]` Mass Nickname
- `[17]` Grant Admin
- `[18]` Mass Assign Role
- `[19]` Remove Role

**Channel Management (7 operations):**
- `[02]` Delete Channels
- `[05]` Create Channels
- `[06]` Mass Ping
- `[10]` Create Categories
- `[11]` Rename Channels
- `[13]` Shuffle Channels
- `[31]` Delete Categories

**Role Management (4 operations):**
- `[07]` Create Roles
- `[08]` Delete Roles
- `[12]` Rename Roles
- `[21]` Copy Role Permissions

**Guild Management (6 operations):**
- `[22]` Rename Guild
- `[23]` Modify Verification Level
- `[24]` Change AFK Timeout
- `[25]` Delete Invites
- `[26]` Create Invites
- `[27]` Get Invites

**Advanced Features (4 operations):**
- `[09]` Delete Emojis
- `[28]` Webhook Spam
- `[29]` Auto React
- `[30]` React to Pinned

**System Features:**
- `[32]` Execute Preset
- `[33]` Create Preset
- `[34]` List Presets
- `[35]` Statistics
- `[36]` History
- `[37]` Queue Operations
- `[38]` View Queue
- `[39]` Clear Queue
- `[00]` or `[20]` Exit

### Example Usage

#### Example 1: Ban All Members
```
Select: [01] BAN MEMBERS
Enter reason (optional): Nuked
Result: All members (except bot) will be banned
```

#### Example 2: Create Channels
```
Select: [05] CREATE CHANNELS
Enter count: 50
Enter name (optional): nuked-channel
Result: 50 new channels created
```

#### Example 3: Execute Preset
```
Select: [32] EXECUTE PRESET
Enter preset name: my_preset
Result: All operations in preset executed sequentially
```

---

## 🔧 Advanced Features

### Operation Queue System

Queue operations for background execution:

1. Select `[37] QUEUE OPS` from main menu
2. Choose operation type to queue
3. Set priority level (LOW, NORMAL, HIGH, CRITICAL)
4. Operation added to queue

**View Queue:** `[38] VIEW QUEUE`
**Clear Queue:** `[39] CLEAR QUEUE`

### Preset System

Create custom operation sequences:

1. Select `[33] CREATE PRESET`
2. Enter preset name
3. Select operations to include
4. Configure parameters
5. Preset saved to `presets.json`

**Execute Preset:** `[32] EXECUTE PRESET`

### Statistics & History

- **View Statistics:** `[35] STATISTICS` - Real-time operation metrics
- **View History:** `[36] HISTORY` - Complete operation history

---

## 🐛 Troubleshooting

### Issue: "No such file or directory" when navigating

**Problem:** `cd ~/storage/shared/DemonX-Nuker-main` fails with "No such file or directory"

**Solutions:**

**1. Check if storage is set up:**
```bash
# Setup storage access (if not done)
termux-setup-storage

# Verify storage link exists
ls -la ~/storage/shared
```

**2. Find where the project actually is:**
```bash
# Search in storage directory
cd ~/storage/shared
find . -name "DemonX-Nuker-main" -type d 2>/dev/null

# Or search for setup script
find . -name "setup_termux.sh" 2>/dev/null

# List all directories to see what's available
ls -la
```

**3. Check common locations:**
```bash
# Check Downloads
ls ~/storage/shared/Download

# Check Documents
ls ~/storage/shared/Documents

# Check root of shared storage
ls ~/storage/shared/
```

**4. Copy project to Termux home (Easiest):**
```bash
# Find the project first
cd ~/storage/shared
find . -name "DemonX-Nuker-main" -type d 2>/dev/null

# Copy to home (replace /path/to/ with actual path from find command)
cp -r ./path/to/DemonX-Nuker-main ~/

# Navigate to it
cd ~/DemonX-Nuker-main
pwd  # Verify you're in the right place
ls   # List files to confirm
```

**5. If project doesn't exist, download/clone it:**
```bash
# Option 1: Clone from GitHub (if you have URL)
cd ~
git clone <repository-url>
cd DemonX-Nuker-main

# Option 2: Download ZIP and extract
# Use a file manager to download ZIP, then:
cd ~/storage/shared/Download
unzip DemonX-Nuker-main.zip
cd DemonX-Nuker-main
```

**6. Verify you're in the right directory:**
```bash
# Check current directory
pwd

# List files (should see setup_termux.sh, demonx_complete.py, etc.)
ls -la

# Verify key files exist
ls setup_termux.sh demonx_complete.py requirements.txt
```

### Issue: "Invalid bot token"

**Solutions:**
- Verify token from Discord Developer Portal
- Ensure token copied completely (no extra spaces)
- Check token hasn't been regenerated
- Verify bot is enabled in Developer Portal

### Issue: "Guild not found"

**Solutions:**
- Verify bot is in target server
- Check Guild ID is correct (enable Developer Mode)
- Ensure bot hasn't been removed from server
- Verify Guild ID format (numeric only)

### Issue: "Insufficient Permissions"

**Solutions:**
- Grant Administrator permission to bot
- Check bot role hierarchy (must be above target roles)
- Enable "Server Members Intent" in Discord Developer Portal
- Verify bot has necessary permissions

### Issue: "Module not found" errors

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or reinstall specific package
pip install --force-reinstall discord.py aiohttp colorama

# Verify Python version
python3 --version  # Should be 3.8+
```

### Issue: Application stops when Termux is closed

**Solution:** Use tmux for background execution (see Method 2 above)

### Issue: "Permission denied" when running script

**Solution:**
```bash
chmod +x setup_termux.sh
bash setup_termux.sh
```

### Issue: Dependencies fail to install

**Solutions:**
```bash
# Update pip first
pip install --upgrade pip

# Try installing with --user flag
pip install --user -r requirements.txt

# Or install packages individually
pip install discord.py
pip install aiohttp
pip install colorama
```

### View Logs

Check application logs for detailed error information:

```bash
# View full log
cat demonx.log

# View last 50 lines
tail -n 50 demonx.log

# Follow log in real-time
tail -f demonx.log
```

---

## 📁 File Structure on Termux

After setup, your project structure should look like:

```
~/storage/shared/DemonX-Nuker-main/
├── demonx_complete.py          # Main CLI application (USE THIS)
├── demonx_gui.py               # GUI (DOESN'T WORK on Termux)
├── setup_termux.sh             # Setup script
├── requirements.txt            # Python dependencies
├── config.json                 # Configuration file
├── proxies.txt                 # Proxy list (optional)
├── presets.json                # Operation presets (auto-generated)
├── operation_queue.json        # Operation queue (auto-generated)
├── operation_history.json      # Operation history (auto-generated)
├── demonx.log                  # Application logs
└── demonx/                     # Package directory
    ├── __init__.py
    ├── config.py
    ├── rate_limiter.py
    ├── proxy_manager.py
    ├── history.py
    ├── presets.py
    ├── utils.py
    ├── operation_queue.py
    └── ...
```

---

## 🔐 Security Best Practices

1. **Never Share Your Bot Token**
   - Tokens are stored in memory only
   - Never commit tokens to version control
   - Regenerate token if compromised

2. **Use Dry Run Mode for Testing**
   ```json
   {
     "dry_run": true
   }
   ```
   This logs operations without executing them.

3. **Test in Private Server First**
   - Always test operations in a test server
   - Verify bot permissions before use
   - Start with small batch sizes

4. **Monitor Rate Limits**
   - Application handles rate limits automatically
   - Watch for rate limit warnings in logs
   - Use reasonable batch sizes

---

## 📊 Performance Tips

1. **Use tmux for Background Execution**
   - Keeps application running when Termux is closed
   - Allows you to detach and reattach sessions

2. **Monitor System Resources**
   ```bash
   # Check memory usage
   free -h

   # Check CPU usage
   top
   ```

3. **Use Operation Queue**
   - Queue multiple operations
   - Set priorities for important operations
   - Execute in background

4. **Enable Verbose Mode for Debugging**
   ```json
   {
     "verbose": true
   }
   ```

---

## 🆘 Getting Help

### Check Logs First
```bash
tail -n 100 demonx.log
```

### Verify Configuration
```bash
cat config.json
```

### Test Dependencies
```bash
python3 -c "import discord; import aiohttp; import colorama; print('OK')"
```

### Reinstall if Needed
```bash
pip install --force-reinstall -r requirements.txt
```

---

## ✅ Quick Reference

### Essential Commands

```bash
# Setup
bash setup_termux.sh

# Run application
python3 demonx_complete.py

# Run in background (tmux)
tmux
python3 demonx_complete.py
# Detach: Ctrl+B, then D
# Reattach: tmux attach

# Check logs
tail -f demonx.log

# View config
cat config.json

# Edit config
nano config.json
```

### File Locations

| File | Purpose | Location |
|------|---------|----------|
| `config.json` | Main configuration | Project root |
| `proxies.txt` | Proxy list | Project root |
| `presets.json` | Operation presets | Auto-generated |
| `operation_queue.json` | Operation queue | Auto-generated |
| `operation_history.json` | Operation history | Auto-generated |
| `demonx.log` | Application logs | Project root |

---

## 🎯 Summary

**Quick Start Checklist:**

1. ✅ Install Termux from F-Droid
2. ✅ Run `termux-setup-storage`
3. ✅ Update packages: `pkg update && pkg upgrade`
4. ✅ Install Python: `pkg install python python-pip git`
5. ✅ Navigate to project: `cd ~/storage/shared/DemonX-Nuker-main`
6. ✅ Run setup: `bash setup_termux.sh`
7. ✅ Configure: Edit `config.json` if needed
8. ✅ Run: `python3 demonx_complete.py`
9. ✅ Use tmux for background: `tmux` then run application

**Remember:**
- ✅ Use CLI version (`demonx_complete.py`)
- ❌ GUI version doesn't work on Termux
- ✅ Use tmux for background execution
- ✅ Test in private server first
- ✅ Enable "Server Members Intent" in Discord Developer Portal

---

**For more information, see the main README.md file.**

---

*Last Updated: Based on DemonX Nuker v2.3*

