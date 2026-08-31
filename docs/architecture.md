# Smart Dialer Architecture

## 1. Overview

The Smart Dialer is a safety-first outbound calling system designed to maximize agent utilization while preventing uncontrolled over-dialing.

The system separates prediction, safety enforcement, resource allocation, call execution, and provider event processing into independent components.

The core pipeline is:

Metrics
   ↓
Predictive Pacing Engine
   ↓
Safety Controller
   ↓
Progressive Dialer
   ↓
Atomic Allocation
   ↓
Dial Executor
   ↓
Telecom Provider
   ↓
Provider Events
   ↓
State Machines


## 2. Core Components

### Predictive Pacing Engine

The pacing engine estimates how many calls should be attempted based on:

- available agents
- historical answer rate
- ringing calls
- target utilization
- average talk time

It produces a recommendation rather than directly placing calls.

This separation is intentional: predictive logic is allowed to make mistakes, but it must never bypass the safety boundary.


### Safety Controller

The Safety Controller is the hard safety boundary.

It evaluates the pacing recommendation against:

- available agents
- reserved agents
- maximum agent utilization
- ringing-call limits
- provider health

The final number of calls allowed to proceed is always bounded by these safety rules.

If the provider is unhealthy, predictive dialing is stopped and progressive fallback is requested.


### Progressive Dialer

The Progressive Dialer provides the deterministic baseline.

It allocates calls only when capacity is available and never intentionally exceeds available agent capacity.

It is also used as the fallback when predictive dialing cannot safely operate.


### Atomic Allocation

Agent and borrower allocation is performed through database-backed conditional state transitions.

The allocator must handle situations where multiple workers observe the same available resources.

A worker can observe a resource as available but still fail to reserve it because another worker may have claimed it first.

This makes the database state transition the source of truth rather than the worker's in-memory observation.


### Dial Executor

The Dial Executor takes an allocated call and invokes the selected telecom provider.

Responsibilities include:

- provider lookup
- call initiation
- provider call ID assignment
- transitioning the call to `INITIATED`
- handling provider failures
- releasing the agent and borrower when initiation fails


### Provider Layer

The provider layer uses a common provider interface.

The project currently includes mock providers:

- Provider A
- Provider B

This allows provider behavior to be tested independently from the dialer logic.


### Provider Event Processor

Provider events are treated as an external, unreliable input stream.

The processor handles:

- duplicate events
- out-of-order events
- terminal call states
- agent release
- borrower state updates

Provider event IDs are unique per provider, allowing duplicate events to be detected.


## 3. State Machines

Call lifecycle:

```text
QUEUED
  ↓
RESERVED
  ↓
INITIATED
  ↓
RINGING
  ↓
ANSWERED
  ↓
CONNECTED
  ↓
COMPLETED
