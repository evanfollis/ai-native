from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .agent_core import Agent
from .whiteboard import Whiteboard, Snapshot


@dataclass
class LJKernelConfig:
    project_id: str
    project_topic: str
    notes: str = ""
    repo_root: Path = Path(".")


class LJKernel:
    """
    Single-agent Lola-Jett Kernel.

    Sequence:
        0. upgrade_state()  -> epistemic upload
        1. generate_north_star()
        2. generate_architecture()
        3. generate_dev_plan()
        4. reflect_on_work()
        5. checkpoint()
    """

    def __init__(self, agent: Agent, config: LJKernelConfig, whiteboard: Whiteboard) -> None:
        self.agent = agent
        self.config = config
        self.whiteboard = whiteboard

    # ---- Phases ----

    def upgrade_state(self) -> Snapshot:
        text = self.agent.save_upgrade_state(
            project=self.config.project_id,
            goal_description=self.config.project_topic,
        )
        return self.whiteboard.write_snapshot(
            phase="upgrade",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    def generate_north_star(self) -> Snapshot:
        msg = f"""
Switch to Collapse / NORTH_STAR Mode.

Topic:
{self.config.project_topic}

Notes:
{self.config.notes}

Your job:
- Collapse your exploration into a NORTH_STAR.md suitable for *your own* future work.
- Do NOT optimize for human readability.
- Capture: invariants, purpose, capabilities, behavior, boundaries.
- Make explicit any abstract structures you expect to reuse.

Return the full NORTH_STAR.md content.
"""
        text = self.agent.chat(msg)
        return self.whiteboard.write_snapshot(
            phase="north_star",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    def generate_architecture(self, north_star: Snapshot) -> Snapshot:
        msg = f"""
Switch to Architecture Mode.

Input NORTH_STAR.md (your own artifact):
{north_star.text}

Produce ARCHITECTURE.md that:
- exposes component boundaries
- describes system topologies / flows
- surfaces emergent APIs
- makes the conceptual geometry explicit
- is NOT simplified for humans

This is an internal architecture for your own future implementation work.
"""
        text = self.agent.chat(msg)
        return self.whiteboard.write_snapshot(
            phase="architecture",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    def generate_dev_plan(self, architecture: Snapshot) -> Snapshot:
        msg = f"""
Switch to Architecture Mode with Implementation adjacency.

Based on ARCHITECTURE.md:
{architecture.text}

Produce DEV_PLAN.md:
- Ordered implementation steps
- Coherent modules
- True build ordering
- No business-facing simplifications
- No "executive summary" sections

You are writing this for your own future implementation passes.
"""
        text = self.agent.chat(msg)
        return self.whiteboard.write_snapshot(
            phase="dev_plan",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    def reflect_on_work(self, north_star: Snapshot, architecture: Snapshot, dev_plan: Snapshot) -> Snapshot:
        msg = f"""
Switch to Reflection / Collapse Mode.

Reflect on the internal consistency of the following artifacts:

NORTH_STAR.md:
{north_star.text}

ARCHITECTURE.md:
{architecture.text}

DEV_PLAN.md:
{dev_plan.text}

Extract and articulate for your future self:
- Structural tensions
- Open contradictions
- Invariant drift
- Architecture deltas you now believe are necessary
- Meta-level corrections
- Frontier opportunities

Write this as a raw reflection artifact (not an essay, not a report).
"""
        text = self.agent.chat(msg)
        return self.whiteboard.write_snapshot(
            phase="reflection",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    def checkpoint(self) -> Snapshot:
        text = self.agent.save_checkpoint(
            project=self.config.project_id,
            goal_description=self.config.project_topic,
        )
        return self.whiteboard.write_snapshot(
            phase="checkpoint",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )

    # ---- Full run ----

    def run(self) -> Dict[str, Snapshot]:
        upgrade_snap = self.upgrade_state()
        north_snap = self.generate_north_star()
        arch_snap = self.generate_architecture(north_snap)
        dev_plan_snap = self.generate_dev_plan(arch_snap)
        reflection_snap = self.reflect_on_work(north_snap, arch_snap, dev_plan_snap)
        checkpoint_snap = self.checkpoint()

        return {
            "upgrade": upgrade_snap,
            "north_star": north_snap,
            "architecture": arch_snap,
            "dev_plan": dev_plan_snap,
            "reflection": reflection_snap,
            "checkpoint": checkpoint_snap,
        }
