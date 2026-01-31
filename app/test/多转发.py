import asyncio
import socket

# --- 配置区域 ---
REMOTE_SOCKS_HOST = 'us.arxlabs.io'
# REMOTE_SOCKS_HOST = '3ef8f2e5e5fa8c3b.lqz.na.ipidea.online'
REMOTE_SOCKS_PORT = 3010
# 你的四个账号信息 (请务必核对 10004 的账号密码)
# PROXY_CONFIGS = [
#     {"local_port": 10005, "user": "sASaSu1woq6Oyk5LbP-zone-custom", "pass": "qILdeK4TOI"},
#     {"local_port": 10006, "user": "R0tJznI2fVWHyx_E7x-zone-custom", "pass": "Tlwulnn4Cw"},
#     {"local_port": 10007, "user": "olC7vNxDWOQH5DICpg-zone-custom", "pass": "Vcq35ZZrtu"},
#     {"local_port": 10008, "user": "ji0A_DepQkaZQP1yPR-zone-custom", "pass": "RuKVd5wLC9"},
# ]

PROXY_CONFIGS = [
    {"local_port": 10005, "user": "mxy1q2w3e4r1-region-GB-sid-mQSbHYhy-t-5", "pass": "mxy1q2w3e4r1"},
    {"local_port": 10006, "user": "vgik1120227-region-GB-sid-wtmCmRBF-t-5", "pass": "r1tiglzc"},
    # {"local_port": 10007, "user": "lhyQI6sk864vsi5YyJ-zone-custom-region-my", "pass": "lCMs0b6c9V"},
    # {"local_port": 10008, "user": "iWO01bn8EdLlHaYUu4-zone-custom-region-my", "pass": "UbbQ7gNUE1"},
    # {"local_port": 10009, "user": "EPxPBXJJoZK29pdAgQ-zone-custom-region-my", "pass": "SIF4Pp3kVe"},
    # {"local_port": 10010, "user": "CD3kBlMTvBPqmy4kTV-zone-custom-region-my", "pass": "FgeWqPlR6J"},
    # {"local_port": 10011, "user": "snY4DgnUPLLms15AGn-zone-custom-region-my", "pass": "nVqny4v6qB"},
    # {"local_port": 10012, "user": "mxmv0o_R6mDZO_MtId-zone-custom-region-my", "pass": "qlZyojBm0w"},
    # {"local_port": 10013, "user": "n6CxH7DFPzWaIbZP_k-zone-custom-region-id", "pass": "EyQer2Vs0U"},
    # {"local_port": 10014, "user": "h_aUt7xsf5R62TlHQX-zone-custom-region-gb", "pass": "pIImjeLn8r"},

]


class SOCKS5Bridge:
    def __init__(self, config):
        self.config = config
        # 用于保存正在运行的任务引用，防止被垃圾回收
        self.tasks = set()

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
            # 1. 浏览器握手
            data = await reader.read(3)
            if not data or data[0] != 0x05:
                writer.close()
                return
            writer.write(bytes([0x05, 0x00]))
            await writer.drain()

            # 2. 连接远程代理
            try:
                remote_reader, remote_writer = await asyncio.open_connection(
                    REMOTE_SOCKS_HOST, REMOTE_SOCKS_PORT)
            except Exception as e:
                print(f"[{local_port}] 无法连接远程服务器: {e}")
                writer.close()
                return

            # 3. 远程身份验证 (RFC 1929)
            remote_writer.write(bytes([0x05, 0x01, 0x02]))
            await remote_writer.drain()

            methods = await remote_reader.read(2)
            if not methods or methods[1] != 0x02:
                print(f"[{local_port}] 远程服务器不支持密码认证")
                return

            auth_packet = (bytes([0x01, len(self.config['user'])]) +
                           self.config['user'].encode() +
                           bytes([len(self.config['pass'])]) +
                           self.config['pass'].encode())
            remote_writer.write(auth_packet)
            await remote_writer.drain()

            auth_res = await remote_reader.read(2)
            if not auth_res or auth_res[1] != 0x00:
                print(f"❌ [{local_port}] 认证失败! 请检查账号: {self.config['user']}")
                return

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