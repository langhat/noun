import ctypes
from ctypes import wintypes

def show_notification(title, message, duration=5000):
    """在Windows右下角显示弹出通知（兼容Windows 7+）"""
    # 完整的NOTIFYICONDATA结构体定义（兼容Windows Vista及以上）
    class NOTIFYICONDATA(ctypes.Structure):
        _fields_ = [
            ('cbSize', wintypes.DWORD),
            ('hWnd', wintypes.HWND),
            ('uID', wintypes.UINT),
            ('uFlags', wintypes.UINT),
            ('uCallbackMessage', wintypes.UINT),
            ('hIcon', wintypes.HICON),
            ('szTip', wintypes.WCHAR * 128),
            ('dwState', wintypes.DWORD),
            ('dwStateMask', wintypes.DWORD),
            ('szInfo', wintypes.WCHAR * 256),
            ('uTimeoutOrVersion', wintypes.UINT),
            ('szInfoTitle', wintypes.WCHAR * 64),
            ('dwInfoFlags', wintypes.DWORD),
            ('guidItem', wintypes.GUID),  # Windows Vista+ 必需
            ('hBalloonIcon', wintypes.HICON)  # Windows Vista+ 必需
        ]

    # Windows API常量
    NIM_ADD = 0x00000000
    NIM_MODIFY = 0x00000001
    NIM_DELETE = 0x00000002
    NIF_INFO = 0x00000010
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000001
    NIIF_INFO = 0x00000001  # 信息图标

    # 加载系统库
    shell32 = ctypes.WinDLL('shell32.dll', use_last_error=True)
    user32 = ctypes.WinDLL('user32.dll', use_last_error=True)

    # 初始化结构体
    nid = NOTIFYICONDATA()
    nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)  # 自动计算结构体大小（关键！）
    nid.hWnd = None
    nid.uID = 100  # 唯一ID，用于后续删除通知
    nid.uFlags = NIF_ICON | NIF_TIP | NIF_INFO  # 启用图标、提示和气泡信息

    # 设置图标（使用系统信息图标）
    nid.hIcon = user32.LoadIconW(None, 32516)  # IDI_INFORMATION（信息图标）
    if not nid.hIcon:
        nid.hIcon = user32.LoadIconW(None, 32512)  # 备用：IDI_APPLICATION

    # 通知内容
    nid.szTip = "AI助手通知"  # 托盘悬停提示
    nid.szInfoTitle = title[:63]  # 限制标题长度（64字符）
    nid.szInfo = message[:255]    # 限制内容长度（256字符）
    nid.uTimeoutOrVersion = 0x00040000 | duration  # 高字节为版本，低字节为超时
    nid.dwInfoFlags = NIIF_INFO  # 显示信息类图标

    try:
        # 添加通知
        success = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        if not success:
            raise ctypes.WinError(ctypes.get_last_error())
        
        # 延迟后删除通知（避免托盘残留图标）
        import threading
        def delete_notification():
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            if nid.hIcon:
                user32.DestroyIcon(nid.hIcon)  # 释放图标资源
        
        threading.Timer(duration / 1000 + 1, delete_notification).start()
        return True
    except Exception as e:
        print(f"通知显示失败: {e}")
        # 清理资源
        if nid.hIcon:
            user32.DestroyIcon(nid.hIcon)
        return False