from asyncio_socks_server import Server
import os

Server(
    host="127.0.0.1",
    port=int(os.environ.get("PORT", 10000))
).run()
