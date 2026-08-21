# ADR 0002: Monorepo Structure and Architectural Layering

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm  
**Context:** Monorepo architecture for the Tradly Forex Intelligence Platform.

---

## Context
Tradly requires strict separation of concerns between presentation, orchestration, domain algorithms, and data access.

## Decision
Adopt a standard monorepo layout:
- `apps/web/`: Next.js 14 App Router (BFF only, zero business math).
- `apps/api/`: FastAPI backend enforcing Layering Law: `routers → services → repositories → DB`.
- `app/domain/`: Pure functions with zero I/O and strict `decimal.Decimal` types.
- `infra/`: Database migrations, Docker compose, and CI definitions.

## Consequences
- **Positive:** Modular codebase, isolated test execution, and rapid CI feedback.
- **Negative:** Requires disciplined import rules preventing routers from accessing database models directly.
