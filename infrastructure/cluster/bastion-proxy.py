import socket
import socketserver
import sys
import threading

PORTA_PERMITIDA = 443
BUFFER = 65536


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        requisicao = self.rfile.readline(BUFFER).decode("latin-1").strip()
        while self.rfile.readline(BUFFER).strip():
            pass

        partes = requisicao.split()
        if len(partes) < 2 or partes[0].upper() != "CONNECT":
            self.wfile.write(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            return

        host, _, porta = partes[1].rpartition(":")
        if not host or porta != str(PORTA_PERMITIDA):
            self.wfile.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            return

        try:
            destino = socket.create_connection((host, PORTA_PERMITIDA), timeout=10)
        except OSError:
            self.wfile.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            return

        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.wfile.flush()

        with destino:
            self.ligar(self.connection, destino)

    def ligar(self, cliente: socket.socket, destino: socket.socket) -> None:
        threads = [
            threading.Thread(target=self.encaminhar, args=(cliente, destino), daemon=True),
            threading.Thread(target=self.encaminhar, args=(destino, cliente), daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    @staticmethod
    def encaminhar(origem: socket.socket, destino: socket.socket) -> None:
        try:
            while True:
                pedaco = origem.recv(BUFFER)
                if not pedaco:
                    break
                destino.sendall(pedaco)
        except OSError:
            pass
        finally:
            try:
                destino.shutdown(socket.SHUT_WR)
            except OSError:
                pass


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    Servidor((sys.argv[1], int(sys.argv[2])), Handler).serve_forever()
