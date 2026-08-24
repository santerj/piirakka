"""Background tasks for the application."""

import asyncio
from datetime import datetime

from piirakka.model.device import BluetoothDevice
from piirakka.model.recent_track import RecentTrack
from piirakka.services.bluetooth import BluetoothDeviceScanner


async def observe_current_track(context, track_history, interval: int = 1) -> None:
    """Observe player for track changes and push updates.

    Args:
    context: The application Context (for player access and pushing changes)
    track_history: TrackHistoryManager instance
    interval: Poll interval in seconds

    """
    while True:
        await asyncio.sleep(interval)
        current_track_title = context.player.current_track()
        if current_track_title is None:
            continue

        current_track = RecentTrack(
            title=current_track_title,
            station=context.player.current_station.name,
            timestamp=datetime.now().strftime("%H:%M"),
        )

        # Push track if history is empty or current track differs from most recent
        if not track_history or track_history.most_recent().title != current_track_title:
            await context.push_track(current_track)


async def background_bluetooth_scan(context, interval: int = 10) -> list[BluetoothDevice]:
    """
    Scan bluetooth devices periodically to have a list of options ready for the users.

    Args
    ----
    context: The application context for storing state
    interval: the period for running a background scan

    """
    scanner = BluetoothDeviceScanner()

    while True:
        devices = await scanner.scan(timeout_seconds=5)
        context.available_bluetooth_devices = devices
        await asyncio.sleep(interval)
