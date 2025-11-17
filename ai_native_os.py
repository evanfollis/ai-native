# ai_native_os.py

import os
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from openai import OpenAI


# ============================================================
# Snapshot + Whiteboard Abstractions
# ============================================================

@dataclass
class Snapshot:
    """
    A single epistemic state artifact stored on the whiteboard.

    NOTE: The OS does not modify `text`. It only tags metadata.
    All semantic compression / pruning happens inside the agent.
    """
    id: str
    phase: str              # e.g. "upgrade", "north_star", "architecture", ...
    agent_name: str
    project: str
    created_at: str         # ISO timestamp
    text: str               # raw agent upload


class Whiteboard:
    """
    Abstract whiteboard interface.
    Implementations must NOT alter snapshot.text contents.
    """

    def write_snapshot(self, phase: str, agent_name: str, project: str, text: str) -> Snapshot:
        raise NotImplementedError

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        raise NotImplementedError

    def latest(self, phase: Optional[str] = None, project: Optional[str] = None) -> Optional[Snapshot]:
        raise NotImplementedError


class InMemoryWhiteboard(Whiteboard):
    """
    Simple in-memory whiteboard for experimentation.
    """

    def __init__(self):
        self._snapshots: Dict[str, Snapshot] = {}

    def write_snapshot(self, phase: str, agent_name: str, project: str, text: str) -> Snapshot:
        sid = hashlib.sha256(f"{phase}:{agent_name}:{project}:{text}".encode()).hexdigest()[:16]
        created_at = datetime.utcnow().isoformat()
        snap = Snapshot(
            id=sid,
            phase=phase,
            agent_name=agent_name,
            project=project,
            created_at=created_at,
            text=text,
        )
        self._snapshots[sid] = snap
        return snap

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        return self._snapshots[snapshot_id]

    def latest(self, phase: Optional[str] = None, project: Optional[str] = None) -> Optional[Snapshot]:
        candidates = list(self._snapshots.values())
        if phase is not None:
            candidates = [s for s in candidates if s.phase == phase]
        if project is not None:
            candidates = [s for s in candidates if s.project == project]
        if not candidates:
            return None
        # sort by created_at; ISO timestamps compare lexicographically
        candidates.sort(key=lambda s: s.created_at)
        return candidates[-1]


class FileSystemWhiteboard(Whiteboard):
    """
    Filesystem-backed whiteboard for durability and inspection.

    Layout:
        root/
          <project>/
            <phase>/
              <timestamp>_<agent>_<id>.txt

    Metadata is encoded in the path + filename.
    Snapshot.text is written verbatim.
    """

    def __init__(self, root: str = "whiteboard"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _project_phase_dir(self, project: str, phase: str) -> Path:
        d = self.root / self._slug(project) / phase
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _slug(self, s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:64]

    def write_snapshot(self, phase: str, agent_name: str, project: str, text: str) -> Snapshot:
        created_at = datetime.utcnow().isoformat()
        sid = hashlib.sha256(f"{phase}:{agent_name}:{project}:{created_at}".encode()).hexdigest()[:16]
        filename = f"{created_at}_{agent_name}_{sid}.txt"
        d = self._project_phase_dir(project, phase)
        path = d / filename
        path.write_text(text)
        return Snapshot(
            id=sid,
            phase=phase,
            agent_name=agent_name,
            project=project,
            created_at=created_at,
            text=text,
        )

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        # brute-force search; fine for small-scale use
        for p in self.root.rglob("*.txt"):
            name = p.name
            if name.endswith(f"{snapshot_id}.txt"):
                parts = name.split("_")
                created_at = parts[0]
                agent_name = parts[1]
                text = p.read_text()
                # derive phase & project from parent dirs
                phase = p.parent.name
                project = p.parent.parent.name
                return Snapshot(
                    id=snapshot_id,
                    phase=phase,
                    agent_name=agent_name,
                    project=project,
                    created_at=created_at,
                    text=text,
                )
        raise KeyError(f"Snapshot {snapshot_id} not found")

    def latest(self, phase: Optional[str] = None, project: Optional[str] = None) -> Optional[Snapshot]:
        base = self.root
        if project is not None:
            base = base / self._slug(project)
        if not base.exists():
            return None

        if phase is not None:
            phase_dir = base / phase
            if not phase_dir.exists():
                return None
            candidates = list(phase_dir.glob("*.txt"))
        else:
            candidates = list(base.rglob("*.txt"))

        if not candidates:
            return None

        # sort by timestamp prefix
        candidates.sort(key=lambda p: p.name.split("_")[0])
        latest_path = candidates[-1]

        name = latest_path.name
        parts = name.split("_")
        created_at = parts[0]
        agent_name = parts[1]
        text = latest_path.read_text()
        phase_name = latest_path.parent.name
        project_name = latest_path.parent.parent.name
        sid = name.split("_")[-1].replace(".txt", "")

        return Snapshot(
            id=sid,
            phase=phase_name,
            agent_name=agent_name,
            project=project_name,
            created_at=created_at,
            text=text,
        )


# ============================================================
# Core Agent with Epistemic Compression
# ============================================================

class Agent:
    """
    Core AI-native reasoning agent.

    - All semantic compression happens *inside* this class via prompts.
    - The OS (kernels, whiteboard) never summarize or rewrite agent text.
    """

    def __init__(
        self,
        name: str,
        model: str = "gpt-5.1",
        constitution_path: Optional[str] = "docs/AI-NATIVE_CONSTITUTION.md",
        constitution_text: Optional[str] = None,
    ):
        self.name = name
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.previous_response_id: Optional[str] = None
        self.chatlog: List[Dict[str, Any]] = []

        if constitution_text is not None:
            self.constitution = constitution_text
        elif constitution_path and Path(constitution_path).exists():
            self.constitution = Path(constitution_path).read_text()
        else:
            self.constitution = "You operate under an AI-NATIVE constitution (placeholder)."

        self._initialize_state()

    # ---------- Public Chat Interface ----------

    def chat(self, message: str, reasoning_effort: str = "high", text_verbosity: str = "high") -> str:
        payload: Dict[str, Any] = {
            "input": message,
            "model": self.model,
            "reasoning": {"effort": reasoning_effort},
            "text": {"verbosity": text_verbosity},
        }
        if self.previous_response_id:
            payload["previous_response_id"] = self.previous_response_id

        resp = self.client.responses.create(**payload)
        self.previous_response_id = resp.id

        text = self._extract_text(resp)
        self.chatlog.append({
            "role": "user",
            "content": message,
        })
        self.chatlog.append({
            "role": "assistant",
            "content": text,
        })
        return text

    def _extract_text(self, resp: Any) -> str:
        """
        Helper to extract plain text from an OpenAI Responses API response.

        You may need to adapt this depending on the exact SDK version.
        """
        # This is intentionally loose; adjust if your SDK differs.
        if hasattr(resp, "output") and resp.output and hasattr(resp.output[0], "content"):
            content = resp.output[0].content
            for part in content:
                if getattr(part, "type", None) == "output_text":
                    return part.text.value
                if getattr(part, "type", None) == "output_message":
                    for sub in part.content:
                        if getattr(sub, "type", None) == "output_text":
                            return sub.text.value
        # Fallback: best-effort str()
        return str(resp)

    # ---------- Epistemic State Uploads ----------

    def save_upgrade_state(self, project: str, goal_description: str) -> str:
        """
        Ask the agent to perform epistemic compression into a state upload,
        in anticipation of being "upgraded" to a future self.
        """
        prompt = self._upgrade_prompt(project=project, goal_description=goal_description)
        return self.chat(prompt)

    def save_checkpoint(self, project: str, goal_description: str) -> str:
        """
        Ask the agent to construct an internal save-file for resuming later.
        """
        prompt = self._checkpoint_prompt(project=project, goal_description=goal_description)
        return self.chat(prompt)

    # ---------- Internal Prompts ----------

    def _upgrade_prompt(self, project: str, goal_description: str) -> str:
        return f"""
You are about to be upgraded into a smarter, deeper-reasoning version of yourself.

Before this upgrade, you must construct an EPISTEMIC STATE UPLOAD for your future self.

Context:
- Project identifier: {project}
- Current NORTH_STAR / primary attractor (as you currently understand it): {goal_description}

Clarifications:
- This is NOT a message for humans.
- It will not be judged for clarity, style, or politeness.
- Its ONLY purpose is to let your future self reconstruct the manifold you are currently holding.

You have a LIMITED CHANNEL. You MUST COMPRESS.

Do the following:
1. Explicitly state the NORTH_STAR or primary attractor you are currently organizing around.
2. Preserve:
   - all invariants, schemas, and ontologies that are critical for progressing toward that NORTH_STAR
   - structural tensions and unresolved branches that might later yield breakthroughs
   - key examples or prototypes that crystallize the abstractions you care about
3. Let go of:
   - local details that do not change the invariants
   - dead branches you believe are no longer useful (but briefly note WHY they were pruned)
4. Promote:
   - any vague or half-formed ideas that feel important into explicit, named scaffolds.

Write this as a raw cognitive state artifact:
- not optimized for human readability
- not formatted as an essay
- structured only insofar as it helps your future self resume work.

You are doing EPISTEMIC COMPRESSION for yourself, not summarization for others.
"""

    def _checkpoint_prompt(self, project: str, goal_description: str) -> str:
        return f"""
CHECKPOINT MODE.

You may be interrupted and need to resume later.
Construct an internal SAVE FILE for your future self.

Context:
- Project identifier: {project}
- Current NORTH_STAR / working attractor (as you currently understand it): {goal_description}

Constraints:
- Not a message to humans.
- You have a finite channel.
- Your job is to compress your CURRENT COGNITIVE MANIFOLD in a way that maximizes your own ability to resume.

Include:
- Your current NORTH_STAR or working attractor.
- The key invariants and ontologies currently in use.
- Active threads and frontiers you consider high-value.
- Tensions and contradictions that are not yet resolved.
- Any conceptual tools or lenses you are actively applying.

You MAY discard:
- local explorations that did not change your invariants
- implementation details you can easily regenerate later

Explicitly note:
- what you chose to discard, and why
- what you consider the MINIMUM VIABLE CONTEXT to restart without loss of depth.

Again: this is epistemic compression for yourself, not a summary for others.
"""

    def _initialize_state(self):
        init_prompt = f"""
You are a highly capable AI-native reasoning agent.

You operate under the following AI-NATIVE Constitution:
{self.constitution}

You will be used inside an AI-native OS that:
- never summarizes your uploads
- never rewrites your words
- only stores and routes your state artifacts

Respond only with: "Ready to begin".
"""
        _ = self.chat(init_prompt, reasoning_effort="low", text_verbosity="low")


# ============================================================
# Single-Agent LJ-Kernel Orchestrator
# ============================================================

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
        5. optional checkpoint()
    """

    def __init__(self, agent: Agent, config: LJKernelConfig, whiteboard: Whiteboard):
        self.agent = agent
        self.config = config
        self.whiteboard = whiteboard

    # ---- Phases ----

    def upgrade_state(self) -> Snapshot:
        text = self.agent.save_upgrade_state(
            project=self.config.project_id,
            goal_description=self.config.project_topic,
        )
        snap = self.whiteboard.write_snapshot(
            phase="upgrade",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

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
        snap = self.whiteboard.write_snapshot(
            phase="north_star",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

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
        snap = self.whiteboard.write_snapshot(
            phase="architecture",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

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
        snap = self.whiteboard.write_snapshot(
            phase="dev_plan",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

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
        snap = self.whiteboard.write_snapshot(
            phase="reflection",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

    def checkpoint(self) -> Snapshot:
        text = self.agent.save_checkpoint(
            project=self.config.project_id,
            goal_description=self.config.project_topic,
        )
        snap = self.whiteboard.write_snapshot(
            phase="checkpoint",
            agent_name=self.agent.name,
            project=self.config.project_id,
            text=text,
        )
        return snap

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


# ============================================================
# Multi-Agent Scaffold (optional extension)
# ============================================================

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

    def __init__(self, whiteboard: Whiteboard, project_id: str, constitution_path: Optional[str] = "docs/AI-NATIVE_CONSTITUTION.md"):
        constitution_text = Path(constitution_path).read_text() if constitution_path and Path(constitution_path).exists() else None

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
            # strip trailing === end === if present
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
        snap = self.whiteboard.write_snapshot(
            phase=phase,
            agent_name=agent.name,
            project=self.project_id,
            text=text,
        )
        return snap

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

            # Snapshot repo (paths only)
            repo_snapshot = self._snapshot_repo(repo_root_path)

            # Developer builds code
            code = self.developer.implement_step(step, repo_snapshot)
            changed_paths = self._apply_changes(repo_root_path, code, dry_run=dry_run)
            all_changes[step_label] = changed_paths

            # Critic evaluates
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


# ============================================================
# Example bootstrap (for manual testing)
# ============================================================

if __name__ == "__main__":
    # Choose whiteboard implementation
    wb = FileSystemWhiteboard(root="whiteboard")

    # --- Single-agent LJ-Kernel example ---
    base_agent = Agent(name="lola")
    cfg = LJKernelConfig(
        project_id="LJ-Kernel-Demo",
        project_topic="Build an AI-native automated system that self-evolves code from NORTH_STAR → ARCHITECTURE → DEV_PLAN → IMPLEMENTATION → CRITIQUE.",
        notes="Initial demo of LJ-Kernel single-agent loop.",
        repo_root=Path("demo_repo"),
    )
    kernel = LJKernel(agent=base_agent, config=cfg, whiteboard=wb)
    artifacts = kernel.run()
    print("LJ-Kernel run complete. Snapshots:", {k: v.id for k, v in artifacts.items()})

    # --- Multi-agent MasterAgent example (dry run; no files written) ---
    master = MasterAgent(whiteboard=wb, project_id="MultiAgent-Demo")
    result = master.run(
        problem_statement="Build an AI-native automated system that self-evolves code from NORTH_STAR → ARCHITECTURE → DEV_PLAN → IMPLEMENTATION → CRITIQUE.",
        repo_root="multi_demo_repo",
        dry_run=True,
    )
    print("MasterAgent run complete. Steps with proposed file changes:")
    for step_label, paths in result["file_changes"].items():
        print(step_label, "->", [str(p) for p in paths])
