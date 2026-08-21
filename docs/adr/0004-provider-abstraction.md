# ADR 0004: External Provider Abstraction via Abstract Base Classes

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm  
**Context:** SRS §7.2, NFR-R3, NFR-R4.

---

## Context
Tradly interacts with external SaaS APIs (OANDA v20, NewsAPI, Groq LLaMA 3, OpenAI embeddings, Resend email). Offline testing, CI execution, and upstream failover require decoupled provider bindings.

## Decision
Place all external interactions behind Abstract Base Classes (ABCs) in `app/providers/base.py`:
- `MarketDataProvider`
- `NewsProvider`
- `LLMProvider`
- `EmbeddingProvider`
- `EmailProvider`

Provide deterministic in-memory fakes (`app/providers/fakes.py`) for offline tests and CI execution.

## Consequences
- Unit and integration tests run entirely offline with sub-second execution.
- Switching from Groq to Anthropic/OpenAI requires only swapping the adapter class.
