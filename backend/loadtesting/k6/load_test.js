/**
 * MatchHire Backend Load Testing Suite
 * 
 * This script tests the performance of key API endpoints under load.
 * Tests realistic user journeys including authentication, job browsing,
 * applications, and dashboard access.
 * 
 * Usage:
 *   k6 run load_test.js
 *   k6 run load_test.js --vus 50 --duration 5m
 *   k6 run load_test.js --out json=results.json
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Configuration
export const options = {
  stages: [
    // Ramp up to 10 users over 1 minute
    { duration: '1m', target: 10 },
    // Stay at 10 users for 2 minutes
    { duration: '2m', target: 10 },
    // Ramp up to 50 users over 1 minute
    { duration: '1m', target: 50 },
    // Stay at 50 users for 3 minutes
    { duration: '3m', target: 50 },
    // Ramp down to 0 over 1 minute
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests < 500ms, 99% < 1000ms
    http_req_failed: ['rate<0.01'], // Error rate < 1%
    errors: ['rate<0.01'], // Custom error rate < 1%
  },
};

// Configuration
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const CANDIDATE_EMAIL = 'candidate@example.com';
const CANDIDATE_PASSWORD = 'testpass123';
const RECRUITER_EMAIL = 'recruiter@example.com';
const RECRUITER_PASSWORD = 'testpass123';

// Store tokens for reuse
let candidateToken = null;
let recruiterToken = null;

/**
 * Login and get JWT token
 */
function login(email, password) {
  const payload = JSON.stringify({
    email: email,
    password: password,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(`${BASE_URL}/api/auth/login/`, payload, params);
  
  check(res, {
    'login successful': (r) => r.status === 200,
  }) || errorRate.add(1);

  if (res.status === 200) {
    const data = JSON.parse(res.body);
    // Extract token from cookies (simplified - actual implementation may vary)
    return res.cookies.access_token;
  }
  
  return null;
}

/**
 * Test: Health Check
 */
export function testHealthCheck() {
  const res = http.get(`${BASE_URL}/health/`);
  
  check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Test: Public Job List
 */
export function testPublicJobList() {
  const res = http.get(`${BASE_URL}/api/jobs/public/`);
  
  check(res, {
    'job list status 200': (r) => r.status === 200,
    'job list response time < 300ms': (r) => r.timings.duration < 300,
    'job list has data': (r) => JSON.parse(r.body).results.length > 0,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Test: Candidate Dashboard
 */
export function testCandidateDashboard() {
  if (!candidateToken) {
    candidateToken = login(CANDIDATE_EMAIL, CANDIDATE_PASSWORD);
  }
  
  if (!candidateToken) {
    errorRate.add(1);
    return;
  }
  
  const params = {
    headers: {
      'Cookie': `access_token=${candidateToken}`,
    },
  };
  
  const res = http.get(`${BASE_URL}/api/analytics/candidate/dashboard/`, params);
  
  check(res, {
    'dashboard status 200': (r) => r.status === 200,
    'dashboard response time < 500ms': (r) => r.timings.duration < 500,
    'dashboard has metrics': (r) => JSON.parse(r.body).total_applications !== undefined,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Test: Job Recommendations
 */
export function testJobRecommendations() {
  if (!candidateToken) {
    candidateToken = login(CANDIDATE_EMAIL, CANDIDATE_PASSWORD);
  }
  
  if (!candidateToken) {
    errorRate.add(1);
    return;
  }
  
  const params = {
    headers: {
      'Cookie': `access_token=${candidateToken}`,
    },
  };
  
  const res = http.get(`${BASE_URL}/api/jobs/recommendations/`, params);
  
  check(res, {
    'recommendations status 200': (r) => r.status === 200,
    'recommendations response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Test: Recruiter Dashboard
 */
export function testRecruiterDashboard() {
  if (!recruiterToken) {
    recruiterToken = login(RECRUITER_EMAIL, RECRUITER_PASSWORD);
  }
  
  if (!recruiterToken) {
    errorRate.add(1);
    return;
  }
  
  const params = {
    headers: {
      'Cookie': `access_token=${recruiterToken}`,
    },
  };
  
  const res = http.get(`${BASE_URL}/api/analytics/recruiter/dashboard/`, params);
  
  check(res, {
    'recruiter dashboard status 200': (r) => r.status === 200,
    'recruiter dashboard response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Test: Resume Search
 */
export function testResumeSearch() {
  if (!recruiterToken) {
    recruiterToken = login(RECRUITER_EMAIL, RECRUITER_PASSWORD);
  }
  
  if (!recruiterToken) {
    errorRate.add(1);
    return;
  }
  
  const params = {
    headers: {
      'Cookie': `access_token=${recruiterToken}`,
    },
  };
  
  const res = http.get(`${BASE_URL}/api/resumes/search/?skills=python`, params);
  
  check(res, {
    'resume search status 200': (r) => r.status === 200,
    'resume search response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  responseTime.add(res.timings.duration);
}

/**
 * Main test scenario
 */
export default function () {
  // Test health check (lightweight)
  testHealthCheck();
  
  // Test public endpoints (no auth required)
  testPublicJobList();
  
  // Test candidate journey (40% of users)
  if (__VU % 10 < 4) {
    testCandidateDashboard();
    testJobRecommendations();
  }
  
  // Test recruiter journey (30% of users)
  if (__VU % 10 >= 4 && __VU % 10 < 7) {
    testRecruiterDashboard();
    testResumeSearch();
  }
  
  // Mixed traffic (30% of users)
  if (__VU % 10 >= 7) {
    testCandidateDashboard();
    testRecruiterDashboard();
  }
  
  // Think time between requests
  sleep(Math.random() * 3 + 1); // 1-4 seconds
}

/**
 * Setup function - runs once before test
 */
export function setup() {
  console.log('Starting load test...');
  console.log(`Target: ${BASE_URL}`);
  console.log(`Candidate: ${CANDIDATE_EMAIL}`);
  console.log(`Recruiter: ${RECRUITER_EMAIL}`);
}

/**
 * Teardown function - runs once after test
 */
export function teardown(data) {
  console.log('Load test completed');
}
