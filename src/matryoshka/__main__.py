import re
from argparse import ArgumentParser
from base64 import encodebytes
from logging import getLogger
from os import environ
from socket import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import Optional
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

logger = getLogger(__name__)


class MatryoshkaHandler(BaseRequestHandler):
    request: socket
    name: Optional[str] = None

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
        logger.info("Connection from %s:%s", *self.client_address)

        self.send(banner)
        self.send("Welcome to the Matryoshka server!")
        self.send("Please send your name to receive the flag")
        if (name := self.recv(timeout=10)) is None:
            self.send("Invalid input")
            return
        self.name = name = re.sub(r"[^a-zA-Z0-9]", "", name.decode(errors="replace"))
        if not name:
            self.send("Invalid name")
            return
        logger.info("Client (%s:%s) identified as %r", *self.client_address, name)
        self.send(f"Hello {name}!")

        for round in range(self.rounds):
            self.send(f"Round {round + 1}/{self.rounds}")
            self.send("Please wait for the message to be prepared")
            temp_flag = "%s_flag{%s}" % (name, uuid4())
            try:
                encoded = encode(temp_flag.encode())
            except Exception:
                logger.exception("encoding failed for user %r", name)
                self.send("Internal failure occurred, please report to author")
                return
            if encoded is None:
                logger.error("encoding failed for client %r", name)
                self.send("Internal encoding result invalid, please report to author")
                return
            self.send("-----BEGIN MATRYOSHKA MESSAGE-----")
            self.send(encodebytes(encoded).decode(), newline=False)
            self.send("-----END MATRYOSHKA MESSAGE-----")

            self.send('Flag format is "%s_flag{uuid4()}"' % name)
            self.send("Please send the flag in 60 seconds timeout")
            received = self.recv(timeout=60)
            if received is None:
                self.send("Timeout occurred")
                return
            if temp_flag not in received.decode():
                self.send("Invalid flag")
                return
            logger.info(
                "user %r passed round %s/%s",
                name,
                round + 1,
                self.rounds,
            )
        self.send(f"Congratulations! Here is your flag: {self.flag}")

    def finish(self) -> None:
        logger.info(
            "Connection from %r (%s:%s) closed", self.name, *self.client_address
        )
        return super().finish()


parser = ArgumentParser()
parser.add_argument(
    "-p", "--port", type=int, default=1337, help="Port to bind the server to"
)
parser.add_argument(
    "-l", "--host", type=str, default="0.0.0.0", help="Server listening address"
)
parser.add_argument(
    "-r", "--rounds", type=int, default=25, help="Number of rounds to produce temp flag"
)
if flag := environ.get("FLAG"):
    parser.add_argument(
        "-f", "--flag", type=str, default=flag, help="Flag to be encoded"
    )
else:
    parser.add_argument(
        "-f", "--flag", type=str, required=True, help="Flag to be encoded"
    )
parser.add_argument("-L", "--log-level", type=str, default="INFO", help="Log level")


def main():
    args = parser.parse_args()

    root_logger = getLogger()
    root_logger.setLevel(args.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(RichHandler())

    logger.debug("Starting server with args %s", args)
    with ThreadingTCPServer(
        (args.host, args.port), MatryoshkaHandler, bind_and_activate=False
    ) as server:
        logger.info("Server started at %s:%s", *server.server_address)
        server.allow_reuse_address = True
        server.allow_reuse_port = True
        setattr(server, "rounds", args.rounds)
        setattr(server, "flag", args.flag)
        try:
            server.server_bind()
            server.server_activate()
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped")
        except Exception as e:
            logger.exception("Failed to start server, %s", e)
    return


if __name__ == "__main__":
    main()
