import os

# 核心修改：强制让 requests 和 websocket 忽略全局代理访问本地地址
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = '127.0.0.1,localhost'

import requests
import websocket
import json
import time
import subprocess
import os
import sys
import platform
import random
import concurrent.futures


def get_work_area():
    os_name = platform.system()

    if os_name == "Windows":
        return _get_windows_work_area()
    elif os_name == "Darwin":  # macOS
        return _get_mac_work_area()
    elif os_name == "Linux":
        return _get_linux_work_area()
    else:
        raise NotImplementedError(f"不支持的操作系统: {os_name}")


def _get_windows_work_area():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    rect = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.right - rect.left, rect.bottom - rect.top


def _get_mac_work_area():
    """获取 macOS 的工作区大小（排除 Dock 和菜单栏）"""
    try:
        # 方法1：使用 AppKit（推荐）
        from AppKit import NSScreen

        main_screen = NSScreen.mainScreen()
        visible_frame = main_screen.visibleFrame()

        width = int(visible_frame.size.width)
        height = int(visible_frame.size.height)

        return width, height

    except ImportError:
        # 方法2：使用 pyobjc
        try:
            import Foundation
            from AppKit import NSScreen

            main_screen = NSScreen.mainScreen()
            visible_frame = main_screen.visibleFrame()

            width = int(visible_frame.size.width)
            height = int(visible_frame.size.height)

            return width, height

        except ImportError:
            # 方法3：使用 tkinter（不需要额外安装）
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口

                # 获取屏幕可用大小
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()

                return width, height
            except:
                # 方法4：最后的方法，使用系统命令
                import subprocess
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType", "-json"],
                    capture_output=True,
                    text=True
                )
                # 解析输出获取屏幕信息
                # 这里需要根据实际输出格式解析
                return 1920, 1080  # 默认值


def _get_linux_work_area():
    """获取 Linux 的工作区大小"""
    try:
        # 尝试使用 tkinter
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except:
        # 尝试使用 xrandr
        import subprocess
        try:
            output = subprocess.check_output(
                ["xrandr"], stderr=subprocess.DEVNULL
            ).decode()
            # 解析 xrandr 输出
            for line in output.split('\n'):
                if ' connected' in line and '*' in line:
                    # 查找分辨率
                    import re
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        return int(match.group(1)), int(match.group(2))
        except:
            pass
        return 1920, 1080  # 默认值


# ===== 2. 增强版 RuyiInstance 类 =====
class RuyiInstance:
    def __init__(self, index, port, proxy_port, user_data_base, chrome_path, fp_path):
        self.index = index
        self.port = port
        self.proxy_port = proxy_port  # 新增：代理端口
        self.id_counter = 0
        self.ws = None
        self.target_id = None
        self.user_data_path = f"{user_data_base}_{index}"
        self.chrome_path = chrome_path
        self.fp_path = fp_path

    def launch(self):
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)
        cmd = [
            self.chrome_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_path}",
            f"--proxy-server=socks5://127.0.0.1:{self.proxy_port}",  # 核心修改：连接本地中转代理
            "--remote-allow-origins=*",
            "--no-sandbox",
            f"--ruyi={{\"ruyiFile\":\"{self.fp_path}\"}}",
            "--enable-automation",
            "--disable-session-crashed-bubble",
            "--no-first-run",  # 跳过首次运行向导
            "about:blank"
        ]
        return subprocess.Popen(cmd)

    def send_cdp(self, method, params=None):
        current_id = self.id_counter
        self.ws.send(json.dumps({'id': current_id, 'method': method, 'params': params or {}}))
        self.id_counter += 1
        while True:
            response = json.loads(self.ws.recv())
            if response.get('id') == current_id:
                return response
            elif response.get("method") == "Runtime.bindingCalled":
                print(f'[Win {self.index}] bindingCalled:', response)
            else:
                pass  # 过滤掉不相关的事件

    def connect(self):
        for _ in range(15):
            try:
                res = requests.get(f"http://127.0.0.1:{self.port}/json").json()
                # 寻找空白页或已加载的页面
                page = next((p for p in res if p.get('type') == 'page'), None)
                if page:
                    self.ws = websocket.create_connection(page['webSocketDebuggerUrl'])
                    self.target_id = page['id']
                    return True
            except:
                time.sleep(1)
        return False

    def set_bounds(self, x, y, w, h):
        res = self.send_cdp('Browser.getWindowForTarget', {'targetId': self.target_id})
        win_id = res['result']['windowId']
        return self.send_cdp('Browser.setWindowBounds', {
            'windowId': win_id,
            'bounds': {'left': int(x), 'top': int(y), 'width': int(w), 'height': int(h), 'windowState': 'normal'}
        })

    def rt_enable(self):
        return self.send_cdp("Runtime.enable")

    def rt_compileScript(self, expression, source_url, persist_script=True):
        return self.send_cdp("Runtime.compileScript", {
            "expression": expression, "sourceURL": source_url, "persistScript": persist_script
        })

    def rt_runScript(self, script_id):
        return self.send_cdp("Runtime.runScript", {"scriptId": script_id})


# ===== 3. 主流程执行 =====

# 配置路径 (请检查是否与你的环境一致)
CHROME_BIN = r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DATA_DIR = r"/Volumes/SSD-SAMSUNG/demo/chromium/testCDP"
FP_PATH = r"E:\pycode\ruyicdp\fp.txt"

# 布局：2x2, 共 4 个窗口
COLS, ROWS, NUM_INSTANCES = 2, 2, 4
LOCAL_PROXY_START = 10005  # 对应代理脚本的起始端口

WORK_WIDTH, WORK_HEIGHT = get_work_area()
instances = []

# 1. 启动所有实例
for i in range(NUM_INSTANCES):
    # 为每个窗口分配 调试端口(9222+i) 和 代理端口(10001+i)
    inst = RuyiInstance(i, 9222 + i, LOCAL_PROXY_START + i, DATA_DIR, CHROME_BIN, FP_PATH)
    inst.launch()
    instances.append(inst)

print(f"正在启动 {NUM_INSTANCES} 个窗口，请稍候...")
time.sleep(5)

win_w, win_h = WORK_WIDTH / COLS, WORK_HEIGHT / ROWS

# 2. 连接并操作
for i, inst in enumerate(instances):
    print(f"尝试连接窗口 {i} (端口 {inst.port}, 代理 {inst.proxy_port})...")
    if inst.connect():
        # 自动布局
        inst.set_bounds((i % COLS) * win_w, (i // COLS) * win_h, win_w, win_h)

        # 开启 Runtime
        inst.rt_enable()

        # 跳转到检测网站验证 IP
        inst.send_cdp('Page.navigate', {'url': 'https://www.browserscan.net/zh'})
        time.sleep(3)
        inst.send_cdp('Page.reload')


        print(f"✅ 窗口 {i} 已连接")

        # 执行你的自定义 JS 逻辑
        code = """
        console.log("Proxy Port: " + window.location.origin);
        """
        try:
            compiled = inst.rt_compileScript(code, "test_script.js")
            inst.rt_runScript(compiled["result"]["scriptId"])
        except:
            pass
    else:
        print(f"❌ 窗口 {i} 连接调试端口失败")

print("\n所有操作已完成，请检查浏览器窗口。")