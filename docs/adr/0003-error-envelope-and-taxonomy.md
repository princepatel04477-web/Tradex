# ADR 0003: REST Response Envelope and Error Taxonomy

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm  
**Context:** SRS CI-4, NFR-U3, NFR-M5.

---

## Context
Client applications require predictable response formats for both successful payloads and domain error states.

## Decision
All REST responses conform to the envelope model:
```json
{
  "data": { ... } | null,
  "error": {
    "code": "INSUFFICIENT_MARGIN",
    "message": "Insufficient Free Margin: order requires $1085.00, but only $500.00 is available.",
    "details": { "required": "1085.00", "available": "500.00" }
  } | null,
  "meta": {
    "request_id": "7b8f9e21-0a44-4c55-b441-9a74c0b62e49",
    "timestamp": "2026-08-21T08:30:00Z",
    "version": "v1"
  }
}
```

## Consequences
- Every client receives a trace correlation ID in `meta.request_id`.
- Type generators create strongly-typed response structures.
