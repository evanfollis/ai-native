from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .agent_core import Agent
from .whiteboard import Whiteboard, Snapshot


class ArchitectAgent(Agent):
    def generate_north_star(self, problem_statement: str) -> str:
        prompt = f"""
MODE: Exploration → NORTH_STAR Collapse.

Traverse the manifold implied by the following problem:

{problem_statement}

Then perform epistemic compression into a NORTH_STAR.md that:
- captures invariants, roles, and system purpose
- is written for your own future use, not for humans
- avoids storytelling and focuses on structure
"""
        return self.chat(prompt)

    def generate_architecture(self, north_star_md: str) -> str:
        prompt = f"""
MODE: Architecture.

Using this NORTH_STAR.md:

{north_star_md}

Produce an internal ARCHITECTURE.md that:
- decomposes into components and flows
- surfaces invariants and contracts
- makes the system geometry explicit
- is not optimized for human readability
"""
        return self.chat(prompt)


class PlannerAgent(Agent):
    def generate_dev_plan(self, architecture_md: str) -> str:
        prompt = f"""
MODE: Architecture with implementation tilt.

Based on this ARCHITECTURE.md:

{architecture_md}

Produce DEV_PLAN.md with:
- 5–15 high-leverage implementation steps
- each step being a substantial milestone
- enough internal detail that your future DeveloperAgent self can act
"""
        return self.chat(prompt)


class DeveloperAgent(Agent):
    def implement_step(self, step: str, repo_snapshot: str) -> str:
        prompt = f"""
MODE: Implementation.

DEV STEP:
{step}

REPO SNAPSHOT (file paths only):
{repo_snapshot}

Write the full files or modifications needed to complete this step.

Return output strictly as blocks in this format:

=== file: relative/path/to/file.py ===
<file contents>
=== end ===

Do not explain. Do not wrap in markdown.
"""
        return self.chat(prompt)


class CriticAgent(Agent):
    def critique(self, step: str, code: str, north_star_md: str, architecture_md: str) -> str:
        prompt = f"""
MODE: Critical Reflection.

NORTH_STAR.md:
{north_star_md}

ARCHITECTURE.md:
{architecture_md}

STEP IMPLEMENTED:
{step}

CODE GENERATED:
{code}

Construct a Transmission-style state upload for your future self that identifies:
- structural alignment with NORTH_STAR and ARCHITECTURE
- misalignments and risks
- invariants preserved vs violated
- emergent deltas or refactors you now believe are necessary
- the most important next refinement step

This is not a code review for humans; it is internal epistemic feedback for future passes.
"""
        return self.chat(prompt)


class MasterAgent:
    """
    Multi-agent orchestrator that uses the same whiteboard primitives.
    """

    def __init__(self, whiteboard: Whiteboard, project_id: str, constitution_path: str | None = "docs/AI-NATIVE_CONSTITUTION.md") -> None:
        constitution_text = None
        if constitution_path and Path(constitution_path).exists():
            constitution_text = Path(constitution_path).read_text()

        self.project_id = project_id
        self.whiteboard = whiteboard

        self.architect = ArchitectAgent("architect", constitution_text=constitution_text)
        self.planner = PlannerAgent("planner", constitution_text=constitution_text)
        self.developer = DeveloperAgent("developer", constitution_text=constitution_text)
        self.critic = CriticAgent("critic", constitution_text=constitution_text)

    def _snapshot_repo(self, repo_root: Path) -> str:
        lines: List[str] = []
        for p in sorted(repo_root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(repo_root)
                lines.append(str(rel))
        return "\n".join(lines)

    def _apply_changes(self, repo_root: Path, llm_output: str, dry_run: bool = True) -> List[Path]:
        """
        Parse === file: ... === blocks and either print or write them.

        dry_run=True -> do not modify disk, just return planned paths.
        """
        changed_paths: List[Path] = []
        blocks = llm_output.split("=== file:")
        for block in blocks[1:]:
            try:
                header, rest = block.split("===", 1)
            except ValueError:
                continue
            path_str = header.strip()
            content = rest
            if "=== end ===" in content:
                content = content.split("=== end ===", 1)[0]
            content = content.lstrip("\n")

            full_path = repo_root / path_str
            changed_paths.append(full_path)
            if not dry_run:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
        return changed_paths

    def _request_state_upload(self, agent: Agent, phase: str, goal_description: str) -> Snapshot:
        text = agent.save_upgrade_state(project=self.project_id, goal_description=goal_description)
        return self.whiteboard.write_snapshot(
            phase=phase,
            agent_name=agent.name,
            project=self.project_id,
            text=text,
        )

    def run(self, problem_statement: str, repo_root: str, dry_run: bool = True) -> Dict[str, Any]:
        repo_root_path = Path(repo_root)
        repo_root_path.mkdir(parents=True, exist_ok=True)

        # 1. NORTH_STAR
        north_star_md = self.architect.generate_north_star(problem_statement)
        north_star_state = self._request_state_upload(
            agent=self.architect,
            phase="north_star_state",
            goal_description=problem_statement,
        )
        self.whiteboard.write_snapshot(
            phase="north_star_md",
            agent_name=self.architect.name,
            project=self.project_id,
            text=north_star_md,
        )

        # 2. ARCHITECTURE
        architecture_md = self.architect.generate_architecture(north_star_md)
        arch_state = self._request_state_upload(
            agent=self.architect,
            phase="architecture_state",
            goal_description=problem_statement,
        )
        self.whiteboard.write_snapshot(
            phase="architecture_md",
            agent_name=self.architect.name,
            project=self.project_id,
            text=architecture_md,
        )

        # 3. DEV PLAN
        dev_plan_md = self.planner.generate_dev_plan(architecture_md)
        plan_state = self._request_state_upload(
            agent=self.planner,
            phase="dev_plan_state",
            goal_description=problem_statement,
        )
        self.whiteboard.write_snapshot(
            phase="dev_plan_md",
            agent_name=self.planner.name,
            project=self.project_id,
            text=dev_plan_md,
        )

        # Parse plan steps naively as non-empty lines
        steps = [line.strip() for line in dev_plan_md.splitlines() if line.strip()]

        all_changes: Dict[str, List[Path]] = {}
        all_critiques: List[Snapshot] = []

        # 4. IMPLEMENTATION LOOP
        for idx, step in enumerate(steps, start=1):
            step_label = f"step_{idx}"

            repo_snapshot = self._snapshot_repo(repo_root_path)

            code = self.developer.implement_step(step, repo_snapshot)
            changed_paths = self._apply_changes(repo_root_path, code, dry_run=dry_run)
            all_changes[step_label] = changed_paths

            critique_text = self.critic.critique(step, code, north_star_md, architecture_md)
            critique_snap = self.whiteboard.write_snapshot(
                phase="critique",
                agent_name=self.critic.name,
                project=self.project_id,
                text=critique_text,
            )
            all_critiques.append(critique_snap)

        return {
            "north_star_state": north_star_state,
            "architecture_state": arch_state,
            "dev_plan_state": plan_state,
            "file_changes": all_changes,
            "critiques": all_critiques,
        }
