import asyncio
import socket
import time
import random

# --- 配置区域 ---
REMOTE_SOCKS_HOST = 'us.arxlabs.io'
# REMOTE_SOCKS_HOST = '3ef8f2e5e5fa8c3b.lqz.na.ipidea.online'
REMOTE_SOCKS_PORT = 3010
ISOLATED_COOLDOWN = 600
REMOTE_TIMEOUT = 10
REMOTE_RETRY_MAX_ATTEMPTS = 0
# 你的四个账号信息 (请务必核对 10004 的账号密码)
# PROXY_CONFIGS = [
#     {"local_port": 10005, "user": "sASaSu1woq6Oyk5LbP-zone-custom", "pass": "qILdeK4TOI"},
#     {"local_port": 10006, "user": "R0tJznI2fVWHyx_E7x-zone-custom", "pass": "Tlwulnn4Cw"},
#     {"local_port": 10007, "user": "olC7vNxDWOQH5DICpg-zone-custom", "pass": "Vcq35ZZrtu"},
#     {"local_port": 10008, "user": "ji0A_DepQkaZQP1yPR-zone-custom", "pass": "RuKVd5wLC9"},
# ]

PROXY_CONFIGS = [
    {
        "local_port": 10005,
        "remote_host": "port1.novproxy.io",
        "remote_port": 4236,
        "user": "BMFrVxVYgTA9",
        "pass": "8ds82Rz2CTee",
    },
    {
        "local_port": 10006,
        "remote_host": "45.43.58.27",
        "remote_port": 4072,
        "user": "AO2hV8BZPRVf",
        "pass": "ZMhCUDO6qajx",
    },
    {
        "local_port": 10007,
        "remote_host": "45.43.58.27",
        "remote_port": 4259,
        "user": "5qMZ7caXdFfv",
        "pass": "284XVwvRJ1R7",
    },
    {
        "local_port": 10008,
        "remote_host": "45.43.58.27",
        "remote_port": 4472,
        "user": "YppV3qErmL9q",
        "pass": "9Qh1w7irxrGn",
    },
]


class SOCKS5Bridge:
    def __init__(self, config):
        self.config = config
        # 用于保存正在运行的任务引用，防止被垃圾回收
        self.tasks = set()
        self.cooldown_until = 0.0

    async def pipe(self, reader, writer):
        try:
            while not reader.at_eof():
                data = await reader.read(16384)  # 增大缓冲区到 16KB
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
            pass
        except Exception as e:
            print(f"[{self.config['local_port']}] 转发异常: {e}")
        finally:
            if not writer.is_closing():
                writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

    async def handle_client(self, reader, writer):
        remote_reader, remote_writer = None, None
        local_port = self.config['local_port']

        try:
            now = time.time()
            if now < self.cooldown_until:
                writer.close()
                return

            # 1. 浏览器握手
            try:
                header = await reader.readexactly(2)
            except asyncio.IncompleteReadError:
                writer.close()
                return

            if not header or header[0] != 0x05:
                writer.close()
                return
            nmethods = header[1]

            try:
                methods = await reader.readexactly(nmethods) if nmethods else b""
            except asyncio.IncompleteReadError:
                writer.close()
                return

            if 0x00 not in methods:
                writer.write(bytes([0x05, 0xFF]))
                await writer.drain()
                writer.close()
                return

            writer.write(bytes([0x05, 0x00]))
            await writer.drain()

            remote_host = self.config.get('remote_host') or REMOTE_SOCKS_HOST
            remote_port = self.config.get('remote_port') or REMOTE_SOCKS_PORT

            attempt = 0
            while True:
                attempt += 1
                if REMOTE_RETRY_MAX_ATTEMPTS and attempt > REMOTE_RETRY_MAX_ATTEMPTS:
                    print(f"[{local_port}] 远程握手重试次数已达上限: {REMOTE_RETRY_MAX_ATTEMPTS}")
                    writer.close()
                    return

                if remote_writer and (not remote_writer.is_closing()):
                    remote_writer.close()
                if remote_writer:
                    try:
                        await remote_writer.wait_closed()
                    except:
                        pass
                remote_reader, remote_writer = None, None

                try:
                    remote_reader, remote_writer = await asyncio.wait_for(
                        asyncio.open_connection(remote_host, remote_port),
                        timeout=REMOTE_TIMEOUT
                    )

                    remote_writer.write(bytes([0x05, 0x02, 0x00, 0x02]))
                    await remote_writer.drain()

                    methods = await asyncio.wait_for(remote_reader.readexactly(2), timeout=REMOTE_TIMEOUT)
                    chosen = methods[1] if methods else 0xFF
                    if chosen not in (0x00, 0x02):
                        raise ConnectionError(f"auth method={chosen}")

                    if chosen == 0x02:
                        auth_packet = (bytes([0x01, len(self.config['user'])]) +
                                       self.config['user'].encode() +
                                       bytes([len(self.config['pass'])]) +
                                       self.config['pass'].encode())
                        remote_writer.write(auth_packet)
                        await remote_writer.drain()

                        auth_res = await asyncio.wait_for(remote_reader.readexactly(2), timeout=REMOTE_TIMEOUT)
                        if (not auth_res) or auth_res[1] != 0x00:
                            print(f"❌ [{local_port}] 认证失败! 请检查账号: {self.config['user']}")
                            self.cooldown_until = time.time() + ISOLATED_COOLDOWN
                            return

                    break

                except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionError, OSError) as e:
                    print(f"[{local_port}] 远程握手读取失败: {e}")
                    delay = min(5.0, 0.25 * (2 ** min(attempt - 1, 4)))
                    delay = delay + random.uniform(0, 0.2)
                    await asyncio.sleep(delay)
                    continue

            # 4. 建立双向转发任务
            # 使用 wait 确保两个 pipe 协程运行结束前 handle_client 不会退出
            t1 = asyncio.create_task(self.pipe(reader, remote_writer))
            t2 = asyncio.create_task(self.pipe(remote_reader, writer))

            self.tasks.add(t1)
            self.tasks.add(t2)
            t1.add_done_callback(self.tasks.discard)
            t2.add_done_callback(self.tasks.discard)

            # 核心修改：显式等待任务完成，防止 Task 被 destroy
            await asyncio.wait([t1, t2])

        except Exception as e:
            # print(f"[{local_port}] 连接处理异常: {e}")
            pass
        finally:
            if not writer.is_closing():
                writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

            if remote_writer and (not remote_writer.is_closing()):
                remote_writer.close()
            if remote_writer:
                try:
                    await remote_writer.wait_closed()
                except:
                    pass

    async def start(self):
        server = await asyncio.start_server(self.handle_client, '127.0.0.1', self.config['local_port'])
        print(f"✅ 代理端口 {self.config['local_port']} 已启动 -> {self.config['user'][:10]}...")
        async with server:
            await server.serve_forever()


async def main():
    # 为每个配置创建一个独立的 Bridge 实例
    tasks = []
    for cfg in PROXY_CONFIGS:
        bridge = SOCKS5Bridge(cfg)
        tasks.append(asyncio.create_task(bridge.start()))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        # 设置 Windows 事件循环策略，减少 Proactor 报错
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务已停止")