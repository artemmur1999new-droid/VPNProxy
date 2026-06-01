import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
# Render автоматически передает номер порта в переменную окружения PORT
PORT = int(os.environ.get("PORT", 10000))

async def handle_client(reader, writer):
    try:
        # Читаем заголовки HTTP-запроса от клиента
        data = await reader.read(4096)
        if not data:
            return
            
        request = data.decode('utf-8', errors='ignore')
        lines = request.split('\r\n')
        
        # Проверяем, что это запрос метода CONNECT (туннелирование)
        if not lines[0].startswith('CONNECT'):
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await writer.drain()
            return

        # Извлекаем целевой хост и порт (например, google.com:443)
        target = lines[0].split(' ')[1]
        host, port = target.split(':')
        port = int(port)

        # Подключаемся к целевому серверу
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
        
        # Отвечаем балансировщику Render, что соединение установлено
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        # Двунаправленная пересылка сырых байтов
        async def pipe(r, w):
            try:
                while True:
                    chunk = await r.read(4096)
                    if not chunk:
                        break
                    w.write(chunk)
                    await w.drain()
            except Exception:
                pass
            finally:
                w.close()

        await asyncio.gather(pipe(reader, remote_writer), pipe(remote_reader, writer))

    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        writer.close()

async def main():
    # Запуск на порту, который требует Render (0.0.0.0 обязателен для внешней сети)
    server = await asyncio.start_server(handle_client, "0.0.0.0", PORT)
    logging.info(f"Сервер успешно запущен Render на порту {PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
