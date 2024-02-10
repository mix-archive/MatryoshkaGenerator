from argparse import ArgumentParser
from base64 import encodebytes
from logging import basicConfig, getLogger
from socket import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
from uuid import uuid4

from rich.logging import RichHandler

from .encode import encode

banner = r"""
              _                        _     _                _          
  /\/\   __ _| |_ _ __ _   _  ___  ___| |__ | | ____ _  /\/\ (_)___  ___ 
 /    \ / _` | __| '__| | | |/ _ \/ __| '_ \| |/ / _` |/    \| / __|/ __|
/ /\/\ \ (_| | |_| |  | |_| | (_) \__ \ | | |   < (_| / /\/\ \ \__ \ (__ 
\/    \/\__,_|\__|_|   \__, |\___/|___/_| |_|_|\_\__,_\/    \/_|___/\___|
                       |___/                                             
"""  # noqa:W291

basicConfig(level="INFO", handlers=[RichHandler()])
logger = getLogger(__name__)


class MatryoshkaHandler(BaseRequestHandler):
    request: socket

    @property
    def flag(self) -> str:
        return getattr(self.server, "flag")

    @property
    def rounds(self) -> int:
        return getattr(self.server, "rounds")

    def send(self, text: str, newline: bool = True):
        self.request.sendall(text.encode() + (b"\n" if newline else b""))

    def recv(self, buffer_size: int = 1024, timeout: int = 20):
        self.request.settimeout(timeout)
        received = b""
        while True:
            try:
                data = self.request.recv(buffer_size)
            except TimeoutError:
                return
            received += data
            if len(data) < buffer_size:
                break
        return received

    def handle(self):
        logger.info("Connection from %s", self.client_address)

        self.send(banner)
        self.send("Welcome to the Matryoshka server!")
        self.send('Please send "encode" to receive the encoded message')
        if self.request.recv(1024).strip() != b"encode":
            self.send("Invalid input")
            return

        for round in range(self.rounds):
            self.send(f"Round {round + 1}/{self.rounds}")
            self.send("Please wait for the message to be prepared")
            temp_flag = "temp_flag{%s}" % uuid4()
            try:
                encoded = encode(temp_flag.encode())
            except Exception:
                logger.exception("encoding failed for client %s", self.client_address)
                self.send("Internal failure occurred, please report to author")
                return
            if encoded is None:
                logger.error("encoding failed for client %s", self.client_address)
                self.send("Internal failure occurred, please report to author")
                return
            self.send("-----BEGIN MATRYOSHKA MESSAGE-----")
            self.send(encodebytes(encoded).decode())
            self.send("-----END MATRYOSHKA MESSAGE-----")

            self.send('Flag format is "temp_flag{uuid4()}"')
            self.send("Please send the flag in 60 seconds timeout")
            received = self.recv(timeout=60)
            if received is None:
                self.send("Timeout occurred")
                return
            if temp_flag not in received.decode():
                self.send("Invalid flag")
                return
            logger.info(
                "user %s passed round %s/%s",
                self.client_address,
                round + 1,
                self.rounds,
            )
        self.send(f"Congratulations! Here is your flag: {self.flag}")

    def finish(self) -> None:
        logger.info("Connection from %s closed", self.client_address)
        return super().finish()


parser = ArgumentParser()
parser.add_argument("--port", type=int, default=0, help="Port to bind the server to")
parser.add_argument(
    "--host", type=str, default="0.0.0.0", help="Server listening address"
)
parser.add_argument(
    "--rounds", type=int, default=10, help="Number of rounds to produce temp flag"
)
parser.add_argument("--flag", type=str, required=True, help="Flag to be encoded")
parser.add_argument("--log-level", type=str, default="INFO", help="Log level")


def main():
    args = parser.parse_args()
    basicConfig(level=args.log_level, handlers=[RichHandler()])
    listen_address = (args.host, args.port)
    with ThreadingTCPServer(listen_address, MatryoshkaHandler) as server:
        logger.info("Server started at %s:%s", *server.server_address)
        server.allow_reuse_address = True
        server.allow_reuse_port = True
        setattr(server, "rounds", args.rounds)
        setattr(server, "flag", args.flag)
        server.serve_forever()
    return


if __name__ == "__main__":
    main()
