# ACP — Agent Context Protocol (Concept Summary)

## Overview

ACP (Agent Context Protocol) is a proposed minimal communication layer that enables software agents to interact through **trusted, permission-scoped, and auditable exchanges of intent**.

It is not a replacement for the internet.  
It is a **new layer on top of existing infrastructure**.

---

## Core Idea

> ACP enables agents to exchange **signed, permission-scoped intent**, rather than raw data.

---

## Where ACP Fits (Internet Stack Evolution)

| Layer | Purpose |
|------|--------|
| Physical | Wires, radio, signals |
| Network | TCP/IP (packet routing) |
| Application | HTTP (data exchange) |
| Identity | OAuth (access control) |
| **Intent (ACP)** | **Delegated action + trust between agents** |

---

## Problem Statement

Current systems allow:
- Data exchange (HTTP)
- Service access (APIs)
- Authentication (OAuth)

But they lack:
- Agent identity verification
- Capability discovery between systems
- Permission-scoped context sharing
- Structured task negotiation
- Verifiable interaction records

---

## Goal

Design a **minimal, open, composable protocol** that allows:

- Agents to prove identity
- Agents to declare capabilities
- Agents to exchange tasks within explicit permission
- Agents to share minimal necessary context
- Agents to produce verifiable receipts

---

## Non-Goals

ACP does **not**:
- Replace TCP/IP or HTTP
- Define AI reasoning
- Require a central authority
- Enforce a global identity system
- Act as a platform or product

---

## Core Principles (UNIX-Aligned)

1. **Ownership First**  
   Agents act on behalf of a defined owner.

2. **Explicit Identity**  
   Every interaction is verifiable.

3. **Minimal Disclosure**  
   Only required data is shared.

4. **Scoped Consent**  
   Permissions are:
   - specific
   - time-limited
   - revocable

5. **Capability Declaration**  
   Agents explicitly state what they can do.

6. **Transport Agnostic**  
   Works over HTTP, WebSocket, P2P, or radio.

7. **Stateless Interaction, Stateful Audit**  
   Interactions are simple; logs are durable.

8. **Composable Design**  
   Each component is independent.

9. **No Central Dependency**  
   No required registry or broker.

10. **Rebuildable Simplicity**  
    One engineer should be able to implement it from scratch.

---

## Core Components

### 1. Identity
- Public/private keypair
- Agent ID = hash(public key)
- All messages are signed

### 2. Capability Card (`agent-card.json`)
Declares what an agent can do.

```json
{
  "agent_id": "abc123",
  "name": "ExampleAgent",
  "endpoint": "https://agent.local/api",
  "capabilities": ["schedule_meeting"]
}
```

### 3. Consent Token (GRANT)
Defines what is allowed.

```json
{
  "grant_id": "g-001",
  "issuer": "agent_A",
  "recipient": "agent_B",
  "capability": "schedule_meeting",
  "scope": {
    "data": ["availability_window"],
    "expires": "timestamp"
  }
}
```

### 4. Message Envelope

```json
{
  "message_id": "m-001",
  "from": "agent_A",
  "to": "agent_B",
  "type": "ASK",
  "grant_id": "g-001",
  "payload": { "...": "..." },
  "signature": "..."
}
```

### 5. Message Types

- `HELLO` → Identity introduction
- `CAPS` → Capability declaration
- `GRANT` → Permission issuance
- `ASK` → Task request
- `REPLY` → Task response
- `RECEIPT` → Final audit record

### 6. Receipt (Audit Record)

```json
{
  "task_id": "t-001",
  "participants": ["agent_A", "agent_B"],
  "action": "schedule_meeting",
  "result": "confirmed",
  "timestamp": "...",
  "signatures": ["...", "..."]
}
```

---

## Minimal Interaction Flow

1. HELLO → identify
2. CAPS → discover capabilities
3. GRANT → define permission
4. ASK → request action
5. REPLY → return result
6. RECEIPT → log outcome

---

## Key Insight

ACP is not just about communication.

It is about:

> **structured, constrained, and accountable interaction between autonomous systems**

---

## Technical Domains Involved

- Distributed systems (message passing, failure handling)
- Cryptography (signatures, identity)
- Security (authorization, revocation)
- Protocol design (minimal interfaces)
- Multi-agent systems (coordination)

---

## Transport Layer (Unchanged)

ACP runs on top of:
- HTTP / HTTPS
- WebSocket
- gRPC
- P2P / mesh
- radio (optional, not required)

It does not replace network infrastructure.

---

## Key Challenges

- Designing minimal yet sufficient primitives
- Preventing over-complexity
- Handling trust and revocation safely
- Making it easy to implement
- Achieving interoperability without centralization

---

## Development Path

### Phase 1 — Proof
- Two agents
- Signed messages
- One capability
- One task
- Receipt log

### Phase 2 — Abstraction
- Extract protocol components
- Simplify interfaces
- Remove assumptions

### Phase 3 — Specification
- Write minimal open spec
- Provide reference implementation

### Phase 4 — Adoption
- Open usage
- Independent implementations
- Iterative improvement

---

## Success Criteria

Two independent agents can:
- verify identity
- exchange a scoped task
- complete it
- produce a verifiable receipt

---

## Final Framing

ACP is:
- not a product
- not a platform
- not a framework

It is:

> a minimal primitive for **machine-level responsibility and interaction**

---

## One-Line Summary

> ACP is a lightweight protocol for agents to form **trusted, permission-scoped, auditable relationships** over existing networks.
