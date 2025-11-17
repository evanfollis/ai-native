from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI


@dataclass
class Exchange:
    role: str
    content: str
    meta: Dict[str, Any]


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
    ) -> None:
        self.name = name
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.previous_response_id: Optional[str] = None
        self.chatlog: List[Exchange] = []

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
        self.chatlog.append(Exchange(role="user", content=message, meta={}))
        self.chatlog.append(Exchange(role="assistant", content=text, meta={"response_id": resp.id}))
        return text

    def _extract_text(self, resp: Any) -> str:
        """
        Helper to extract plain text from an OpenAI Responses API response.

        You may need to adapt this depending on the exact SDK version.
        """
        # Best-effort conservative extraction:
        try:
            if hasattr(resp, "output") and resp.output:
                # responses.create returns a list of "output" items
                first = resp.output[0]
                if hasattr(first, "content"):
                    for part in first.content:
                        t = getattr(part, "type", None)
                        if t == "output_text":
                            return part.text.value
                        if t == "output_message":
                            # message-style wrapper
                            for sub in part.content:
                                if getattr(sub, "type", None) == "output_text":
                                    return sub.text.value
        except Exception:
            pass
        # Fallback:
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

    def _initialize_state(self) -> None:
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
