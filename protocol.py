import struct
from enum import IntEnum


class PacketType(IntEnum):
    COMMAND = 1
    RESPONSE = 2
    FILE = 3
    ERROR = 4


def send_packet(sock, packet_type: PacketType, data: bytes | str) -> None:
    if isinstance(data, str):
        data = data.encode()

    header = struct.pack(
        "!BI",
        packet_type,
        len(data)
    )

    sock.sendall(header + data)


def recv_exact(sock, size: int) -> bytes:
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        if not chunk:
            raise ConnectionError("Connection closed")

        data += chunk

    return data


def recv_packet(sock):
    header = recv_exact(sock, 5)

    packet_type, length = struct.unpack(
        "!BI",
        header
    )

    data = recv_exact(sock, length)

    return PacketType(packet_type), data
