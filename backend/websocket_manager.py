import json
from typing import List, Dict, Any
from fastapi import WebSocket
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial welcome and status packet
        await websocket.send_json({
            "event": "connection_established",
            "data": {
                "message": "Connected to Clear Vision Real-Time Live Stream",
                "connected_clients": len(self.active_connections),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: Dict[str, Any]):
        """Broadcasts an event with payload to all connected clients."""
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                to_remove.append(connection)

        for dead_conn in to_remove:
            self.disconnect(dead_conn)

    async def broadcast_scraper_log(self, job_id: str, message: str, level: str = "info", progress_pct: int = 0):
        await self.broadcast("scraper_log", {
            "job_id": job_id,
            "message": message,
            "level": level,
            "progress_pct": progress_pct,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    async def broadcast_new_review(self, review: Dict[str, Any]):
        await self.broadcast("new_review", {
            "review": review,
            "message": f"New {review.get('rating')}★ review received from {review.get('name')} on {review.get('platform')}."
        })

    async def broadcast_review_updated(self, review: Dict[str, Any]):
        await self.broadcast("review_updated", {
            "review": review
        })

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        await self.broadcast("stats_updated", {
            "stats": stats
        })

ws_manager = WebSocketManager()
