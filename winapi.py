"""
Небольшая обёртка для часто-используемых вызовов WinAPI
(позиционирование, размеры экрана, окно «поверх всех», прямоугольник
и позиция taskbar’a).
"""
import ctypes
from ctypes import wintypes
from logging_config import log_exceptions

# ──────────────────────────────────────────────────────────────
#  базовые константы и функции
# ──────────────────────────────────────────────────────────────
USER32, SHELL32 = ctypes.windll.user32, ctypes.windll.shell32

HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOMOVE       = 0x0002
SWP_NOSIZE       = 0x0001
SWP_NOACTIVATE   = 0x0010
HWND_NOTOPMOST = -2
# wrap Get/Set helpers ---------------------------------------------------------
SetWindowPos = USER32.SetWindowPos
SetWindowPos.argtypes = (
    wintypes.HWND, wintypes.HWND,
    ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int,
    ctypes.c_uint,
)
SetWindowPos.restype = wintypes.BOOL

GetSM   = USER32.GetSystemMetrics      # ширина/высота экрана
GetFG   = USER32.GetForegroundWindow   # foreground-window HWND
GetRect = USER32.GetWindowRect         # HWND → RECT

GetSystemMetrics = USER32.GetSystemMetrics
GetSystemMetrics.argtypes = (ctypes.c_int,)
GetSystemMetrics.restype  = ctypes.c_int

SM_CXSCREEN, SM_CYSCREEN = 0, 1        # индексы метрик

# ──────────────────────────────────────────────────────────────
#  структуры и util-функции
# ──────────────────────────────────────────────────────────────
class RECT(ctypes.Structure):
    _fields_ = [
        ("left",   ctypes.c_long),
        ("top",    ctypes.c_long),
        ("right",  ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize",           ctypes.c_uint),
        ("hWnd",             wintypes.HWND),
        ("uCallbackMessage", ctypes.c_uint),
        ("uEdge",            ctypes.c_uint),
        ("rc",               RECT),
        ("lParam",           ctypes.c_int),
    ]

ABM_GETTASKBARPOS = 0x00000005

@log_exceptions
def taskbar_rect_edge():
    """
    Возвращает кортеж (RECT, edge), где edge ∈ {0=left,1=top,2=right,3=bottom}.
    """
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(abd)
    SHELL32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(abd))
    return abd.rc, abd.uEdge
