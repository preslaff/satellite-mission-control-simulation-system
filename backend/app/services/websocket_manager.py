"""
WebSocket Connection Manager
Handles real-time satellite position updates and alerts
"""

import asyncio
import json
from typing import Dict, Set, List
from datetime import datetime
from fastapi import WebSocket
from app.services.satellite_fetcher import satellite_fetcher


class WebSocketManager:
    """Manages WebSocket connections and broadcasts satellite updates"""

    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Tracked satellites per connection: {connection_id: Set[norad_id]}
        self.tracked_satellites: Dict[str, Set[int]] = {}

        # Update interval in seconds
        self.update_interval = 1.0

        # Background task for broadcasting updates
        self.broadcast_task = None

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.tracked_satellites[connection_id] = set()
        print(f"WebSocket connected: {connection_id}")

        # Start broadcast task if not running
        if self.broadcast_task is None or self.broadcast_task.done():
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())

    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.tracked_satellites:
            del self.tracked_satellites[connection_id]
        print(f"WebSocket disconnected: {connection_id}")

    def add_satellite(self, connection_id: str, norad_id: int):
        """Add satellite to tracking list for a connection"""
        if connection_id in self.tracked_satellites:
            self.tracked_satellites[connection_id].add(norad_id)
            print(f"Tracking satellite {norad_id} for connection {connection_id}")

    def remove_satellite(self, connection_id: str, norad_id: int):
        """Remove satellite from tracking list for a connection"""
        if connection_id in self.tracked_satellites:
            self.tracked_satellites[connection_id].discard(norad_id)
            print(f"Stopped tracking satellite {norad_id} for connection {connection_id}")

    def set_satellites(self, connection_id: str, norad_ids: List[int]):
        """Set the complete list of tracked satellites for a connection"""
        if connection_id in self.tracked_satellites:
            self.tracked_satellites[connection_id] = set(norad_ids)
            print(f"Set tracked satellites for {connection_id}: {norad_ids}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                print(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def _broadcast_loop(self):
        """Background task that continuously broadcasts satellite positions"""
        print("Starting WebSocket broadcast loop...")

        while self.active_connections:
            try:
                # Collect all unique satellites being tracked
                all_tracked_satellites = set()
                for satellites in self.tracked_satellites.values():
                    all_tracked_satellites.update(satellites)

                if not all_tracked_satellites:
                    # No satellites to track, wait and continue
                    await asyncio.sleep(self.update_interval)
                    continue

                # Fetch current positions for all tracked satellites
                positions = {}
                timestamp = datetime.utcnow().isoformat()

                for norad_id in all_tracked_satellites:
                    try:
                        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)
                        if tle_data:
                            state = satellite_fetcher.propagate_position(tle_data)
                            if state:
                                positions[norad_id] = {
                                    'id': norad_id,
                                    'name': tle_data['OBJECT_NAME'],
                                    'position': state['position'],
                                    'velocity': state['velocity'],
                                    'timestamp': timestamp
                                }
                    except Exception as e:
                        print(f"Error fetching position for satellite {norad_id}: {e}")

                # Send positions to each connection (only satellites they're tracking)
                disconnected = []
                for connection_id, websocket in self.active_connections.items():
                    try:
                        # Filter positions for this connection's tracked satellites
                        tracked = self.tracked_satellites.get(connection_id, set())
                        connection_positions = {
                            sat_id: pos for sat_id, pos in positions.items()
                            if sat_id in tracked
                        }

                        if connection_positions:
                            message = {
                                'type': 'position_update',
                                'timestamp': timestamp,
                                'satellites': list(connection_positions.values())
                            }
                            await websocket.send_json(message)

                    except Exception as e:
                        print(f"Error sending updates to {connection_id}: {e}")
                        disconnected.append(connection_id)

                # Clean up disconnected clients
                for connection_id in disconnected:
                    self.disconnect(connection_id)

                # Wait before next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in broadcast loop: {e}")
                await asyncio.sleep(self.update_interval)

        print("Broadcast loop stopped (no active connections)")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
