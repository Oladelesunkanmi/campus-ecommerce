import os
import httpx

client: httpx.AsyncClient | None = None

HTTP_TIMEOUT_S = float(os.environ.get("HTTP_TIMEOUT_S", 10.0))
HTTP_MAX_CONNECTIONS = int(os.environ.get("HTTP_MAX_CONNECTIONS", 50))
HTTP_MAX_KEEPALIVE = int(os.environ.get("HTTP_MAX_KEEPALIVE", 20))


async def init():
    global client
    limits = httpx.Limits(max_connections=HTTP_MAX_CONNECTIONS, max_keepalive_connections=HTTP_MAX_KEEPALIVE)
    client = httpx.AsyncClient(timeout=HTTP_TIMEOUT_S, limits=limits)


async def close():
    global client
    if client is not None:
        await client.aclose()
        client = None
