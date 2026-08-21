# ADR 0006: Account Equity is Derived on the Fly, Never Stored

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm  
**Context:** SRS §5.4, DI-4, FR-4.10, FR-4.11.

---

## Context
In Forex trading, account equity fluctuates with every bid/ask price tick across all open positions. Storing equity in the `paper_accounts` table causes write amplification and race conditions.

## Decision
Account equity is **never stored as a mutable column in PostgreSQL**.
Instead, equity is always computed on-the-fly:
$$\text{Equity} = \text{Balance} + \sum \text{Floating P\&L}(\text{Open Positions})$$

Periodic equity points are captured as read-only historical time-series entries when positions close or on schedule for charting the equity curve.

## Consequences
- Single source of truth for account capital (`balance` + active positions).
- Zero database write thrashing on tick updates.
