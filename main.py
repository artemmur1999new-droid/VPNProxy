import socket
import threading
import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 10000))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

print(f"Proxy listening on {HOST}:{PORT}")


def relay(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                s.close()
            except:
                pass


def handle_client(client):
    try:
        request = client.recv(8192)
        if not request:
            client.close()
            return

        first_line = request.split(b"\r\n", 1)[0].decode("utf-8", errors="ignore")
        print(first_line)

        # Только HTTPS CONNECT
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

        # Подключаемся напрямую (без PySocks!)
        remote = socket.create_connection((host, port), timeout=15)

        client.sendall(
            b"HTTP/1.1 200 Connection Established\r\n"
            b"Proxy-Agent: PythonProxy\r\n\r\n"
        )

        threading.Thread(target=relay, args=(client, remote), daemon=True).start()
        threading.Thread(target=relay, args=(remote, client), daemon=True).start()

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
    threading.Thread(target=handle_client, args=(client,), daemon=True).start()