# AI-Native OS (Lola-Jett Kernel & Multi-Agent Scaffold)

This repo implements an AI-native “OS layer” for agents that:

- Treats **state uploads** as first-class artifacts (epistemic compression for the agent’s future self, not human summaries).
- Uses a **Whiteboard** abstraction (in-memory or filesystem) to store raw state snapshots with minimal metadata.
- Provides:
  - A **single-agent** LJ-Kernel loop:
    - UPGRADE → NORTH_STAR → ARCHITECTURE → DEV_PLAN → REFLECTION → CHECKPOINT
  - A **multi-agent** scaffold:
    - Architect / Planner / Developer / Critic + MasterAgent orchestrator.

All semantic compression is done *by the agents*, for themselves; the OS never summarizes or rewrites their uploads.

## Layout

- `ai_native_os/whiteboard.py`  
  Snapshot dataclass + Whiteboard interface + in-memory and filesystem implementations.

- `ai_native_os/agent_core.py`  
  Core `Agent` class with:
  - Constitution loading
  - Chat wrapper for OpenAI Responses API
  - Epistemic `save_upgrade_state` and `save_checkpoint` prompts.

- `ai_native_os/lj_kernel.py`  
  Single-agent `LJKernel` orchestrator and `LJKernelConfig`.

- `ai_native_os/multi_agent.py`  
  Role-specialized agents (`ArchitectAgent`, `PlannerAgent`, `DeveloperAgent`, `CriticAgent`) and `MasterAgent` orchestrator.

- `scripts/run_lj_kernel.py`  
  Example entrypoint for the single-agent loop.

- `scripts/run_multi_agent.py`  
  Example entrypoint for the multi-agent loop (defaults to dry-run: prints planned file writes but does not touch disk).

- `docs/AI-NATIVE_CONSTITUTION.md`  
  Placeholder for your AI-NATIVE Constitution text.

## Setup

```bash
cd ai-native-os
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Set your OpenAI key:

```bash
export OPENAI_API_KEY="sk-..."  # PowerShell: $env:OPENAI_API_KEY="sk-..."
```

## Run examples

Single-agent LJ-Kernel:

```python
python scripts/run_lj_kernel.py
```

Multi-agent scaffold (dry run, no real file writes):

```python
python scripts/run_multi_agent.py
```

By default, filesystem whiteboard snapshots go under whiteboard/ and demo repos under demo_repo/ and multi_demo_repo/.

NOTE: The Agent._extract_text helper may need minor adjustment depending on the exact openai SDK version and Responses API schema you’re using. It’s written to be conservative and easy to tweak.