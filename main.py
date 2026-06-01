import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)

PORT = int(os.environ.get("PORT", 10000))


async def read_headers(reader):
    header = b""
    while b"\r\n\r\n" not in header:
        chunk = await reader.read(1024)
        if not chunk:
            break
        header += chunk
    return header


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def handle_client(reader, writer):
    try:
        raw = await read_headers(reader)
        if not raw:
            writer.close()
            return

        request_line = raw.split(b"\r\n", 1)[0].decode(errors="ignore")
        logging.info(f"REQ: {request_line}")

        if not request_line.startswith("CONNECT"):
            writer.write(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            await writer.drain()
            writer.close()
            return

        target = request_line.split(" ")[1]
        host, port = target.split(":")
        port = int(port)

        remote_reader, remote_writer = await asyncio.open_connection(host, port)

        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        await asyncio.gather(
            pipe(reader, remote_writer),
            pipe(remote_reader, writer)
        )

    except Exception as e:
        logging.error(f"ERR: {e}")
        try:
            writer.close()
        except:
            pass


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", PORT)
    logging.info(f"Proxy running on {PORT}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
