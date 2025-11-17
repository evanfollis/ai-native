from pathlib import Path

from ai_native_os.agent_core import Agent
from ai_native_os.lj_kernel import LJKernel, LJKernelConfig
from ai_native_os.whiteboard import FileSystemWhiteboard


def main() -> None:
    wb = FileSystemWhiteboard(root="whiteboard")

    agent = Agent(name="lola")

    cfg = LJKernelConfig(
        project_id="LJ-Kernel-Demo",
        project_topic=(
            "Build an AI-native automated system that self-evolves code "
            "from NORTH_STAR → ARCHITECTURE → DEV_PLAN → IMPLEMENTATION → CRITIQUE."
        ),
        notes="Initial demo of LJ-Kernel single-agent loop.",
        repo_root=Path("demo_repo"),
    )

    kernel = LJKernel(agent=agent, config=cfg, whiteboard=wb)
    artifacts = kernel.run()

    print("LJ-Kernel run complete. Snapshot IDs:")
    for phase, snap in artifacts.items():
        print(f"  {phase}: {snap.id}")


if __name__ == "__main__":
    main()
