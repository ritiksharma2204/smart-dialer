# Evaluation and Test Evidence

This document maps the prototype to the requested assignment behaviors and
provides reproducible commands for the evaluator.

## 1. Automated tests

Run the complete test suite:

```bash
pytest -q
```

The tests cover:

- agent reservation/concurrency behavior;
- call allocation;
- call state transitions;
- provider initiation;
- provider failures;
- provider events;
- duplicate provider events;
- out-of-order/late events;
- cancellation and resource release;
- predictive pacing;
- safety-controller limits;
- progressive dialing;
- failure simulation;
- metrics;
- end-to-end scenarios.

## 2. Basic predictive simulation

Run:

```bash
python scripts/simulate.py
```

The simulation evaluates:

| Scenario | Answer rate | Avg talk time | Provider condition |
|---|---:|---:|---|
| A | 20% | 120 sec | healthy |
| B | 50% | 90 sec | healthy |
| C | 70% | 180 sec | healthy |
| D | changing/degraded | changing | latency/failure/outage |

The output shows:

- requested calls from the Predictive Pacing Engine;
- calls allowed by the Safety Controller;
- whether the safety decision was approved;
- whether progressive fallback was requested;
- provider latency/failure assumptions.

The important architectural property is that the pacing engine only recommends a
number. The Safety Controller remains the hard boundary before allocation and
provider execution.

## 3. HTTP smoke test

Start the stack:

```bash
docker compose up --build -d
```

Verify the service:

```bash
curl -i http://127.0.0.1:8000/health
```

Expected:

```text
HTTP/1.1 200 OK
{"status":"ok"}
```

Create a campaign in the Docker database:

```bash
docker compose exec app python -c "from app.database import SessionLocal; from app.models.campaign import Campaign; db=SessionLocal(); c=Campaign(name='Evaluation Campaign'); db.add(c); db.commit(); db.refresh(c); print('CAMPAIGN_ID=', c.id); db.close()"
```

Use the printed campaign ID:

```bash
curl -i -X POST http://127.0.0.1:8000/campaigns/<CAMPAIGN_ID>/dial
```

A valid campaign returns HTTP 200. With no queued borrowers/available work,
`calls_started` may legitimately be `0`.

## 4. Basic load test

Run:

```bash
k6 run \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env CAMPAIGN_ID=<CAMPAIGN_ID> \
  load-tests/dial-cycle.js
```

The prototype's current verified local run used:

- 5 VUs;
- 30 seconds;
- 150 iterations;
- 150 HTTP requests;
- 300 checks;
- 100% checks succeeded;
- 0% HTTP request failures;
- average HTTP request duration about 12.5 ms.

These figures are environment-specific and should be treated as sample local
results, not production capacity claims.

## 5. Failure behavior demonstrated by tests

### Worker/provider failure

The provider-outage tests verify that a failed initiation moves the call to
`FAILED` and releases both the agent and borrower.

### Duplicate events

The same provider event ID can be replayed without creating another state
transition.

### Terminal/late events

Once a call is terminal, a later-arriving event such as `ANSWERED` is ignored,
so the call remains terminal.

### Cancellation

A cancelled call releases the agent and returns the borrower to a reusable
state.

### Provider degradation

An unhealthy provider causes predictive pacing to request zero calls and the
Safety Controller to reject the request while requesting progressive fallback.

## 6. Architecture documents

- `docs/architecture.md` — component architecture and state-machine design.
- `docs/scaling.md` — scaling/distributed-system strategy.
- `docs/adr-001-predictive-pacing.md` — architecture decision record for
  predictive pacing.

The design deliberately avoids Kafka/Redis/microservices in the prototype.
PostgreSQL is the persistence and concurrency source of truth; the architecture
can later be split into workers/services if scale requires it.
