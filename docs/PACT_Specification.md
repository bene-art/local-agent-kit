# PACT — Protocol for Agent Capability and Trust

> **This document has moved.** The canonical PACT specification and reference implementation now live at:
>
> **[github.com/bene-art/pact-protocol](https://github.com/bene-art/pact-protocol)**
>
> - Formal spec: [`spec/PACT_v1.md`](https://github.com/bene-art/pact-protocol/blob/main/spec/PACT_v1.md)
> - Concept document: [`docs/PACT_Specification.md`](https://github.com/bene-art/pact-protocol/blob/main/docs/PACT_Specification.md)
> - Reference implementation: [`src/pact/`](https://github.com/bene-art/pact-protocol/tree/main/src/pact)
> - Test vectors: [`tests/vectors/`](https://github.com/bene-art/pact-protocol/tree/main/tests/vectors)

## Integration with local-agent-kit

Install the PACT protocol with local-agent-kit support:

```bash
pip install pact-protocol[lak]
```

Make any local-agent-kit agent PACT-addressable:

```python
from pact import PACTAgent
from pact.contrib.lak_channel import PACTChannel

pact = PACTAgent("alice", capabilities=["ask_question"])
channel = PACTChannel(pact)
agent = Agent.from_directory("./my-agent", channel=channel)
asyncio.run(agent.run())
```
