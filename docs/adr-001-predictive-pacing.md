# ADR-001: Separate Predictive Pacing from Safety Enforcement

## Status

Accepted

## Context

The Smart Dialer needs to determine how many outbound calls should be started while maintaining strict control over agent capacity and provider health.

A predictive pacing algorithm is useful because the number of calls that will actually be answered is uncertain.

For example, if there are 10 available agents and the historical answer rate is 20%, the system may need to initiate more than 10 calls to keep agents productive.

However, allowing predictive logic to directly initiate calls creates a safety risk.

A bug, incorrect metric, unexpected answer-rate change, or overly aggressive prediction could cause the system to place an excessive number of calls.

Therefore, predictive logic must not be responsible for enforcing hard operational limits.

## Decision

The system separates predictive pacing from safety enforcement.

The architecture is:

```text
Metrics
   ↓
Predictive Pacing Engine
   ↓
Safety Controller
   ↓
Call Allocation
   ↓
Dial Executor
   ↓
Provider
