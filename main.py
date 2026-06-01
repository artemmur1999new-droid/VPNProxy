from asyncio_socks_server import Server

Server(
    host="127.0.0.1",
    port=10001
).run()