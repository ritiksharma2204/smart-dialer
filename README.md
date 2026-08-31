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
