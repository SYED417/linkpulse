import http from 'k6/http'
import { check } from 'k6'

// Target the deployed ALB and a real short code. Override with env vars:
//   k6 run -e TARGET=http://... -e CODE=abc123 loadtest.js
const BASE = __ENV.TARGET || 'http://linkpulse-alb-1966342716.us-east-1.elb.amazonaws.com'
const CODE = __ENV.CODE || 'wHqKEq'

export const options = {
  vus: 50,          // 50 concurrent virtual users
  duration: '30s',  // for 30 seconds
  thresholds: {
    http_req_failed: ['rate<0.01'],     // <1% errors
    http_req_duration: ['p(95)<800'],   // 95% of requests under 800ms
  },
}

export default function () {
  // redirects: 0 -> measure our 307 itself; each hit records a click in RDS.
  const res = http.get(`${BASE}/${CODE}`, { redirects: 0 })
  check(res, {
    'status is 307': (r) => r.status === 307,
  })
}
