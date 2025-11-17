from ai_native_os.multi_agent import MasterAgent
from ai_native_os.whiteboard import FileSystemWhiteboard


def main() -> None:
    wb = FileSystemWhiteboard(root="whiteboard")

    master = MasterAgent(whiteboard=wb, project_id="MultiAgent-Demo")

    result = master.run(
        problem_statement=(
            "Build an AI-native automated system that self-evolves code "
            "from NORTH_STAR → ARCHITECTURE → DEV_PLAN → IMPLEMENTATION → CRITIQUE."
        ),
        repo_root="multi_demo_repo",
        dry_run=True,  # Start safe: no disk writes, just planned changes
    )

    print("MasterAgent run complete.")
    print("State snapshot IDs:")
    print("  north_star_state:", result["north_star_state"].id)
    print("  architecture_state:", result["architecture_state"].id)
    print("  dev_plan_state:", result["dev_plan_state"].id)

    print("\nPlanned file changes per step (dry run):")
    for step_label, paths in result["file_changes"].items():
        print(" ", step_label, "->", [str(p) for p in paths])

    print("\nNumber of critique snapshots:", len(result["critiques"]))


if __name__ == "__main__":
    main()
