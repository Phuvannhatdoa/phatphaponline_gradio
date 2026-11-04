"""process_alive.py — kiểm tra "tiến trình còn sống" an toàn trên Windows.

Vì sao KHÔNG dùng ``os.kill(pid, 0)`` để dò?

  Trên Windows, CPython cài ``os.kill`` bằng ``OpenProcess`` +
  ``TerminateProcess`` (Modules/posixmodule.c, ``os_kill_impl``): mọi giá trị
  ``sig`` khác ``CTRL_C_EVENT`` / ``CTRL_BREAK_EVENT`` đều bị coi là **mã
  thoát** và kết thúc tiến trình đích. Nghĩa là ``os.kill(pid, 0)`` không phải
  phép "thử tồn tại" như trên POSIX — nó vừa có thể giết nhầm, vừa không đáng
  tin cậy.

  Đo thật trên máy Windows / Python 3.14.3 (2026-11-04) với job T50 đang sống
  (PID 22708, tiến trình con của app.py cũ):

      >>> os.kill(22708, 0)
      OSError: [WinError 87] The parameter is incorrect

  ⇒ hàm ``_t50_pid_alive`` cũ trong app.py trả về False cho một tiến trình
  đang sống, khiến dashboard ghi ``running=False`` và bỏ quên job (job vẫn
  dịch tiếp trong nền). Cùng lúc, nếu OpenProcess thành công thì
  ``TerminateProcess(handle, 0)`` lại là lệnh **giết** tiến trình.

  Vì vậy ở đây dùng ``OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)`` +
  ``GetExitCodeProcess``: chỉ cần quyền ĐỌC, không bao giờ có quyền
  ``PROCESS_TERMINATE`` nên không thể vô tình dừng job. Trên POSIX giữ nguyên
  ``os.kill(pid, 0)`` (ở đó nó đúng là phép dò tồn tại).

Cách dùng::

    from process_alive import pid_alive
    if pid_alive(1234):
        ...
"""

import os
import sys

__all__ = ['pid_alive']

_STILL_ACTIVE = 259
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _pid_alive_windows(pid):
    """Windows: OpenProcess(query) + GetExitCodeProcess == STILL_ACTIVE.

    Trả False khi: pid không tồn tại, không mở được handle (thiếu quyền),
    hoặc tiến trình đã thoát. Không bao giờ gọi TerminateProcess.
    """
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = kernel32.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION, False, wintypes.DWORD(pid))
    if not handle:
        # Không tồn tại (ERROR_INVALID_PARAMETER) hoặc không đủ quyền đọc.
        return False
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def pid_alive(pid):
    """True nếu ``pid`` đang là một tiến trình còn sống.

    Chấp nhận int hoặc chuỗi số (status file có thể lưu chuỗi); mọi giá trị
    rỗng / không hợp lệ / <= 0 đều trả False thay vì ném exception.
    """
    if pid is None or pid == '':
        return False
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False

    if sys.platform == 'win32':
        try:
            return _pid_alive_windows(pid)
        except Exception:
            # Thiếu ctypes/kernel32 (rất hiếm) → không dám khẳng định còn sống.
            return False

    try:
        os.kill(pid, 0)          # POSIX: đây đúng là phép dò tồn tại
        return True
    except OSError:
        return False
