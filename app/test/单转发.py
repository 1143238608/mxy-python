import asyncio
import socket

# --- 配置区域 ---
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 1081  # 浏览器连接这个端口（无需密码）

REMOTE_SOCKS_HOST = 'prem.iprocket.io'
REMOTE_SOCKS_PORT = 9595  # 远程SOCKS5端口
REMOTE_USER = 'sub14104296-res-hk'
REMOTE_PASS = 'FjCC156Il8IkI8F'


async def handle_client(reader, writer):
    try:
        # 1. 处理浏览器的 SOCKS5 握手 (No Auth)
        data = await reader.read(3)
        if not data or data[0] != 0x05:
            writer.close()
            return

        # 告诉浏览器：我们接受“无需认证”方式
        writer.write(bytes([0x05, 0x00]))
        await writer.drain()

        # 2. 连接远程真实的 SOCKS5 服务器
        remote_reader, remote_writer = await asyncio.open_connection(
            REMOTE_SOCKS_HOST, REMOTE_SOCKS_PORT)

        # 3. 与远程服务器进行身份验证 (RFC 1929)
        # 发送支持的方法：用户名密码 (0x02)
        remote_writer.write(bytes([0x05, 0x01, 0x02]))
        await remote_writer.drain()

        resp = await remote_reader.read(2)
        if resp[1] != 0x02:
            print("远程服务器不支持用户名密码认证")
            return

        # 发送用户名和密码
        auth_packet = bytes([0x01]) + \
                      bytes([len(REMOTE_USER)]) + REMOTE_USER.encode() + \
                      bytes([len(REMOTE_PASS)]) + REMOTE_PASS.encode()
        remote_writer.write(auth_packet)
        await remote_writer.drain()

        auth_resp = await remote_reader.read(2)
        if auth_resp[1] != 0x00:
            print("认证失败，请检查用户名密码")
            return

        # 4. 建立双向转发（透传模式）
        async def pipe(r, w):
            try:
                while True:
                    d = await r.read(4096)
                    if not d: break
                    w.write(d)
                    await w.drain()
            except:
                pass
            finally:
                w.close()

        # 同时运行两个转发方向
        await asyncio.gather(
            pipe(reader, remote_writer),
            pipe(remote_reader, writer)
        )

    except Exception as e:
        print(f"处理连接时出错: {e}")
    finally:
        writer.close()


async def main():
    server = await asyncio.start_server(handle_client, LOCAL_HOST, LOCAL_PORT)
    print(f"中转代理已启动: {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_SOCKS_HOST}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())