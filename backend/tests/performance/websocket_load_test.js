// k6 WebSocket Load Test
// Week 3, Tuesday - Performance Testing
// Tests /ws/ping endpoint with multiple concurrent connections

import ws from 'k6/ws';
import { check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics
const pingCount = new Counter('pings_sent');
const pongCount = new Counter('pongs_received');
const latency = new Trend('websocket_latency_ms');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 connections
    { duration: '1m', target: 10 },    // Stay at 10 connections
    { duration: '30s', target: 50 },   // Ramp up to 50 connections
    { duration: '1m', target: 50 },    // Stay at 50 connections
    { duration: '30s', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    'websocket_latency_ms': ['p(95)<50'],  // 95% of pings should be under 50ms
    'pongs_received': ['count>0'],
  },
};

export default function () {
  const url = 'ws://localhost:8000/api/v1/ws/ping';
  
  const response = ws.connect(url, function (socket) {
    socket.on('open', function () {
      console.log('WebSocket connection established');
    });

    socket.on('message', function (message) {
      const data = JSON.parse(message);
      
      if (data.type === 'ready') {
        console.log('Server ready, starting pings...');
        
        // Send 10 pings per connection
        for (let i = 0; i < 10; i++) {
          const startTime = Date.now();
          
          socket.send(JSON.stringify({
            type: 'ping',
            client_timestamp: new Date().toISOString()
          }));
          
          pingCount.add(1);
          
          // Wait for pong (handled by on('message'))
          socket.setTimeout(function () {
            const endTime = Date.now();
            const rtt = endTime - startTime;
            latency.add(rtt);
            pongCount.add(1);
          }, 0);
        }
        
        // Close connection after pings
        socket.setTimeout(function () {
          socket.close();
        }, 1000);
        
      } else if (data.type === 'pong') {
        // Pong received
        check(data, {
          'has client_timestamp': (r) => r.client_timestamp !== undefined,
          'has server_timestamp': (r) => r.server_timestamp !== undefined,
        });
      }
    });

    socket.on('error', function (e) {
      console.log('WebSocket error:', e);
    });
  });

  check(response, {
    'WebSocket connection successful': (r) => r && r.status === 101,
  });
}
