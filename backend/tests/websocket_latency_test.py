"""
WebSocket Latency Testing Script
Week 3, Tuesday - WebSocket Performance Testing

Tests the /ws/ping endpoint to measure round trip time
"""

import asyncio
import websockets
import json
from datetime import datetime
import statistics

async def test_websocket_latency(url: str = "ws://localhost:8000/api/v1/ws/ping", num_pings: int = 100):
    """
    Test WebSocket latency by sending ping messages
    
    Args:
        url: WebSocket endpoint URL
        num_pings: Number of pings to send
    """
    latencies = []
    
    async with websockets.connect(url) as websocket:
        # Wait for ready message
        ready = await websocket.recv()
        print(f"Server ready: {ready}\n")
        
        print(f"Sending {num_pings} pings...")
        
        for i in range(num_pings):
            # Send ping with timestamp
            client_timestamp = datetime.utcnow().isoformat()
            ping_message = {
                "type": "ping",
                "client_timestamp": client_timestamp
            }
            
            send_time = datetime.utcnow()
            await websocket.send(json.dumps(ping_message))
            
            # Receive pong
            pong = await websocket.recv()
            receive_time = datetime.utcnow()
            
            # Calculate latency
            latency_ms = (receive_time - send_time).total_seconds() * 1000
            latencies.append(latency_ms)
            
            # Print progress every 10 pings
            if (i + 1) % 10 == 0:
                print(f"  Ping {i + 1}/{num_pings}: {latency_ms:.2f}ms")
        
        # Calculate statistics
        print("\n" + "=" * 60)
        print("LATENCY STATISTICS")
        print("=" * 60)
        print(f"Total pings:        {num_pings}")
        print(f"Min latency:        {min(latencies):.2f}ms")
        print(f"Max latency:        {max(latencies):.2f}ms")
        print(f"Average latency:    {statistics.mean(latencies):.2f}ms")
        print(f"Median latency:     {statistics.median(latencies):.2f}ms")
        print(f"Std deviation:      {statistics.stdev(latencies):.2f}ms")
        print("=" * 60)

if __name__ == "__main__":
    try:
        print("WebSocket Latency Test")
        print("-" * 60)
        asyncio.run(test_websocket_latency())
    except Exception as e:
        print(f"Error: {e}")
