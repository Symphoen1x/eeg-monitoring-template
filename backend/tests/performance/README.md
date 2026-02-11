# Performance Testing Guide

## Overview

This directory contains performance testing scripts for the Fumorive backend API.

## Prerequisites

### Install k6

**Windows (PowerShell):**
```powershell
# Using Chocolatey
choco install k6

# Or download from https://k6.io/docs/getting-started/installation/
```

**Python WebSocket Test:**
```bash
# Install websockets library
pip install websockets
```

## Test Scripts

### 1. WebSocket Load Test (`websocket_load_test.js`)

Tests WebSocket `/ws/ping` endpoint with concurrent connections.

**Run:**
```bash
k6 run websocket_load_test.js
```

**Test Scenario:**
- Ramps up to 10 concurrent connections (30s)
- Maintains 10 connections (1min)
- Ramps up to 50 connections (30s)
- Maintains 50 connections (1min)
- Ramps down to 0 (30s)

**Success Criteria:**
- 95% of pings < 50ms latency
- All pongs received

### 2. API Load Test (`api_load_test.js`)

Tests REST API endpoints (health, EEG status, buffer stats).

**Run:**
```bash
k6 run api_load_test.js
```

**Test Scenario:**
- Ramps up to 20 RPS (30s)
- Maintains 20 RPS (2min)
- Ramps up to 50 RPS (30s)
- Maintains 50 RPS (2min)
- Ramps down to 0 (30s)

**Success Criteria:**
- 95% of requests < 200ms
- 95% success rate

### 3. WebSocket Latency Test (`../websocket_latency_test.py`)

Simple Python script to measure WebSocket latency.

**Run:**
```bash
cd ..
python websocket_latency_test.py
```

**Output:**
- Min/Max/Average/Median latency
- Standard deviation

## Running Tests

### Before Testing

1. **Start backend server:**
   ```bash
   cd ../..
   python main.py
   ```

2. **Verify server is ready:**
   ```bash
   curl http://localhost:8000/health
   ```

### Run All Tests

```bash
# WebSocket load test
k6 run websocket_load_test.js

# API load test
k6 run api_load_test.js

# Python latency test
cd ..
python websocket_latency_test.py
```

## Expected Results

### Localhost Performance

**WebSocket Latency:**
- Average: < 5ms
- 95th percentile: < 10ms

**API Response Time:**
- Average: < 20ms
- 95th percentile: < 50ms

### Interpreting Results

**Good Performance:**
- WebSocket latency < 10ms (p95)
- API requests < 100ms (p95)
- >99% success rate

**Needs Optimization:**
- WebSocket latency > 50ms (p95)
- API requests > 200ms (p95)
- <95% success rate

## Metrics Tracked

- `http_req_duration`: HTTP request duration
- `websocket_latency_ms`: WebSocket round-trip time
- `api_success_rate`: Success rate of API calls
- `pings_sent` / `pongs_received`: WebSocket ping/pong counts

## Troubleshooting

**Connection Refused:**
- Ensure backend server is running on port 8000
- Check CORS settings if testing from different origin

**High Latency:**
- Check system resources (CPU, memory)
- Verify database connection performance
- Check Redis connection latency

**Low Success Rate:**
- Check backend error logs
- Verify database can handle load
- Check timeout settings
