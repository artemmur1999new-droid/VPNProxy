import socket
import threading
import socks
import socks5serv

socks5 = "34.84.162.206:38081"
proxy = "127.0.0.1:10000"

proxy_host, proxy_port = proxy.split(":")
proxy_port = int(proxy_port)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((proxy_host, proxy_port))
server.listen(100)

print(f"Proxy listening on {proxy_host}:{proxy_port}")


def relay(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.shutdown(socket.SHUT_RDWR)
        except:
            pass

        try:
            dst.shutdown(socket.SHUT_RDWR)
        except:
            pass

        try:
            src.close()
        except:
            pass

        try:
            dst.close()
        except:
            pass


def handle_client(client):
    try:
        request = client.recv(8192)

        if not request:
            client.close()
            return

        first_line = request.split(b"\r\n", 1)[0].decode(
            "utf-8",
            errors="ignore"
        )

        print(first_line)

        if not first_line.startswith("CONNECT "):
            client.sendall(
                b"HTTP/1.1 405 Method Not Allowed\r\n"
                b"Connection: close\r\n\r\n"
            )
            client.close()
            return

        target = first_line.split()[1]

        if ":" in target:
            host, port = target.rsplit(":", 1)
            port = int(port)
        else:
            host = target
            port = 443

        socks5_host, socks5_port = socks5.split(":")
        socks5_port = int(socks5_port)

        remote = socks.socksocket()
        remote.set_proxy(
            socks.SOCKS5,
            socks5_host,
            socks5_port
        )

        remote.settimeout(15)
        remote.connect((host, port))

        client.sendall(
            b"HTTP/1.1 200 Connection Established\r\n"
            b"Proxy-Agent: PythonProxy\r\n\r\n"
        )

        threading.Thread(
            target=relay,
            args=(client, remote),
            daemon=True
        ).start()

        threading.Thread(
            target=relay,
            args=(remote, client),
            daemon=True
        ).start()

    except Exception as e:
        print("Error:", e)

        try:
            client.sendall(
                b"HTTP/1.1 502 Bad Gateway\r\n"
                b"Connection: close\r\n\r\n"
            )
        except:
            pass

        try:
            client.close()
        except:
            pass


while True:
    client, addr = server.accept()

    threading.Thread(
        target=handle_client,
        args=(client,),
        daemon=True
    ).start()