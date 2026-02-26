"""
Python equivalent of index源码.js
Install: pip install -r requirements.txt
Run:     python main.py
Env vars:
  PORT  - listening port (default 3000)
  TOKEN - WebSocket auth token (default ech123456)
  PRIP  - comma-separated fallback IPs (default ProxyIP.JP.CMLiussss.net)
"""

import asyncio
import json
import logging
import os
import socket
import time

import aiohttp
from aiohttp import web

# ── 配置 ──────────────────────────────────────────────────────────────────────
PORT  = int(os.environ.get('PORT', 3000))
TOKEN = os.environ.get('TOKEN', 'ech123456')
CF_FALLBACK_IPS = (
    os.environ['PRIP'].split(',')
    if os.environ.get('PRIP')
    else ['ProxyIP.JP.CMLiussss.net']
)

DOH_SERVERS = [
    'https://dns.google/dns-query',
    'https://cloudflare-dns.com/dns-query',
    'https://dns.alidns.com/dns-query',
]

DNS_CACHE_TTL = 300  # seconds
dns_cache: dict = {}  # {hostname: {ip, timestamp}}

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)


# ── DoH DNS 解析 ──────────────────────────────────────────────────────────────

def is_ip(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, addr.strip('[]'))
        return True
    except OSError:
        pass
    return False


async def query_doh(session: aiohttp.ClientSession, doh_server: str, hostname: str) -> str:
    url = f"{doh_server}?name={hostname}&type=A"
    async with session.get(
        url,
        headers={'Accept': 'application/dns-json'},
        timeout=aiohttp.ClientTimeout(total=5)
    ) as resp:
        data = await resp.json(content_type=None)
        for ans in (data.get('Answer') or []):
            if ans.get('type') == 1:  # A record
                return ans['data']
        raise ValueError('No A record found')


async def resolve_doh(hostname: str) -> str:
    # 缓存命中
    cached = dns_cache.get(hostname)
    if cached and time.time() - cached['timestamp'] < DNS_CACHE_TTL:
        log.info(f"[DoH Cache Hit] {hostname} -> {cached['ip']}")
        return cached['ip']

    # 已是 IP 直接返回
    if is_ip(hostname):
        return hostname

    log.info(f"[DoH Query] Resolving {hostname}...")

    async with aiohttp.ClientSession() as session:
        for doh_server in DOH_SERVERS:
            try:
                ip = await query_doh(session, doh_server, hostname)
                dns_cache[hostname] = {'ip': ip, 'timestamp': time.time()}
                log.info(f"[DoH Success] {hostname} -> {ip} (via {doh_server})")
                return ip
            except Exception as e:
                log.error(f"[DoH Failed] {doh_server}: {e}")

    # 回退到系统 DNS
    log.info(f"[DoH Fallback] Using system DNS for {hostname}")
    try:
        loop = asyncio.get_event_loop()
        infos = await loop.getaddrinfo(hostname, None, family=socket.AF_INET)
        if infos:
            ip = infos[0][4][0]
            dns_cache[hostname] = {'ip': ip, 'timestamp': time.time()}
            return ip
    except Exception as e:
        log.error(f"[System DNS Failed] {hostname}: {e}")

    raise RuntimeError(f"Failed to resolve {hostname}")


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def parse_address(addr: str) -> tuple:
    if addr.startswith('['):
        end = addr.index(']')
        return addr[1:end], int(addr[end + 2:])
    sep = addr.rfind(':')
    return addr[:sep], int(addr[sep + 1:])


def is_cf_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(k in msg for k in (
        'proxy request', 'cannot connect', 'econnrefused', 'etimedout',
        'connection refused', 'timed out'
    ))


# ── WebSocket 会话处理 ────────────────────────────────────────────────────────

async def handle_session(ws: web.WebSocketResponse):
    remote_reader = None
    remote_writer = None
    is_closed = False
    pump_task = None

    async def cleanup():
        nonlocal is_closed, remote_reader, remote_writer, pump_task
        if is_closed:
            return
        is_closed = True

        if pump_task and not pump_task.done():
            pump_task.cancel()

        if remote_writer:
            try:
                remote_writer.close()
                await remote_writer.wait_closed()
            except Exception:
                pass
            remote_writer = None
            remote_reader = None

        if not ws.closed:
            try:
                await ws.close(code=1000, message=b'Server closed')
            except Exception:
                pass

    async def pump_remote_to_ws():
        try:
            while not is_closed and remote_reader:
                data = await remote_reader.read(65536)
                if not data:
                    break
                if not ws.closed:
                    await ws.send_bytes(data)
        except Exception:
            pass

        if not is_closed:
            try:
                await ws.send_str('CLOSE')
            except Exception:
                pass
            await cleanup()

    async def connect_to_remote(target_addr: str, first_frame_data: str):
        nonlocal remote_reader, remote_writer, pump_task

        host, port = parse_address(target_addr)
        attempts = [None] + CF_FALLBACK_IPS

        for i, fallback in enumerate(attempts):
            target_host = fallback if fallback else host
            try:
                resolved = target_host
                if not is_ip(target_host):
                    try:
                        resolved = await resolve_doh(target_host)
                        log.info(f"[Connect] {target_host} resolved to {resolved}")
                    except Exception as e:
                        log.error(f"[DNS Error] Failed to resolve {target_host}: {e}")
                        # 解析失败仍尝试直接连接

                remote_reader, remote_writer = await asyncio.wait_for(
                    asyncio.open_connection(resolved, port),
                    timeout=10
                )

                if first_frame_data:
                    remote_writer.write(first_frame_data.encode())
                    await remote_writer.drain()

                await ws.send_str('CONNECTED')
                pump_task = asyncio.create_task(pump_remote_to_ws())
                return

            except Exception as e:
                if remote_writer:
                    try:
                        remote_writer.close()
                    except Exception:
                        pass
                remote_reader = remote_writer = None

                if not is_cf_error(e) or i == len(attempts) - 1:
                    raise

    async for msg in ws:
        if is_closed:
            break

        try:
            if msg.type == aiohttp.WSMsgType.TEXT:
                message: str = msg.data

                if message.startswith('CONNECT:'):
                    sep = message.index('|', 8)
                    await connect_to_remote(message[8:sep], message[sep + 1:])

                elif message.startswith('DATA:'):
                    if remote_writer:
                        remote_writer.write(message[5:].encode())
                        await remote_writer.drain()

                elif message == 'CLOSE':
                    break

            elif msg.type == aiohttp.WSMsgType.BINARY:
                # 原版: data instanceof Buffer -> remoteSocket.write(data)
                if remote_writer:
                    remote_writer.write(msg.data)
                    await remote_writer.drain()

            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break

        except Exception as e:
            try:
                await ws.send_str(f'ERROR:{e}')
            except Exception:
                pass
            break

    await cleanup()


# ── HTTP 路由 ─────────────────────────────────────────────────────────────────

async def http_handler(request: web.Request):
    # WebSocket 升级
    if request.headers.get('Upgrade', '').lower() == 'websocket':
        proto = request.headers.get('Sec-WebSocket-Protocol', '')
        if TOKEN and proto != TOKEN:
            return web.Response(text='Unauthorized', status=401)

        ws = web.WebSocketResponse(protocols=[TOKEN] if TOKEN else ())
        await ws.prepare(request)
        await handle_session(ws)
        return ws

    path = request.path

    if path == '/':
        return web.Response(text='Hello-world', status=200,
                            content_type='text/plain')

    if path == '/stats':
        return web.Response(
            text=json.dumps({
                'cacheSize': len(dns_cache),
                'dohServers': DOH_SERVERS,
            }),
            content_type='application/json',
            status=200,
        )

    return web.Response(text='Not Found', status=404)


# ── 启动 ──────────────────────────────────────────────────────────────────────

async def main():
    app = web.Application()
    app.router.add_route('GET', '/{path_info:.*}', http_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    log.info(f"Web listening on port {PORT}")
    log.info(f"Token authentication: {'enabled' if TOKEN else 'disabled'}")
    log.info(f"DoH Servers: {', '.join(DOH_SERVERS)}")
    log.info(f"DNS Cache TTL: {DNS_CACHE_TTL}s")

    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())
