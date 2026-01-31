import json

import requests
import time
import random
import concurrent.futures
from DrissionPage import ChromiumPage, ChromiumOptions

# ========== 配置 ==========
API_BASE_URL = "http://127.0.0.1:50326"
API_KEY = "asp_f597909ac059edff7c71a6dec19338f0c32b840e3ded5ef3"  # 在 TgeBrowser 客户端获取

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def create_env():
    # ========== 步骤 1: 创建浏览器环境 ==========
    print("1. 创建浏览器环境...")
    response = requests.post(
        f"{API_BASE_URL}/api/browser/create",
        json={
            "browserName": "自动化测试1",  # 环境名称
            "proxy": {
                "protocol": "socks5",
                "host": "86.53.76.99",
                "port": 443,
                "username": "SdHNYQEhepMa",
                "password": "vUeLkdmk56",
            },
            "fingerprint": {
                "os": "Windows",
                "platformVersion": 11,
                "kernel": "135",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.9.2537 Safari/537.36",
                "canvas": True,
                "speechVoices": True,
                "clientRects": True,
                "fonts": ["Arial", "Courier New"],
                "disableTLS": [],
                "resolution": "1920x1080",
                "ram": 8,
                "cpu": 4,
                "language": "en-US",
                "languageBaseIp": True,
                "timezone": "Europe/Amsterdam",
                "timezoneBaseIp": True,
                "hardwareAcceleration": True,
                "disableSandbox": False,
                "startupParams": "",
                "deviceName": "DESKTOP-ABCD",
                "portScanProtection": ""
            },
            "startInfo": {
                "startPage": {
                    "mode": "custom",
                    "value": [
                        "https://www.baidu.com"
                    ]
                },
                "otherConfig": {
                    "openConfigPage": False,
                    "checkPage": True,
                    "extensionTab": True
                }
            }
        },
        headers=headers
    )

    env_id = response.json()["data"]["envId"]
    print(f"   环境创建成功，ID: {env_id}")

    # ========== 步骤 2: 启动浏览器 ==========
    print("2. 启动浏览器...")
    response = requests.post(
        f"{API_BASE_URL}/api/browser/start",
        json={"envId": env_id},
        headers=headers
    )

    debug_port = response.json()["data"]["port"]
    print(f"   浏览器已启动，调试端口: {debug_port}")

    # ========== 步骤 3: 连接 DrissionPage ==========
    print("3. 连接 DrissionPage...")
    time.sleep(3)  # 等待浏览器完全启动

    # 方式1: 通过端口连接（推荐）
    co = ChromiumOptions().set_local_port(debug_port)
    page = ChromiumPage(addr_or_opts=co)

    # 方式2: 直接使用端口号
    # from DrissionPage import Chromium
    # page = Chromium(debug_port)

    # 方式3: 使用地址:端口
    # page = Chromium(f'127.0.0.1:{debug_port}')

    # 方式4: 使用 WebSocket URL（需要先获取 ws_url）
    # ws_url = response.json()["data"]["ws"]
    # page = Chromium(ws_url)

    print("   DrissionPage 连接成功")

    # ========== 步骤 4: 执行自动化操作 ==========
    print("4. 执行自动化操作...")

    # 访问网页
    page.get('https://vinovo.si/dash/statistics')
    print(f"   当前页面: {page.title}")

    # 更多操作示例
    page.get_screenshot('screenshot.png')  # 截图
    print("   已保存截图")

    print("\n完成！")


def browser_start():
    data = {
        "envId": 262424,
        # "args": ["--headless"],
        "port": 1111
    }

    response = requests.post(API_BASE_URL + '/api/browser/start', headers=headers, json=data)

    print(response.json())


# 获取环境列表
def select_group(keyword: str):
    params = {
        "current": 1,
        "pageSize": 20,
        "keyword": keyword
    }

    response = requests.get(API_BASE_URL + '/api/browser/list', headers=headers, params=params).text
    print(json.loads(response))


# 获取正在运行的环境列表
def select_open_list():
    response = requests.get(API_BASE_URL + '/api/browser/open/list', headers=headers)
    print(response.json())


# 获取分组列表
def group_list():
    params = {
        'current': '1',
        'pageSize': '20'
    }
    response = requests.get(API_BASE_URL + '/api/groups/list', params=params, headers=headers)
    print(response.json())


# 获取代理列表
def proxies_list():
    params = {
        'current': '1',
        'pageSize': '20'
    }
    response = requests.get(API_BASE_URL + '/api/proxies/list', params=params, headers=headers)
    print(response.json())


def ip_test(envId, port):
    data = {
        "envId": envId,
        # "args": ["--headless"],
        "port": port
    }

    response = requests.post(API_BASE_URL + '/api/browser/start', headers=headers, json=data)

    print(response.json())
    debug_port = response.json()["data"]["port"]
    print(f"   浏览器已启动，调试端口: {debug_port}")

    # ========== 步骤 3: 连接 DrissionPage ==========
    print("3. 连接 DrissionPage...")
    time.sleep(3)  # 等待浏览器完全启动

    # 通过端口连接（推荐）
    co = ChromiumOptions().set_local_port(debug_port)
    page = ChromiumPage(addr_or_opts=co)

    page.get('https://mmxxyy.vidplayer.live/#wvrm5')  # https://vinovo.to/d/9qo4rnd2an26w0  https://mmxxyy.vidplayer.live/#wvrm5

    # 模拟人工操作：等待页面加载
    print("   等待页面加载及模拟人工观察...")
    time.sleep(random.uniform(3, 5))

    # 记录当前Tab，确保后续始终聚焦此页面
    main_tab_id = page.tab_id

    # 模拟人工浏览：随机滚动查看页面
    scroll_pixels = random.randint(300, 700)
    page.scroll.down(scroll_pixels)
    time.sleep(random.uniform(1.5, 3.0))  # 停留阅读
    page.scroll.up(random.randint(100, scroll_pixels // 2))  # 往回滚一点
    time.sleep(random.uniform(0.5, 1.5))
    page.scroll.to_top()

    # 确保页面始终为目标URL
    target_url = 'https://mmxxyy.vidplayer.live/#wvrm5'
    if target_url not in page.url:
        print(f"   页面URL不匹配 ({page.url})，重新加载目标页面...")
        page.get(target_url)
        time.sleep(3)

    # 查找视频元素
    print("   查找视频元素...")
    video_ele = page.ele('tag:video')

    if video_ele:
        print("   找到视频元素，准备模拟真人点击...")

        # 1. 模拟鼠标随机漫游，先移到视频附近（假装没对准）
        page.actions.move_to(video_ele, offset_x=random.randint(50, 150), offset_y=random.randint(50, 150))
        time.sleep(random.uniform(0.5, 1.0))

        # 2. 移动到视频正中心（播放按钮位置）
        print("   瞄准视频正中心播放按钮...")

        # 3. 执行点击尝试循环（应对多次弹窗跳转）
        max_attempts = 10
        is_playing = False

        for attempt in range(max_attempts):
            print(f"   [第 {attempt + 1} 次尝试] 准备点击...")

            # 再次确认是否有弹窗需要先处理
            current_tabs = page.tab_ids
            if len(current_tabs) > 1:
                print("   点击前检测到多余窗口，先清理...")
                for tid in current_tabs:
                    if tid != main_tab_id:
                        try:
                            page.get_tab(tid).close()
                        except:
                            pass
                page.activate_tab(main_tab_id)

            # 重新瞄准视频中心（确保位置准确）
            # 增加拟人化轨迹：先移到边缘，再精确瞄准中心
            w, h = video_ele.rect.size
            # 1. 快速移到视频区域内的一个随机点
            page.actions.move_to(video_ele, offset_x=random.randint(int(w*0.1), int(w*0.3)), offset_y=random.randint(int(h*0.1), int(h*0.3)))
            time.sleep(random.uniform(0.2, 0.5))
            
            # 2. 精确移动到视频正中心（播放按钮位置）
            # 仅施加极小的随机偏移（模拟真人瞄准中心时的微颤）
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            page.actions.move_to(video_ele, offset_x=offset_x, offset_y=offset_y)
            
            # 关键：等待鼠标变成手型（模拟真人的视觉确认过程）
            # 这里的等待时间模拟了用户移动鼠标到按钮上，看到指针变化确认可点击，然后再按下的过程
            print("   悬停等待鼠标指针变为手型...")
            time.sleep(random.uniform(1.0, 2.0))

            # 点击动作
            page.actions.click()
            print("   已点击")
            
            # 点击后立即等待并检查弹窗（最容易出弹窗的时候）
            time.sleep(2)
            if len(page.tab_ids) > 1:
                print("   检测到新窗口跳转，执行关闭并切回操作...")
                for tid in page.tab_ids:
                    if tid != main_tab_id:
                        try:
                            page.get_tab(tid).close()
                        except:
                            pass
                page.activate_tab(main_tab_id)
                print("   已聚焦回视频页面")
            
            # 检查播放状态
            try:
                is_paused = video_ele.run_js('return this.paused')
                if not is_paused:
                    # 进一步确认进度条是否在走
                    t1 = video_ele.run_js('return this.currentTime')
                    time.sleep(1.5)
                    t2 = video_ele.run_js('return this.currentTime')
                    
                    if t2 > t1:
                        print("   ✅ 确认视频正在播放中")
                        is_playing = True
                        break
                    else:
                        print("   视频状态非暂停但进度未动，可能是缓冲或假播放")
                else:
                    print("   视频仍处于暂停状态")
                    
            except Exception as e:
                print(f"   检查播放状态时出错: {e}")

        # 确保播放持续10秒
        if is_playing:
            print("   ⏳ 保持观看 10 秒...")
            start_time = time.time()
            while time.time() - start_time < 12:  # 稍微多一点余量
                time.sleep(1)
                # 持续监控弹窗
                if len(page.tab_ids) > 1:
                    print("   播放期间检测到弹窗，关闭中...")
                    for tid in page.tab_ids:
                        if tid != main_tab_id:
                            try:
                                page.get_tab(tid).close()
                            except:
                                pass
                    page.activate_tab(main_tab_id)

                # 持续监控播放状态
                try:
                    if video_ele.run_js('return this.paused'):
                        print("   视频中途暂停，尝试恢复...")
                        video_ele.run_js('this.play()')
                except:
                    pass

        print("   视频播放状态确认完毕")
    else:
        print("   未找到 video 标签，尝试通用点击策略...")
        # 点击页面中心区域
        w, h = page.rect.size
        page.actions.move_to((w // 2, h // 2)).click()

    # 观看一小会儿
    time.sleep(random.uniform(2, 4))

    print(f"   当前页面: {page.title}")

    time.sleep(2)
    page.quit()


# 262421  262424
if __name__ == '__main__':
    # select_group('自动化')
    # browser_start()
    # select_open_list()
    # group_list()
    # proxies_list()
    envId_list = [262424,264512,264514,264517,264520]
    # envId_list = [264512]
    base_port = 1111
    
    while True:
        print(f"\n========== 开始新一轮任务: {time.strftime('%Y-%m-%d %H:%M:%S')} ==========")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(envId_list)) as executor:
            futures = []
            for i, envId in enumerate(envId_list):
                port = base_port + i
                print(f"Submitting task for envId: {envId}, port: {port}")
                futures.append(executor.submit(ip_test, envId, port))
                
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Task failed with error: {e}")
        
        print("本轮任务完成，进入 3 分钟倒计时...")
        wait_seconds = 180
        for s in range(wait_seconds, 0, -1):
            # 每 30 秒或最后 10 秒打印一次，避免刷屏太快
            if s % 30 == 0 or s <= 10:
                print(f"   距离下一轮还有: {s} 秒...")
            time.sleep(1)
        print("\n")
