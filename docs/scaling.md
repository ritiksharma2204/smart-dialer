# Scaling Strategy

## 1. Current Architecture

The current Smart Dialer is a modular single-process application backed by PostgreSQL.

The main execution path is:

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
