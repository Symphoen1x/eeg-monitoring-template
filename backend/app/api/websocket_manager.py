"""
WebSocket Manager
Manages WebSocket connections for real-time data streaming
Week 3, Monday - Enhanced for EEG Data Relay
"""

from fastapi import WebSocket
from typing import Dict, Set
from uuid import UUID
import json
import asyncio


class ConnectionManager:
    """
    WebSocket connection manager for handling multiple client connections
    Supports broadcasting to specific sessions or all connections
    """
    
    def __init__(self):
        # Active WebSocket connections: {session_id: set of WebSocket connections}
        self.session_connections: Dict[str, Set[WebSocket]] = {}
        
        # General connections (not session-specific)
        self.general_connections: Set[WebSocket] = set()
    
    @property
    def active_connections(self) -> Dict[str, Set[WebSocket]]:
        """Legacy property for backwards compatibility"""
        return self.session_connections
    
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection to accept
            session_id: Optional session ID (as string) to associate connection with
        """
        await websocket.accept()
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(websocket)
        else:
            self.general_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str = None):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
            session_id: Optional session ID (as string) the connection was associated with
        """
        if session_id and session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            # Clean up empty session sets
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        else:
            self.general_connections.discard(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send message to a specific WebSocket connection
        
        Args:
            message: Message to send (string or JSON)
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def send_json(self, data: dict, websocket: WebSocket):
        """
        Send JSON data to a specific WebSocket connection
        
        Args:
            data: Dictionary to send as JSON
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"Error sending JSON: {e}")
    
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """
        Broadcast message to all connections for a specific session
        
        Args:
            session_id: Session ID (as string) to broadcast to
            message: Message to broadcast (as dict, will be JSON encoded)
        """
        if session_id not in self.session_connections:
            return
        
        # Get all connections for this session
        connections = self.session_connections[session_id].copy()
        
        # Send to all connections, remove dead ones
        dead_connections = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to session {session_id}: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for dead_conn in dead_connections:
            self.disconnect(dead_conn, session_id)
    
    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to all active connections
        
        Args:
            message: Message to broadcast (as dict, will be JSON encoded)
        """
        # Broadcast to all session connections
        all_connections = set()
        for session_connections_set in self.session_connections.values():
            all_connections.update(session_connections_set)
        
        # Add general connections
        all_connections.update(self.general_connections)
        
        # Send to all connections, track dead ones
        dead_connections = set()
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to all: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections (need to find which session they belong to)
        for dead_conn in dead_connections:
            # Check session connections
            for session_id, connections in list(self.session_connections.items()):
                if dead_conn in connections:
                    self.disconnect(dead_conn, session_id)
                    break
            # Check general connections
            if dead_conn in self.general_connections:
                self.disconnect(dead_conn)
    
    def get_session_connection_count(self, session_id: str) -> int:
        """
        Get number of active connections for a session
        
        Args:
            session_id: Session ID (as string) to check
        
        Returns:
            Number of active connections
        """
        return len(self.session_connections.get(session_id, set()))
    
    def get_total_connections(self) -> int:
        """
        Get total number of active connections
        
        Returns:
            Total connection count
        """
        session_count = sum(len(conns) for conns in self.session_connections.values())
        return session_count + len(self.general_connections)


# Global connection manager instance
manager = ConnectionManager()
