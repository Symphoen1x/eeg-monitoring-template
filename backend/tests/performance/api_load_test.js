// k6 REST API Load Test
// Week 3, Tuesday - Performance Testing
// Tests REST API endpoints (sessions, EEG, face)

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const requestCount = new Counter('api_requests');
const successRate = new Rate('api_success_rate');
const requestDuration = new Trend('api_request_duration_ms');

// Test configuration
export const options = {
    stages: [
        { duration: '30s', target: 20 },   // Ramp up to 20 RPS
        { duration: '2m', target: 20 },    // Stay at 20 RPS
        { duration: '30s', target: 50 },   // Ramp up to 50 RPS
        { duration: '2m', target: 50 },    // Stay at 50 RPS
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        'http_req_duration': ['p(95)<200'],  // 95% of requests should be under 200ms
        'api_success_rate': ['rate>0.95'],   // 95% success rate
    },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export default function () {
    // Test health check endpoint
    testHealthCheck();
    sleep(0.1);

    // Test EEG status endpoint
    testEEGStatus();
    sleep(0.1);

    // Test buffer stats endpoint
    testBufferStats();
    sleep(0.1);
}

function testHealthCheck() {
    const startTime = Date.now();

    const res = http.get(`${BASE_URL}/../health`);

    const duration = Date.now() - startTime;
    requestDuration.add(duration);
    requestCount.add(1);

    const success = check(res, {
        'health check status is 200': (r) => r.status === 200,
        'health check has status field': (r) => JSON.parse(r.body).status !== undefined,
    });

    successRate.add(success);
}

function testEEGStatus() {
    const startTime = Date.now();

    const res = http.get(`${BASE_URL}/eeg/status`);

    const duration = Date.now() - startTime;
    requestDuration.add(duration);
    requestCount.add(1);

    const success = check(res, {
        'EEG status is 200': (r) => r.status === 200,
        'EEG status has operational status': (r) => JSON.parse(r.body).status !== undefined,
    });

    successRate.add(success);
}

function testBufferStats() {
    const startTime = Date.now();

    const res = http.get(`${BASE_URL}/eeg/buffer/stats`);

    const duration = Date.now() - startTime;
    requestDuration.add(duration);
    requestCount.add(1);

    const success = check(res, {
        'buffer stats is 200': (r) => r.status === 200,
        'buffer stats has buffer field': (r) => JSON.parse(r.body).buffer !== undefined,
    });

    successRate.add(success);
}
