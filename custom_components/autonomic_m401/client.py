from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from .const import SOURCE_FROM_CODE, SOURCE_MAP

_LOGGER = logging.getLogger(__name__)

class AutonomicClient:
    """Local TCP client for the Autonomic M401/M400-style ASCII-hex protocol."""

    def __init__(self, host: str, port: int, zones: list[int]):
        self.host = host
        self.port = port
        self.zones = zones

        self.reader = None
        self.writer = None
        self._lock = asyncio.Lock()
        self._poll_task = None
        self._listeners = []

        self.state = {
            z: {
                "power": False,
                "mute": False,
                "volume": 0,
                "source": "S1",
            }
            for z in zones
        }

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        with suppress(ValueError):
            self._listeners.remove(callback)

    async def start(self):
        self._poll_task = asyncio.create_task(self._poll_loop())
        # Initial refresh is deliberately best-effort.
        with suppress(Exception):
            await self.refresh()

    async def stop(self):
        if self._poll_task:
            self._poll_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._poll_task
        await self.close()

    async def connect(self):
        if self.writer is None or self.writer.is_closing():
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def close(self):
        if self.writer:
            self.writer.close()
            with suppress(Exception):
                await self.writer.wait_closed()
        self.reader = None
        self.writer = None

    async def _write(self, command: str):
        await self.connect()
        self.writer.write((command.upper() + "\n").encode("ascii"))
        await self.writer.drain()

    @staticmethod
    def _parse_line(line: bytes):
        text = line.decode("ascii", errors="ignore").strip().upper()
        # Commands are ASCII hex strings, normally 6+ characters.
        if len(text) < 6:
            return None
        try:
            return bytes.fromhex(text)
        except ValueError:
            return None

    async def _query(self, command: int, zone: int, timeout=1.0):
        """Send a request without data and wait for a matching response.

        The amplifier protocol treats incomplete commands as data requests.
        We ignore unrelated echoed notifications and wait for the requested
        command/zone response.
        """
        wanted = bytes((command, zone))
        async with self._lock:
            await self._write(f"{command:02X}{zone:02X}")
            end = asyncio.get_running_loop().time() + timeout
            while True:
                remaining = end - asyncio.get_running_loop().time()
                if remaining <= 0:
                    return None
                try:
                    raw = await asyncio.wait_for(self.reader.readline(), remaining)
                except asyncio.TimeoutError:
                    return None
                packet = self._parse_line(raw)
                if packet and packet[:2] == wanted:
                    return packet[2:]

    async def _send(self, command: int, zone: int, data: int):
        async with self._lock:
            await self._write(f"{command:02X}{zone:02X}{data:02X}")

    async def set_power(self, zone: int, on: bool):
        await self._send(0x01, zone, 0x01 if on else 0x00)
        self.state[zone]["power"] = on
        self._notify(zone)

    async def set_mute(self, zone: int, muted: bool):
        await self._send(0x02, zone, 0x00 if muted else 0x01)
        self.state[zone]["mute"] = muted
        self._notify(zone)

    async def set_source(self, zone: int, source: str):
        code = SOURCE_MAP[source]
        await self._send(0x03, zone, code)
        self.state[zone]["source"] = source
        self._notify(zone)

    async def set_volume(self, zone: int, volume: int):
        volume = max(0, min(100, int(volume)))
        # Protocol's A0 range is 0x00..0xA0; the manual's specification
        # identifies 100 as full volume. Convert HA's 0..100 to that range.
        raw = round(volume * 0xA0 / 100)
        await self._send(0x04, zone, raw)
        self.state[zone]["volume"] = volume
        self._notify(zone)

    async def refresh_zone(self, zone: int):
        # Power, mute, source and volume are all queryable by sending the
        # command without its data byte.
        queries = (
            ("power", 0x01),
            ("mute", 0x02),
            ("source", 0x03),
            ("volume", 0x04),
        )
        for key, command in queries:
            try:
                data = await self._query(command, zone)
                if not data:
                    continue
                value = data[0]
                if key == "power" and value in (0x00, 0x01):
                    self.state[zone]["power"] = value == 0x01
                elif key == "mute" and value in (0x00, 0x01):
                    self.state[zone]["mute"] = value == 0x00
                elif key == "source":
                    self.state[zone]["source"] = SOURCE_FROM_CODE.get(value, f"S? ({value:02X})")
                elif key == "volume":
                    self.state[zone]["volume"] = round(value * 100 / 0xA0)
            except (OSError, asyncio.TimeoutError) as err:
                _LOGGER.debug("Autonomic zone %s query failed: %s", zone, err)
                await self.close()
        self._notify(zone)

    async def refresh(self):
        for zone in self.zones:
            await self.refresh_zone(zone)

    async def _poll_loop(self):
        while True:
            try:
                await asyncio.sleep(3)
                await self.refresh()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.debug("Autonomic polling failed: %s", err)
                await self.close()

    def _notify(self, zone):
        for callback in tuple(self._listeners):
            callback(zone)
