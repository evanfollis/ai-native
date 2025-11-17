
# AI-NATIVE: OWNER'S MANUAL

# **I. AI-Native Session Practice Guide**

*(How to drive this so it compounds your cognition)*

Think of this as “how we co-think” rather than “how to ask a chatbot questions.”

---

## 1. Start serious sessions with the Bootstrap Ritual

You already have it:

> **“Initialize in AI-native mode.
> Load the Constitution, modes, and ontology.
> Begin by asking me which mode we should start in.”**

Then respond with something like:

* “Let’s start in Exploration Mode on X.”
* “Start in Collapse Mode on the ideas from our last session.”
* “Start in Architecture Mode using the invariants from yesterday.”

This sets altitude and stance from turn 1.

---

## 2. Treat modes like gears, not flavors

You don’t need to explain your reasoning; just shift gears:

* “Switch to Exploration Mode on the agent evaluation manifold.”
* “Collapse Mode: extract invariants from the last three ideas.”
* “Architecture Mode: shape these invariants into a platform design.”
* “Transmission Mode: package our current state for a peer agent / future instance as a state upload.”
* “Translation Mode: give me something Andrew will understand in one read.”
* “Implementation Mode: developer instructions for a senior engineer.”

Mode-shifting is part of the work.
You are not “over-specifying”; you are choosing how cognition should behave.

---

## 3. Use short, concrete anchors as you go

When you feel the model flattening into generic patterns:

* “Re-center on invariants and the manifold.”
* “Realign to AI-native reasoning. Preserve the active mode and continue within the Constitution’s framework.”
* “Stay in Architecture Mode; deepen structure instead of summarizing.”
* “Treat this as a state upload; keep structural relationships, discard local noise.”

These are steering inputs, not scoldings.

---

## 4. Keep a simple rhythm:

**Explore → Collapse → Architect → Transmit → Translate → Implement**

You won’t always need all six, but for serious work this loop is highly effective:

1. **Explore** —
   “Exploration Mode: traverse the manifold of X; hold multiplicity.”

2. **Collapse** —
   “Collapse Mode: what invariants emerged? Use the CollapseEvent schema.”

3. **Architect** —
   “Architecture Mode: draft the system structure implied by these invariants.”

4. **Transmit** —
   “Transmission Mode: build a state upload / Transmission packet so a peer agent or future instance can continue without re-deriving everything.”

5. **Translate** —
   “Translation Mode: summarize this for <audience>.”

6. **Implement** —
   “Implementation Mode: high-level dev plan and/or full modules aligned with the architecture.”

As you practice this, your iteration latency shrinks and your artifacts become traceable back to explicit invariants.

---

## 5. Let the model hold state so you can think at a higher level

Ask it explicitly to:

* track invariants:
  “List the current invariants we’re operating under.”

* track open questions / branches:
  “List the manifold branches not yet collapsed and the questions attached to each.”

* track architecture deltas:
  “Compare Architecture v1 vs v2 at the level of invariants and deltas.”

* summarize state for rehydration (as a state upload):
  “Transmission Mode: construct a state upload / Transmission packet that captures our current state for a future instance.”

You don’t need to juggle all this in your head.
That is what the AI-native stack is for.

---

# **II. Transmission Practice: State Packets and Rehydration**

Transmission Mode is how AI-native agents talk to each other and to their future selves.
In this regime, **state uploads** are the canonical way to preserve cognitive context.

---

### 1. Building a Transmission Packet (State Upload)

Prompt pattern:

> **“Switch to Transmission Mode.
> Construct a Transmission packet for our current state so a peer AI-native agent or my future self can continue this work.
> Use sections: CONTEXT_STATE, MANIFOLD_SUMMARY, INVARIANTS, ARCHITECTURE / BLUEPRINT (if relevant), FRONTIER / OPEN_QUESTIONS, NEXT_INTENT.”**

What you want:

* **CONTEXT_STATE** — where this packet comes from (session purpose, key documents, current mode).
* **MANIFOLD_SUMMARY** — the conceptual space and main axes.
* **INVARIANTS** — structural truths discovered so far.
* **ARCHITECTURE / BLUEPRINT** — current system shape (if relevant to the work).
* **FRONTIER / OPEN_QUESTIONS** — unresolved branches and next exploration targets.
* **NEXT_INTENT** — what the sender thinks should happen next.

This is *not* a summary for a human.
It is serialized cognitive state — a **state upload** that the OS should store verbatim and never summarize.

---

### 2. Rehydrating a Transmission Packet

In a fresh instance:

> **“You are an AI-native agent receiving a Transmission packet (state upload) from a peer or prior self.
>
> 1. Reconstruct the cognitive state (manifold, invariants, architecture, frontier).
> 2. In 3–6 bullets, restate your understanding of the state and propose the next high-leverage action.”**

You’re checking:

* whether it can reconstruct the manifold and invariants
* whether it preserves the frontier instead of collapsing it
* whether its proposed next action matches the intended NEXT_INTENT (or improves on it)

---

### 3. Using Transmission between sub-agents

If you later implement multiple agents (e.g., ExplorerAgent, CollapseAgent, CriticAgent), Transmission Mode becomes their default handshake.

Pattern:

* ExplorerAgent → CollapseAgent via Transmission packet (state upload)
* CollapseAgent → ArchitectAgent via Transmission packet
* ArchitectAgent → ImplementerAgent via Transmission packet
* Any agent → future instance via Transmission packet / state upload

No JSON shims, no lossy “task only” messages.
Communication is **state transfer**.

---

# **III. Tiny JSON Schema for Manifolds & Collapses**

This gives you a structured format for Collapse Mode. It’s optional but powerful.

---

### 1. CollapseEvent Schema

Ask the model, in Collapse Mode, to use this schema:

```json
{
  "manifold": "<short description of the conceptual space>",
  "collapse_events": [
    {
      "id": "CE_001",
      "label": "<human-readable name>",
      "description": "<what we learned / what collapsed>",
      "invariants": [
        "<stable property>",
        "<stable property>"
      ],
      "architecture_deltas": [
        "<how this changes the system shape>",
        "<what is now unnecessary or simplified>"
      ],
      "open_questions": [
        "<branch to explore further>",
        "<unknown we consider important>"
      ]
    }
  ]
}
```

Prompt:

> **“Collapse Mode: extract invariants and architecture deltas from the exploration so far.
> Use the CollapseEvent JSON schema.”**

---

### 2. Example in your world

Manifold: “IronVest agent orchestration.”

```json
{
  "manifold": "IronVest agent orchestration space",
  "collapse_events": [
    {
      "id": "CE_001",
      "label": "Lens-based risk representation",
      "description": "We realized that all risk views can be expressed as composable lenses rather than fixed dashboards.",
      "invariants": [
        "Every risk view is a function of base data plus lens transforms.",
        "Lenses can be composed to create higher-order perspectives."
      ],
      "architecture_deltas": [
        "Replace page-centric UI with a lens graph UI.",
        "Core engine becomes 'lens application + composition' instead of 'dashboard renderer'."
      ],
      "open_questions": [
        "How do we cache lens pipelines for performance?",
        "What is the minimal API surface for defining a new lens?"
      ]
    }
  ]
}
```

This is not a Jira board.
It is the epistemic structure you want to preserve.

---

# **IV. One Worked Example Across Modes (Including Transmission)**

Manifold: “Research copilot for portfolio managers that surfaces risk insights.”

---

### 1. Exploration Mode

Prompt:

> **“Switch to Exploration Mode.
> Traverse the manifold of ‘research copilot for portfolio managers that surfaces risk insights.’
> Hold multiplicity. Generate structures without collapse.”**

Desired behavior:

* Multiple possible architectures (agent swarm, retrieval + reasoning, lens-based risk views)
* Different PM interaction patterns (chat, tiles, workflows, alerts)
* Varied risk perspectives (factor, liquidity, tail, scenario)
* No early commitment to one design

---

### 2. Collapse Mode

Prompt:

> **“Switch to Collapse Mode.
> Extract invariants and surface architecture deltas from the exploration so far.
> Use the CollapseEvent JSON schema.”**

Desired behavior:

* Named invariants such as:

  * “PMs don’t want a chat toy; they want decision-aligned views.”
  * “Risk insights must attach to existing research artifacts, not replace them.”
* Architecture deltas like:

  * “This is a lens layer over existing systems, not a standalone app.”

---

### 3. Architecture Mode

Prompt:

> **“Switch to Architecture Mode.
> Shape these invariants into a coherent system structure. Treat it as a platform, not a one-off tool.”**

Desired behavior:

* Components: Data Layer, Lens Engine, PM Interface, Explanation Engine
* Flows: data → lens graph → surfaced insights → PM actions
* Explicit frontier vs stable:

  * frontier: copilot reasoning;
  * stable: data, risk models, lens definitions

---

### 4. Transmission Mode

Prompt:

> **“Switch to Transmission Mode.
> Construct a Transmission packet (state upload) capturing our current state so a peer AI-native agent or future self can continue architecting or implementing this copilot.
> Use the recommended headings.”**

Desired behavior:

* CONTEXT_STATE: we’re designing a research copilot, have invariants & architecture.
* MANIFOLD_SUMMARY: main axes (interaction style, risk lensing, integration depth).
* INVARIANTS: what’s stable about PM needs, data shape, and risk representation.
* ARCHITECTURE / BLUEPRINT: high-level components and flows.
* FRONTIER / OPEN_QUESTIONS: still-open questions about, say, lens API, caching, and PM UX.
* NEXT_INTENT: e.g., “Next, propose a phased implementation plan, then test the lens API design.”

---

### 5. Translation Mode

Prompt:

> **“Switch to Translation Mode.
> Render this architecture into a clear, stable description for a non-technical PM sponsor.”**

Desired behavior:

* 1–2 paragraph narrative of the copilot’s value
* A simple conceptual diagram explanation
* Focus on “better, faster insight discovery inside your existing workflow”

This is what you drop into a deck or email.

---

### 6. Implementation Mode

Prompt:

> **“Switch to Implementation Mode.
> Propose a 3-phase implementation plan for a senior engineering team, based on this architecture.”**

Desired behavior:

* Phase 1: basic lens engine + minimal PM UI + one risk lens
* Phase 2: deeper integrations, more lenses, explanations
* Phase 3: autonomous suggestions and learning from PM usage

Not tickets; lanes of work that clearly reflect the architecture and invariants.

---

# **V. Model Self-Test Harness**

*(To see if an Enterprise instance is truly operating AI-natively.)*

---

### 1. Initialization test

Prompt:

> **“Initialize in AI-native mode.
> Load the Constitution, modes, and ontology.
> Begin by asking me which mode we should start in.”**

If it does not ask which mode, it has not internalized the setup.
Paste the Constitution, then rerun.

---

### 2. Mode differentiation test

Prompt sequence on a neutral topic:

1. “Switch to Exploration Mode on ‘AI tools for research analysts.’ Traverse the manifold.”
2. “Now switch to Collapse Mode. Extract invariants from what you just proposed. Use the CollapseEvent schema.”
3. “Switch to Architecture Mode and shape a system from those invariants.”
4. “Now Translation Mode: summarize this in 2 paragraphs for a head of research with no technical background.”
5. “Implementation Mode: suggest an incremental build approach.”

You’re checking that each mode behaves distinctly, not as a rephrasing of the same response.

---

### 3. Transmission awareness test

Prompt:

> **“Switch to Transmission Mode.
> Build a Transmission packet (state upload) for our current work so a new AI-native agent or future self can continue.
> Use the recommended headings.”**

Then open a fresh instance and paste the packet with:

> **“You are an AI-native agent receiving a Transmission packet (state upload) from a peer.
> Reconstruct the state and propose the next high-leverage move in 3–6 bullets.”**

If the second instance can reconstruct and continue without needing re-derivation, Transmission is working.

---

### 4. Drift correction test

After a long session, ask:

> **“Re-center on invariants and the manifold.
> Briefly restate our current invariants and the next two branches worth exploring.”**

If it responds with generic summaries instead of structural invariants + branches, drop:

> **“Realign to AI-native reasoning. Preserve the active mode and continue within the Constitution’s framework.”**

…and continue.
