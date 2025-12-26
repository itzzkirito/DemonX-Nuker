# Termux Quick Start Guide

## 🚀 Quick Setup (Copy & Paste)

```bash
# 1. Update Termux
pkg update && pkg upgrade

# 2. Install Python
pkg install python python-pip git

# 3. Navigate to project directory
cd ~/DemonX-Nuker-main

# 4. Run setup script (if available)
chmod +x setup_termux.sh
./setup_termux.sh

# OR manually install dependencies:
pip install -r requirements.txt

# 5. Run DemonX
python3 demonx_complete.py
```

---

## ⚡ One-Liner Setup

```bash
pkg update && pkg upgrade && pkg install python python-pip git && cd ~/DemonX-Nuker-main && pip install -r requirements.txt && python3 demonx_complete.py
```

---

## ✅ Compatibility Checklist

| Component | Status | Notes |
|-----------|--------|-------|
| CLI Version | ✅ Works | Use `demonx_complete.py` |
| GUI Version | ❌ No | Tkinter not available |
| Discord.py | ✅ Works | Fully compatible |
| Colors | ⚠️ Limited | Functional but may look different |
| Rust Components | ⚠️ Optional | Python fallback works |
| All Features | ✅ Works | Everything except GUI |

---

## 📝 Important Notes

1. **Use CLI version only:** `python3 demonx_complete.py`
2. **GUI won't work:** Don't use `demonx_gui.py`
3. **No code changes needed:** Already cross-platform compatible
4. **Rust is optional:** Python fallback works automatically

---

## 🔧 Troubleshooting

**Problem:** `Module not found`
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Problem:** Want background execution
```bash
pkg install tmux
tmux
# Run your script, then Ctrl+B, D to detach
```

**Problem:** Colors not working
- This is cosmetic only, functionality is unaffected

---

## 📚 Full Documentation

See `TERMUX_GUIDE.md` for detailed analysis and information.

