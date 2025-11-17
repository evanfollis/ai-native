from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


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

    def __init__(self) -> None:
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

    def __init__(self, root: str = "whiteboard") -> None:
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
        for p in self.root.rglob("*.txt"):
            name = p.name
            if name.endswith(f"{snapshot_id}.txt"):
                parts = name.split("_")
                created_at = parts[0]
                agent_name = parts[1]
                text = p.read_text()
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
