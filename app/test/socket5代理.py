import os
import re

# 核心修改：强制让 requests 和 websocket 忽略全局代理访问本地地址
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = '127.0.0.1,localhost'

import shutil
import requests
import websocket
import json
import time
import subprocess
import os
import ctypes
from ctypes import wintypes


# ===== 1. 获取屏幕区域工具 =====
import sys
import platform
import random
import concurrent.futures
import threading

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
def parse_ua_to_fingerprint(ua_raw):
    """解析 raw User-Agent 字符串为完整指纹配置"""
    # 清理注释和空白
    ua = ua_raw.split('#')[0].strip()
    if not ua: return None
    
    # 默认值
    platform = "Windows"
    platform_version = "10.0.0"
    model = ""
    mobile = False
    browser_brand = "Google Chrome"
    browser_version = "123.0.0.0"
    major_version = "123"
    architecture = "x86"
    bitness = "64"
    
    # 1. 识别平台与设备
    if "Windows" in ua:
        platform = "Windows"
        architecture = "x86"
        if "Windows NT 10.0" in ua: platform_version = "10.0.0"
        elif "Windows NT 11.0" in ua: platform_version = "15.0.0"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        platform = "macOS"
        architecture = "x86"
        match = re.search(r'Mac OS X ([\d_]+)', ua)
        if match: platform_version = match.group(1).replace('_', '.')
    elif "Android" in ua:
        platform = "Android"
        architecture = "arm"
        mobile = True
        match = re.search(r'Android ([\d.]+)', ua)
        if match: platform_version = match.group(1)
        # 提取型号: Android X; [Model] Build/
        model_match = re.search(r'Android [\d.]+;\s*([^;)]+)(?:Build|;|\))', ua)
        if model_match: model = model_match.group(1).strip()
    elif "iPhone" in ua or "iPad" in ua:
        platform = "iOS"
        architecture = "arm"
        mobile = True
        if "iPad" in ua: model = "iPad"
        else: model = "iPhone"
        match = re.search(r'OS ([\d_]+)', ua)
        if match: platform_version = match.group(1).replace('_', '.')
    elif "Linux" in ua: # Fallback for generic Linux
        platform = "Linux"
        architecture = "x86"

    # 2. 识别浏览器版本
    if "CriOS" in ua: # Chrome on iOS
        browser_brand = "Google Chrome"
        match = re.search(r'CriOS/([\d.]+)', ua)
        if match: 
            browser_version = match.group(1)
            major_version = browser_version.split('.')[0]
    elif "Chrome" in ua:
        browser_brand = "Google Chrome"
        match = re.search(r'Chrome/([\d.]+)', ua)
        if match:
            browser_version = match.group(1)
            major_version = browser_version.split('.')[0]
    
    # 3. 构建 Metadata
    ua_metadata = {
        "brands": [
            {"brand": browser_brand, "version": major_version},
            {"brand": "Chromium", "version": major_version},
            {"brand": "Not?A_Brand", "version": "24"}
        ],
        "fullVersionList": [
            {"brand": browser_brand, "version": browser_version},
            {"brand": "Chromium", "version": browser_version},
            {"brand": "Not?A_Brand", "version": "24.0.0.0"}
        ],
        "fullVersion": browser_version,
        "platform": platform,
        "platformVersion": platform_version,
        "architecture": architecture,
        "model": model,
        "mobile": mobile,
        "bitness": bitness,
        "wow64": False
    }
    
    # 4. 构建 Headers
    sec_ch_ua = f'"{browser_brand}";v="{major_version}", "Chromium";v="{major_version}", "Not?A_Brand";v="24"'
    
    headers = {
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?1" if mobile else "?0",
        "sec-ch-ua-platform": f'"{platform}"',
        "Upgrade-Insecure-Requests": "1"
    }
    
    if model:
        headers["sec-ch-ua-model"] = f'"{model}"'
    if platform_version:
        headers["sec-ch-ua-platform-version"] = f'"{platform_version}"'

    # 5. 平台特定 JS 和 仿真参数
    platform_js = "Win32"
    mobile_emulation = None
    
    if platform == "macOS": platform_js = "MacIntel"
    elif platform == "Android": 
        platform_js = "Linux armv81"
        mobile_emulation = {
             "width": 380, "height": 800, "deviceScaleFactor": 3, "mobile": True,
             "screenOrientation": {"type": "portraitPrimary", "angle": 0}
        }
    elif platform == "iOS": 
        platform_js = "iPhone"
        mobile_emulation = {
             "width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True,
             "screenOrientation": {"type": "portraitPrimary", "angle": 0}
        }
    elif platform == "Linux":
        platform_js = "Linux x86_64"
        
    return {
        "name": f"{platform} {platform_version} ({model or 'PC'})",
        "userAgent": ua,
        "uaMetadata": ua_metadata,
        "headers": headers,
        "platform_js": platform_js,
        "mobile_emulation": mobile_emulation
    }

def get_random_fingerprint():
    """从 UA.txt 读取并生成随机指纹"""
    ua_file_path = r"/Volumes/SSD-SAMSUNG/code/project/mxy-python/app/test/UA.txt"
    
    fingerprints = []
    
    if os.path.exists(ua_file_path):
        try:
            with open(ua_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    fp = parse_ua_to_fingerprint(line)
                    if fp:
                        fingerprints.append(fp)
        except Exception as e:
            print(f"读取 UA.txt 失败: {e}")
            
    # 如果读取失败或文件为空，使用默认兜底指纹
    if not fingerprints:
        print("⚠️ 未找到有效 UA，使用默认兜底指纹")
        fingerprints = [
            parse_ua_to_fingerprint("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        ]
        
    return random.choice(fingerprints)

class RuyiInstance:
    def __init__(self, index, port, proxy_port, user_data_base, chrome_path, fp_path):
        self.index = index
        self.port = port
        self.proxy_port = proxy_port
        self.id_counter = 0
        self.ws = None
        self.target_id = None
        self.user_data_path = f"{user_data_base}_{index}"
        self.chrome_path = chrome_path
        self.fp_path = fp_path
        self.current_ua = None
        
        # API 状态追踪
        self.media_playing = False
        self.media_loading = False
        self.last_media_event = 0
        self.process = None
        self.running = False

    def launch(self):
        # 重置状态
        self.running = True
        self.media_playing = False
        self.media_loading = False
        self.last_media_event = 0
        
        # 每次启动前清理用户数据，确保指纹（Cookies/Storage）隔离
        if os.path.exists(self.user_data_path):
            try:
                shutil.rmtree(self.user_data_path, ignore_errors=True)
            except:
                pass
                
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)
            
        # 每次启动使用随机 User-Agent
        self.current_ua = get_random_fingerprint()
        print(f"[Win {self.index}] 使用指纹: {self.current_ua['name']}")
        
        cmd = [
            self.chrome_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_path}",
            f"--proxy-server=socks5://127.0.0.1:{self.proxy_port}",
            f"--user-agent={self.current_ua['userAgent']}",
            "--remote-allow-origins=*",
            "--no-sandbox",
            "--test-type", # 屏蔽"您使用的是不受支持的命令行标记"提示
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--no-first-run",
            "--disable-web-security",
            "--headless=new",  # ✅ 无头
            "--mute-audio",  # 🔇 关闭声音
            "--disable-site-isolation-trials",
            "about:blank"
        ]
        self.process = subprocess.Popen(cmd)
        return self.process

    def close(self):
        """关闭浏览器进程和连接"""
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None

    def _handle_msg(self, response):
        """处理异步事件 (Media, DOM, etc)"""
        method = response.get('method', '')
        params = response.get('params', {})
        
        if method == "Media.playerEventsAdded":
            events = params.get('events', [])
            for e in events:
                value = str(e.get('value', '')).lower()
                
                # 状态检测: 加载中
                if 'waiting' in value or 'stalled' in value or 'loadstart' in value:
                    self.media_loading = True
                    print(f" [Win {self.index}] API捕获事件: LOADING ({value})")
                
                # 状态检测: 播放中
                if 'playing' in value or 'play' in value:
                    # 严防误判: 过滤掉 create, request, ready 等非播放状态
                    if not any(x in value for x in ['request', 'created', 'construct', 'ready']): 
                        self.media_playing = True
                        self.media_loading = False
                        self.last_media_event = time.time()
                        print(f" [Win {self.index}] API捕获事件: PLAYING ({value})")
                elif 'pause' in value or 'ended' in value or 'suspend' in value:
                    self.media_playing = False
                    self.last_media_event = time.time()
                    print(f"[Win {self.index}] 进入 CDP 自动化控制循环 (超时: 90s)...")
                elif 'canplay' in value:
                    self.media_loading = False

        elif method == "Media.playerPropertiesChanged":
            props = params.get('properties', [])
            for p in props:
                # 某些浏览器版本通过属性传递状态
                if p.get('name') == 'kMediaIsPlaying':
                    self.media_playing = bool(p.get('value'))
                    
        elif method == "Network.requestWillBeSent":
            # 打印主页面的请求头以验证指纹
            if params.get('type') == 'Document':
                req = params.get('request', {})
                print(f"\n[Win {self.index}] 🌍 主文档请求: {req.get('url')}")
                # 格式化打印 Headers
                headers = req.get('headers', {})
                print(f"[Win {self.index}] 📋 Request Headers:")
                for k, v in headers.items():
                    print(f"    {k}: {v}")
                print("-" * 50 + "\n")

    def send_cdp(self, method, params=None):
        current_id = self.id_counter
        self.ws.send(json.dumps({'id': current_id, 'method': method, 'params': params or {}}))
        self.id_counter += 1
        
        start_wait = time.time()
        while True:
            if not self.running:
                return {}
            # 增加超时防止死锁
            if time.time() - start_wait > 10:
                print(f" [Win {self.index}] CDP命令超时: {method}")
                return {}
                
            try:
                response = json.loads(self.ws.recv())
                
                # 优先检查是否是命令响应
                if response.get('id') == current_id:
                    return response
                
                # 处理异步事件
                self._handle_msg(response)
                
            except Exception as e:
                print(f"WebSocket Error: {e}")
                return {}

    def _get_stealth_js(self):
        """生成反检测注入脚本 (根据 UA 适配平台特征)"""
        if not self.current_ua: return ""
        
        platform_val = self.current_ua.get('platform_js', 'Win32')
        is_mobile = self.current_ua.get('uaMetadata', {}).get('mobile', False)
        
        js = f"""
            // 1. 强制覆盖 navigator.webdriver (防止漏网)
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});
            
            // 2. 伪造 navigator.platform 以匹配 UA
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{platform_val}',
            }});
            
            // 3. 移除 Chrome 自动化特征
            if (window.navigator.chrome) {{
                // 某些检测脚本会检查 window.navigator.chrome.runtime
                // 这里保留 chrome 对象但可以做微调
            }}
            
            // 4. 伪造 HardwareConcurrency (防止指纹识别)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => 8,
            }});
            
            // 5. 屏蔽 Automation 相关的权限查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {{
                return parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters);
            }};
        """
        
        if is_mobile:
            js += """
                // 移动端特征补全
                Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 5 });
                
                // 模拟移动端网络信息
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 150,
                        downlink: 10,
                        saveData: false
                    })
                });
            """
            
        return js

    def connect(self):
        for _ in range(15):
            if not self.running:
                return False
            try:
                res = requests.get(f"http://127.0.0.1:{self.port}/json").json()
                page = next((p for p in res if p.get('type') == 'page'), None)
                if page:
                    self.ws = websocket.create_connection(page['webSocketDebuggerUrl'])
                    self.target_id = page['id']
                    
                    # 启用必要的 API 域
                    self.send_cdp("Page.enable")
                    self.send_cdp("DOM.enable")
                    self.send_cdp("Media.enable") # 核心：启用媒体监控 API
                    self.send_cdp("Network.enable") # 核心：启用网络控制 (用于 UserAgentOverride)
                    
                    # 1. 注入反检测脚本 (在页面加载前执行)
                    stealth_js = self._get_stealth_js()
                    self.send_cdp("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
                    
                    # 2. 深度指纹配置 (UA Override & Client Hints)
                    if self.current_ua:
                        # 覆盖 User-Agent 和 Metadata
                        self.send_cdp("Network.setUserAgentOverride", {
                            "userAgent": self.current_ua['userAgent'],
                            "userAgentMetadata": self.current_ua['uaMetadata']
                        })
                        # 设置额外的 HTTP Headers (Client Hints)
                        if self.current_ua.get('headers'):
                            self.send_cdp("Network.setExtraHTTPHeaders", {"headers": self.current_ua['headers']})
                    
                    # 3. 移动端仿真配置 (ViewPort & Touch)
                    mobile_emulation = self.current_ua.get('mobile_emulation')
                    if mobile_emulation:
                        self.send_cdp("Emulation.setDeviceMetricsOverride", mobile_emulation)
                        self.send_cdp("Emulation.setTouchEmulationEnabled", {"enabled": True})
                    
                    return True
            except:
                time.sleep(1)
        return False
    
    def maintain_focus(self):
        """维护窗口焦点并关闭广告 (模拟真人反应)"""
        try:
            # 1. 扫描是否有广告弹窗 (非主窗口的其他 Page)
            res = self.send_cdp("Target.getTargets")
            targets = res.get('result', {}).get('targetInfos', [])
            
            ad_targets = [t for t in targets if t['type'] == 'page' and t['targetId'] != self.target_id]
            
            if ad_targets:
                # 发现广告！模拟真人反应延迟
                print(f"[Win {self.index}] � 检测到 {len(ad_targets)} 个广告弹窗，模拟人工反应...")
                
                # 随机发呆 1.5 - 3 秒 (模拟用户意识到弹了广告)
                time.sleep(random.uniform(1.5, 3.0))
                
                for t in ad_targets:
                    url_snippet = t.get('url', '')[:40]
                    print(f"[Win {self.index}] 🔪 正在关闭广告: {url_snippet}...")
                    
                    # 再次微小延迟，模拟移动鼠标去关闭
                    time.sleep(random.uniform(0.5, 1.0))
                    self.send_cdp("Target.closeTarget", {'targetId': t['targetId']})
                
                # 关闭完广告后，稍作停顿，再聚焦回主窗口
                time.sleep(random.uniform(0.5, 1.0))
                print(f"[Win {self.index}] 🔙 广告已清理，切回主窗口")
                self.send_cdp("Page.bringToFront")
            else:
                # 无广告，确保主窗口在最前
                self.send_cdp("Page.bringToFront")
                    
        except Exception as e:
            pass

    def wait_and_process(self, duration):
        """等待并持续处理事件，同时维护窗口"""
        end = time.time() + duration
        while time.time() < end:
            if not self.running:
                break
            self.maintain_focus()
            # 发送空指令以触发 socket 读取循环 (keep-alive)
            self.send_cdp("DOM.getDocument", {"depth": 0})
            time.sleep(0.5)

    def set_bounds(self, x, y, w, h):
        res = self.send_cdp('Browser.getWindowForTarget', {'targetId': self.target_id})
        win_id = res['result']['windowId']
        return self.send_cdp('Browser.setWindowBounds', {
            'windowId': win_id,
            'bounds': {'left': int(x), 'top': int(y), 'width': int(w), 'height': int(h), 'windowState': 'normal'}
        })

    def check_play_status(self, node_id):
        """主动查询视频状态: PAUSED, BUFFERING, PLAYING"""
        try:
            # 1. 解析 Node
            res = self.send_cdp("DOM.resolveNode", {"nodeId": node_id})
            if 'error' in res or 'object' not in res.get('result', {}):
                return "UNKNOWN"
            
            object_id = res['result']['object']['objectId']
            
            # 2. JS 查询
            js_res = self.send_cdp("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": """
                    function() { 
                        return {
                            readyState: this.readyState,
                            paused: this.paused,
                            currentTime: this.currentTime
                        }; 
                    }
                """,
                "returnByValue": True
            })
            
            # 3. 释放
            self.send_cdp("Runtime.releaseObject", {"objectId": object_id})

            val = js_res.get('result', {}).get('result', {}).get('value', {})
            rs = val.get('readyState', -1)
            paused = val.get('paused', True)
            ct = val.get('currentTime', 0)
            
            print(f"[Win {self.index}] 🔍 状态检查: RS={rs}, Paused={paused}, CT={ct}")
            
            if paused:
                return "PAUSED"
            
            # Paused=False 且 RS < 3 -> 缓冲中
            if rs < 3:
                return "BUFFERING"

            if ct > 0:
                return "PLAYING"
            return "BUFFERING"
            
        except Exception as e:
            print(f"Check error: {e}")
            return "UNKNOWN"

    def find_video_via_api(self):
        """完全使用 CDP API 递归查找 Video 节点"""
        # 获取完整 DOM 树 (depth=-1 无限深度, pierce=True 穿透 iframe/shadow)
        res = self.send_cdp("DOM.getDocument", {"depth": -1, "pierce": True})
        root = res.get('result', {}).get('root')
        
        def recursive_search(node):
            if not node: return None
            
            # 1. 匹配节点名称
            node_name = node.get('nodeName', '').lower()
            if node_name == 'video':
                return node['nodeId']
                
            # 2. 遍历子节点
            children = node.get('children', [])
            for child in children:
                found = recursive_search(child)
                if found: return found
                
            # 3. 遍历 Shadow Roots
            shadows = node.get('shadowRoots', [])
            for shadow in shadows:
                found = recursive_search(shadow)
                if found: return found
                
            # 4. 遍历 Iframe 文档
            if 'contentDocument' in node:
                found = recursive_search(node['contentDocument'])
                if found: return found
                
            return None
            
        return recursive_search(root)


# ===== 3. 自动化与业务逻辑 =====

def simulate_human_move(inst, start_x, start_y, end_x, end_y, steps=25):
    """模拟真人鼠标移动轨迹"""
    for i in range(steps):
        if not inst.running:
            break
        progress = (i + 1) / steps
        t = progress * (2 - progress)
        x = start_x + (end_x - start_x) * t + random.uniform(-2, 2)
        y = start_y + (end_y - start_y) * t + random.uniform(-2, 2)
        inst.send_cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        time.sleep(random.uniform(0.01, 0.03))

def automation_task(inst, win_x, win_y, win_w, win_h, play_duration_range=(60, 70)):
    """单个窗口的自动化任务流程"""
    print(f"🚀 [Win {inst.index}] 开始任务 (API Mode)...")
    
    if not inst.connect():
        print(f"❌ [Win {inst.index}] 连接失败")
        return

    # 1. 布局窗口
    inst.set_bounds(win_x, win_y, win_w, win_h)

    # 2. 访问目标视频页
    # target_url = 'https://abmxy.easyvidplayer.com/#pruqs'
    target_url = 'https://videy.tv/s/yz79sidc'
    # target_url = 'https://vinovo.to/d/5q71nxk3agoj89'
    referrer_url = 'https://blog-five-lime-46.vercel.app/'
    
    # target_url = 'https://mmxxyy.vidplayer.live/#wvrm5'
    # target_url = 'https://up4fun.top/u42bcf4g3hlm.html'
    # target_url = 'https://vinovo.to/d/9qo4rnd2an26w0'
    # target_url = 'https://abstream.to/zogxzwbyj7x1'
    inst.send_cdp('Page.navigate', {'url': target_url, 'referrer': referrer_url})
    print(f"[Win {inst.index}] 正在加载页面 (Referer: {referrer_url})...")
    
    # 等待初始加载
    inst.wait_and_process(5)
    
    print(f"[Win {inst.index}] 进入 API 自动化循环 (等待播放，无超时)...")

    # 循环直到检测到播放
    while not inst.media_playing and inst.running:
        try:
            # --- 0. 窗口维护: 聚焦主页 & 关闭广告 ---
            inst.maintain_focus()

            # --- 1. 使用 Media API 检查状态 ---
            if inst.media_playing:
                break
            
            # --- 2. 使用 DOM API 寻找元素 (No JS) ---
            # 递归遍历 DOM 树查找 video 节点 ID (纯 Python 递归查找)
            video_node_id = inst.find_video_via_api()
            
            target_box = None
            if video_node_id:
                # 获取元素布局位置
                box_res = inst.send_cdp("DOM.getBoxModel", {"nodeId": video_node_id})
                if 'result' in box_res:
                    model = box_res['result']['model']
                    if model['width'] > 0 and model['height'] > 0:
                        # 找到有效可见的 video
                        content = model['content'] # [x1,y1, x2,y2, x3,y3, x4,y4]
                        target_box = {
                            'x': content[0], 
                            'y': content[1], 
                            'width': model['width'], 
                            'height': model['height']
                        }
                        print(f"[Win {inst.index}] API 找到 Video 元素 (已加载): NodeId={video_node_id}")

            # --- 3. 执行点击 (仅当找到视频元素时) ---
            if target_box:
                # [状态检查]
                # 获取准确的播放状态: PAUSED, BUFFERING, PLAYING
                play_status = inst.check_play_status(video_node_id)
                
                if play_status == "PLAYING":
                    print(f"[Win {inst.index}] ✅ 检测到视频已在播放 (RS>=3)，任务完成")
                    inst.media_playing = True
                    break
                    
                if play_status == "BUFFERING":
                    print(f"[Win {inst.index}] ⏳ 视频正在缓冲/加载中... 暂停操作")
                    inst.wait_and_process(1)
                    continue
                    
                # 只有状态为 PAUSED 时才点击
                print(f"[Win {inst.index}] ▶️ 视频处于暂停状态，准备点击...")

                cx = target_box['x'] + target_box['width'] / 2
                cy = target_box['y'] + target_box['height'] / 2
                
                print(f"[Win {inst.index}] -> 点击视频 ({int(cx)}, {int(cy)})")
                
                simulate_human_move(inst, random.randint(10, 200), random.randint(10, 200), cx, cy, steps=3)
                
                inst.send_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1})
                time.sleep(0.05)
                inst.send_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1})
                
                # 点击后等待一段时间，给播放器反应时间
                inst.wait_and_process(5)
            else:
                print(f"[Win {inst.index}] 等待视频元素加载...")
                inst.wait_and_process(2)
            
        except Exception as e:
            print(f"[Win {inst.index}] 异常: {e}")
            time.sleep(1)

    # 播放开始后
    print(f"✅ [Win {inst.index}] 视频确认正在播放! 开始计时观看...")
    min_d, max_d = play_duration_range
    print(f"🎉 [Win {inst.index}] 保持观看 {min_d}-{max_d} 秒...")
    inst.wait_and_process(random.randint(min_d, max_d))
    print(f"[Win {inst.index}] 观看结束。")
    
    # 重置页面，模拟关闭效果
    inst.send_cdp('Page.navigate', {'url': 'about:blank'})


def automation_task_vinovo(inst, win_x, win_y, win_w, win_h, play_duration_range=(90, 100)):
    """Vinovo 任务流程 (优化版)"""
    print(f"🚀 [Win {inst.index}] 开始 Vinovo 任务 (Target: 5q71nxk3agoj89)...")
    
    if not inst.connect():
        print(f"❌ [Win {inst.index}] 连接失败")
        return

    # 1. 布局窗口
    inst.set_bounds(win_x, win_y, win_w, win_h)

    # 2. 访问目标视频页
    target_url = 'https://vinovo.to/d/5q71nxk3agoj89'
    print(f"[Win {inst.index}] 正在访问: {target_url}")
    inst.send_cdp('Page.navigate', {'url': target_url})
    print(f"[Win {inst.index}] 正在加载页面...")
    
    # 等待初始加载
    inst.wait_and_process(5)
    
    print(f"[Win {inst.index}] 进入 Vinovo 自动化循环 (智能检测)...")

    buffering_start_time = 0
    
    # 循环直到检测到播放
    while not inst.media_playing and inst.running:
        try:
            # --- 0. 窗口维护: 聚焦主页 & 关闭广告 ---
            inst.maintain_focus()

            # --- 1. 使用 Media API 检查状态 ---
            if inst.media_playing:
                break
            
            # --- 2. 使用 DOM API 寻找元素 (No JS) ---
            video_node_id = inst.find_video_via_api()
            
            target_box = None
            if video_node_id:
                box_res = inst.send_cdp("DOM.getBoxModel", {"nodeId": video_node_id})
                if 'result' in box_res:
                    model = box_res['result']['model']
                    if model['width'] > 0 and model['height'] > 0:
                        content = model['content']
                        target_box = {
                            'x': content[0], 
                            'y': content[1], 
                            'width': model['width'], 
                            'height': model['height']
                        }
                        # print(f"[Win {inst.index}] API 找到 Video 元素: NodeId={video_node_id}")

            # --- 3. 执行逻辑 (仅当找到视频元素时) ---
            if target_box:
                # [状态检查]
                play_status = inst.check_play_status(video_node_id)
                
                # 情况A: JS显示正在播放 (但CDP可能还没捕获到)
                if play_status == "PLAYING":
                    print(f"[Win {inst.index}] JS状态为 PLAYING, 等待 CDP 事件确认...")
                    buffering_start_time = 0
                    inst.wait_and_process(2)
                    continue
                
                # 情况B: 缓冲中 (可能卡住)
                if play_status == "BUFFERING":
                    if buffering_start_time == 0:
                        buffering_start_time = time.time()
                    
                    elapsed = time.time() - buffering_start_time
                    if elapsed > 10:
                        print(f"[Win {inst.index}] ⚠️ 视频缓冲超时 ({int(elapsed)}s)，尝试点击唤醒...")
                        buffering_start_time = 0 # 重置
                        # 强制点击逻辑，流向下方点击代码
                    else:
                        print(f"[Win {inst.index}] ⏳ 视频正在缓冲 ({int(elapsed)}s)...")
                        inst.wait_and_process(1)
                        continue
                else:
                    buffering_start_time = 0

                # 情况C: 暂停 或 缓冲超时 -> 点击
                print(f"[Win {inst.index}] ▶️ 准备点击视频 (Status={play_status})...")

                cx = target_box['x'] + target_box['width'] / 2
                cy = target_box['y'] + target_box['height'] / 2
                
                simulate_human_move(inst, random.randint(10, 200), random.randint(10, 200), cx, cy, steps=3)
                
                inst.send_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1})
                time.sleep(0.05)
                inst.send_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1})
                
                # 点击后等待，给播放器反应时间
                inst.wait_and_process(3)

            else:
                print(f"[Win {inst.index}] 未找到视频元素，等待加载...")
                inst.wait_and_process(2)

        except Exception as e:
            print(f"[Win {inst.index}] 异常: {e}")
            time.sleep(1)

    # 播放开始后
    if inst.media_playing:
        print(f"✅ [Win {inst.index}] 视频确认正在播放! 开始计时观看...")
        min_d, max_d = play_duration_range
        print(f"🎉 [Win {inst.index}] 保持观看 {min_d}-{max_d} 秒...")
        inst.wait_and_process(random.randint(min_d, max_d))
        print(f"[Win {inst.index}] 观看结束。")
        return True
    
    # 重置页面
    inst.send_cdp('Page.navigate', {'url': 'about:blank'})
    return False


def automation_task_bigshare(inst, win_x, win_y, win_w, win_h, play_duration_range=(30, 30), round_budget_seconds=180):
    """BigShare 任务流程 - 基于 CDP 的严格播放检测与累计计时"""
    print(f"🚀 [Win {inst.index}] 开始 BigShare 任务 (Target: 40289/e)...")
    
    if not inst.connect():
        print(f"❌ [Win {inst.index}] CDP 连接失败")
        return False

    inst.set_bounds(win_x, win_y, win_w, win_h)

    target_url = 'https://bigshare.io/watch/40289/e'
    referrer_url = 'https://blog-five-lime-46.vercel.app/'
    print(f"[Win {inst.index}] 正在访问视频页: {target_url}")
    inst.send_cdp('Page.navigate', {'url': target_url, 'referrer': referrer_url})
    inst.wait_and_process(8)
    
    print(f"[Win {inst.index}] 页面加载完成，进入播放检测循环 (每 3 秒检测一次)...")

    def check_play_status_by_html():
        """用户自定义的播放状态检测逻辑 - 通过正则匹配 HTML 中的 display 样式
        返回: (is_playing, node_id) - is_playing=True 表示正在播放，node_id 用于后续点击
        """
        try:
            doc_res = inst.send_cdp("DOM.getDocument", {"depth": 0})
            root_id = doc_res.get('result', {}).get('root', {}).get('nodeId')
            if not root_id:
                return None, None

            q_res = inst.send_cdp("DOM.querySelector", {
                "nodeId": root_id,
                "selector": ".art-control.art-control-playAndPause"
            })
            node_id = q_res.get('result', {}).get('nodeId')
            if not node_id or node_id <= 0:
                return None, None

            html_res = inst.send_cdp("DOM.getOuterHTML", {"nodeId": node_id})
            if 'result' not in html_res or 'outerHTML' not in html_res['result']:
                return None, None

            play_html = html_res['result']['outerHTML']
            pattern = r'style="[^"]*(display\s*:\s*[^;"]+;)"\s*><svg\s+xmlns'
            match = re.search(pattern, play_html)
            
            if not match:
                return None, node_id
            
            is_play = True if match.group(1) == "display: none;" else False
            return is_play, node_id
        except Exception as e:
            return None, None

    def click_play_button(node_id):
        """点击播放按钮"""
        try:
            box_res = inst.send_cdp("DOM.getBoxModel", {"nodeId": node_id})
            if 'result' not in box_res:
                return False

            model = box_res['result']['model']
            if model['width'] <= 0 or model['height'] <= 0:
                return False

            content = model['content']
            cx = content[0] + model['width'] / 2
            cy = content[1] + model['height'] / 2

            simulate_human_move(inst, random.randint(10, 200), random.randint(10, 200), cx, cy, steps=5)
            inst.send_cdp("Input.dispatchMouseEvent", {
                "type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1
            })
            time.sleep(0.08)
            inst.send_cdp("Input.dispatchMouseEvent", {
                "type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1
            })
            print(f"[Win {inst.index}] ▶️ 已点击播放按钮")
            return True
        except Exception as e:
            print(f"[Win {inst.index}] 点击播放按钮异常: {e}")
            return False

    task_start = time.time()
    last_check = 0.0
    last_reload = 0.0
    
    play_start_time = None
    accumulated_play_time = 0.0
    min_play_duration, max_play_duration = play_duration_range
    required_play_duration = random.randint(min_play_duration, max_play_duration)
    
    print(f"[Win {inst.index}] 需要累计播放时长: {required_play_duration} 秒")

    while inst.running:
        try:
            now = time.time()
            
            if now - task_start > round_budget_seconds:
                print(f"⚠️ [Win {inst.index}] 任务超时 ({round_budget_seconds}s)，放弃本轮任务")
                inst.send_cdp('Page.navigate', {'url': 'about:blank'})
                return False

            inst.maintain_focus()

            if now - last_check >= 3.0:
                last_check = now
                
                is_play, node_id = check_play_status_by_html()
                
                if is_play is True:
                    if play_start_time is None:
                        play_start_time = now
                        print(f"[Win {inst.index}] ✅ 检测到视频开始播放 (用户自定义检测: is_play=True)")
                    else:
                        elapsed = now - play_start_time
                        accumulated_play_time = elapsed
                        print(f"[Win {inst.index}] 📊 播放中... 已累计: {accumulated_play_time:.1f}s / {required_play_duration}s")
                        
                        if accumulated_play_time >= required_play_duration:
                            print(f"✅ [Win {inst.index}] 播放成功! 累计播放 {accumulated_play_time:.1f} 秒")
                            inst.send_cdp('Page.navigate', {'url': 'about:blank'})
                            return True
                elif is_play is False:
                    if play_start_time is not None:
                        print(f"⚠️ [Win {inst.index}] 播放中断 (用户自定义检测: is_play=False)，重置计时器")
                        play_start_time = None
                        accumulated_play_time = 0.0
                    else:
                        print(f"[Win {inst.index}] 视频未播放，尝试点击播放按钮...")
                        if node_id and click_play_button(node_id):
                            inst.wait_and_process(3)
                        else:
                            if now - last_reload > 30:
                                print(f"⚠️ [Win {inst.index}] 长时间无法点击播放按钮，刷新页面...")
                                last_reload = now
                                inst.send_cdp('Page.navigate', {'url': target_url, 'referrer': referrer_url})
                                inst.wait_and_process(8)
                                play_start_time = None
                                accumulated_play_time = 0.0
                else:
                    if now - last_reload > 30:
                        print(f"⚠️ [Win {inst.index}] 无法获取播放状态 (is_play=None)，刷新页面...")
                        last_reload = now
                        inst.send_cdp('Page.navigate', {'url': target_url, 'referrer': referrer_url})
                        inst.wait_and_process(8)
                        play_start_time = None
                        accumulated_play_time = 0.0

            inst.wait_and_process(0.5)

        except Exception as e:
            print(f"[Win {inst.index}] 循环异常: {e}")
            time.sleep(1)

    inst.send_cdp('Page.navigate', {'url': 'about:blank'})
    return False


# ===== 4. 主程序入口 =====
def main():
    # 配置
    CHROME_BIN = r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    DATA_DIR = r"/Volumes/SSD-SAMSUNG/demo/chromium/testCDP"
    FP_PATH = r"E:\pycode\ruyicdp\fp.txt"
    
    COLS, ROWS = 2, 2
    NUM_INSTANCES = 4
    LOCAL_PROXY_START = 10005  # 对应代理脚本的起始端口 (10005-10008)
    
    PLAY_DURATION_RANGE = (30, 30)
    ROUND_BUDGET_SECONDS = 120
    RESTART_COOLDOWN_SECONDS = 5

    WORK_WIDTH, WORK_HEIGHT = get_work_area()
    win_w, win_h = WORK_WIDTH / COLS, WORK_HEIGHT / ROWS
    
    instances = []
    
    # 1. 初始化实例对象
    print("正在初始化实例对象...")
    for i in range(NUM_INSTANCES):
        # 为每个窗口分配 调试端口(9222+i) 和 代理端口(10005+i)
        inst = RuyiInstance(i, 9222 + i, LOCAL_PROXY_START + i, DATA_DIR, CHROME_BIN, FP_PATH)
        instances.append(inst)
    
    def worker_loop(inst, wx, wy, ww, wh):
        while True:
            try:
                print(f"\n[{time.strftime('%H:%M:%S')}] [Win {inst.index}] 启动浏览器进程...")
                inst.launch()
                time.sleep(5)
                ok = automation_task_bigshare(inst, wx, wy, ww, wh, PLAY_DURATION_RANGE, round_budget_seconds=ROUND_BUDGET_SECONDS)
            except Exception as e:
                print(f"[Win {inst.index}] 线程异常: {e}")
                ok = False
            finally:
                inst.close()

            if not ok:
                print(f"[Win {inst.index}] 未完成播放，等待 {RESTART_COOLDOWN_SECONDS}s 后重启...")
                time.sleep(RESTART_COOLDOWN_SECONDS)

    threads = []
    for i, inst in enumerate(instances):
        wx = (i % COLS) * win_w
        wy = (i // COLS) * win_h
        t = threading.Thread(target=worker_loop, args=(inst, wx, wy, win_w, win_h), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        
if __name__ == "__main__":
    main()