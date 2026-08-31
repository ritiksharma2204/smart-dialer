# Smart Dialer

A production-oriented smart outbound dialer prototype designed around
concurrency correctness, provider resilience, deterministic safety controls,
and predictive call pacing.

## What This Project Demonstrates

The system models a real outbound calling platform with:

- Agent and borrower lifecycle management
- Atomic resource allocation
- Call state machines
- Provider abstraction with multiple mock providers
- Idempotent provider event processing
- Out-of-order event handling
- Progressive dialing
- Predictive pacing
- Independent safety controls
- Provider failure fallback
- Failure simulation
- Metrics collection
- Scenario-based testing
- PostgreSQL persistence
- Dockerized application and database
- Automated pytest CI
- k6 load testing

The primary design goal is not simply to place calls, but to ensure that
**predictive dialing never bypasses safety and concurrency guarantees.**

---
## Design Answer

Use predictive pacing to estimate how many calls are needed to keep agents utilized, based on answer rate, agent availability, ringing calls, and talk time.

However, the prediction never directly places calls. Every request passes through a deterministic Safety Controller that caps it by agent capacity, ringing-call limits, and provider health.

This gives us the utilization benefit of predictive dialing while retaining the hard safety and concurrency guarantees of progressive dialing. If the provider becomes unhealthy, predictive dialing stops and the system falls back to progressive dialing.

---
## Architecture

```text
                         Smart Dialer
                              |
              +---------------+---------------+
              |                               |
              v                               v
      Predictive Pacing                Safety Controller
              |                               |
              +---------------+---------------+
                              |
                              v
                     Progressive Dialer
                              |
                              v
                      Atomic Allocation
                              |
                              v
                       Dial Executor
                              |
                              v
                     Provider Registry
                        /          \
                       v            v
                 Provider A    Provider B
                       |
                       v
                  Provider Events
                       |
                       v
                Event Processor
                       |
                       v
                   PostgreSQL
## Verification & Results

The prototype was verified locally with the following checks.

### Automated Test Suite

The complete pytest suite passes:

```text
65 passed in 0.73s

### Predictive Pacing Simulation
Run:
python scripts/simulate.py

### Evaluation Results

A local run produced the following results:

| Scenario | Answer Rate | Avg. Talk Time | Latency | Failure Rate | Requested | Allowed | Approved | Fallback |
|----------|-------------|----------------|---------|--------------|-----------|---------|----------|----------|
| A | 20% | 120 sec | 100 ms | 2% | 12 | 10 | Yes | No |
| B | 50% | 90 sec | 250 ms | 5% | 12 | 10 | Yes | No |
| C | 70% | 180 sec | 500 ms | 10% | 9 | 9 | Yes | No |
| D | 50% | 120 sec | 800 ms | 30% | 0 | 0 | No | Yes |

### Observations

- **Scenario A:** Low answer rate causes the pacing engine to request more calls, but the Safety Controller caps the request at 10.
- **Scenario B:** With a 50% answer rate, predictive pacing still requests 12 calls, while safety limits execution to 10.
- **Scenario C:** Higher answer rate reduces the requested dial count to 9, which can be safely approved.
- **Scenario D:** Provider degradation causes predictive dialing to stop and the system requests progressive fallback.
- The Safety Controller therefore acts as the hard boundary regardless of the pacing recommendation.

### HTTP Smoke Test

HTTP/1.1 200 OK
{"status":"ok"}

### k6 Load Test
Run:
k6 run \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env CAMPAIGN_ID=1 \
  load-tests/dial-cycle.js

The dial-cycle endpoint was load tested locally using:

- 5 virtual users
- 30-second test duration
- 150 completed iterations
- 150 HTTP requests
- 300 checks
- 100% checks succeeded
- 0% checks failed
- 0% HTTP request failures

Observed local performance:

| Metric | Result |
|---|---:|
| Average latency | 17.28 ms |
| p90 latency | 22.89 ms |
| p95 latency | 33.45 ms |
| Maximum latency | 76.06 ms |
| HTTP requests | 150 |
| HTTP request failure rate | 0% |
