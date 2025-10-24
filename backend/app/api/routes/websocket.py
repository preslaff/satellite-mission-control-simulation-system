"""
WebSocket API endpoints for real-time satellite tracking
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import uuid
from app.services.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("/tracking")
async def websocket_tracking(websocket: WebSocket):
    """
    WebSocket endpoint for real-time satellite position updates

    Client sends messages:
    {
        "type": "subscribe",
        "satellites": [norad_id1, norad_id2, ...]
    }

    Server sends messages:
    {
        "type": "position_update",
        "timestamp": "2024-01-01T00:00:00",
        "satellites": [
            {
                "id": norad_id,
                "name": "Satellite Name",
                "position": {"x": ..., "y": ..., "z": ...},
                "velocity": {"vx": ..., "vy": ..., "vz": ...},
                "timestamp": "..."
            },
            ...
        ]
    }
    """
    connection_id = str(uuid.uuid4())

    await ws_manager.connect(websocket, connection_id)

    try:
        # Send welcome message
        await ws_manager.send_personal_message({
            'type': 'connected',
            'connection_id': connection_id,
            'message': 'WebSocket connected successfully'
        }, connection_id)

        # Listen for client messages
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get('type')

                if message_type == 'subscribe':
                    # Client wants to track specific satellites
                    satellites = message.get('satellites', [])
                    if isinstance(satellites, list):
                        ws_manager.set_satellites(connection_id, satellites)
                        await ws_manager.send_personal_message({
                            'type': 'subscribed',
                            'satellites': satellites,
                            'message': f'Now tracking {len(satellites)} satellites'
                        }, connection_id)

                elif message_type == 'add_satellite':
                    # Add single satellite to tracking
                    norad_id = message.get('norad_id')
                    if norad_id:
                        ws_manager.add_satellite(connection_id, norad_id)
                        await ws_manager.send_personal_message({
                            'type': 'satellite_added',
                            'norad_id': norad_id
                        }, connection_id)

                elif message_type == 'remove_satellite':
                    # Remove single satellite from tracking
                    norad_id = message.get('norad_id')
                    if norad_id:
                        ws_manager.remove_satellite(connection_id, norad_id)
                        await ws_manager.send_personal_message({
                            'type': 'satellite_removed',
                            'norad_id': norad_id
                        }, connection_id)

                elif message_type == 'ping':
                    # Keep-alive ping
                    await ws_manager.send_personal_message({
                        'type': 'pong',
                        'timestamp': message.get('timestamp')
                    }, connection_id)

                else:
                    await ws_manager.send_personal_message({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }, connection_id)

            except json.JSONDecodeError:
                await ws_manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }, connection_id)

    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error for {connection_id}: {e}")
        ws_manager.disconnect(connection_id)
