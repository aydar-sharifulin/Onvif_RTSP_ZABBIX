#!/usr/bin/env python3

"""
Zabbix LLD discovery of IP cameras by an open TCP port.

Usage:
    camdiscover.py "<CIDR[,CIDR...]>" "<PORT[,PORT...]>" "<TIMEOUT>" "<WORKERS>"

Example:
    camdiscover.py "192.168.0.0/24,192.168.1.0/24" "554" "0.5" "64"

Output:
[
  {
    "{#CAM.IP}": "192.168.0.10",
    "{#CAM.PORT}": "554"
  }
]
"""

from __future__ import annotations

import concurrent.futures
import ipaddress
import json
import socket
import sys
from dataclasses import dataclass


MAX_ADDRESSES = 65536
DEFAULT_PORTS = (554,)
DEFAULT_TIMEOUT = 0.5
DEFAULT_WORKERS = 64


@dataclass(frozen=True)
class Target:
    ip: str
    port: int


def parse_networks(raw_value: str) -> list[ipaddress.IPv4Network]:
    networks: list[ipaddress.IPv4Network] = []

    for raw_network in raw_value.split(","):
        raw_network = raw_network.strip()
        if not raw_network:
            continue

        try:
            network = ipaddress.ip_network(raw_network, strict=False)
        except ValueError as exc:
            raise ValueError(f"Invalid network '{raw_network}': {exc}") from exc

        if network.version != 4:
            raise ValueError(f"IPv6 network is not supported: {raw_network}")

        networks.append(network)

    if not networks:
        raise ValueError("No valid discovery networks specified")

    return networks


def parse_ports(raw_value: str) -> tuple[int, ...]:
    if not raw_value.strip():
        return DEFAULT_PORTS

    ports: set[int] = set()

    for raw_port in raw_value.split(","):
        raw_port = raw_port.strip()
        if not raw_port:
            continue

        try:
            port = int(raw_port)
        except ValueError as exc:
            raise ValueError(f"Invalid TCP port: {raw_port}") from exc

        if not 1 <= port <= 65535:
            raise ValueError(f"TCP port is outside 1-65535: {port}")

        ports.add(port)

    if not ports:
        raise ValueError("No valid TCP ports specified")

    return tuple(sorted(ports))


def build_targets(
    networks: list[ipaddress.IPv4Network],
    ports: tuple[int, ...],
) -> list[Target]:
    addresses: set[str] = set()

    for network in networks:
        for address in network.hosts():
            addresses.add(str(address))

            if len(addresses) > MAX_ADDRESSES:
                raise ValueError(
                    f"Discovery range exceeds the limit of {MAX_ADDRESSES} addresses"
                )

    return [
        Target(ip=ip, port=port)
        for ip in sorted(addresses, key=ipaddress.ip_address)
        for port in ports
    ]


def port_is_open(target: Target, timeout: float) -> Target | None:
    try:
        with socket.create_connection(
            (target.ip, target.port),
            timeout=timeout,
        ):
            return target
    except (TimeoutError, ConnectionRefusedError, OSError):
        return None


def main() -> int:
    if len(sys.argv) < 2:
        raise ValueError(
            "Usage: camdiscover.py "
            '"<CIDR[,CIDR...]>" ["<PORT[,PORT...]>"] ["<TIMEOUT>"] ["<WORKERS>"]'
        )

    networks = parse_networks(sys.argv[1])
    ports = parse_ports(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_PORTS

    timeout = float(sys.argv[3]) if len(sys.argv) >= 4 else DEFAULT_TIMEOUT
    workers = int(sys.argv[4]) if len(sys.argv) >= 5 else DEFAULT_WORKERS

    if not 0.05 <= timeout <= 10:
        raise ValueError("Timeout must be between 0.05 and 10 seconds")

    if not 1 <= workers <= 256:
        raise ValueError("Workers must be between 1 and 256")

    targets = build_targets(networks, ports)
    discovered: dict[str, int] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(port_is_open, target, timeout)
            for target in targets
        ]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                # For multiple open ports, use the lowest matching port.
                discovered.setdefault(result.ip, result.port)

    output = [
        {
            "{#CAM.IP}": ip,
            "{#CAM.PORT}": str(discovered[ip]),
        }
        for ip in sorted(discovered, key=ipaddress.ip_address)
    ]

    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
