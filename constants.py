import os, sys

__version__ = "1.0.0"
SERVER_UPDATE_URL = "http://127.0.0.1:5000/uploads/xtimer_update.zip"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.modules['__main__'].__file__)
else:
    BASE_DIR = os.path.dirname(__file__)

ICONS_DIR   = os.path.join(BASE_DIR, "icons")
SOUNDS_DIR  = os.path.join(BASE_DIR, "sounds")
PLUGINS_DIR = os.path.join(BASE_DIR, "platforms")

TRAY_ICON     = os.path.join(ICONS_DIR, "tray_icon.ico")
SETTINGS_ICON = os.path.join(ICONS_DIR, "settings_icon.png")
