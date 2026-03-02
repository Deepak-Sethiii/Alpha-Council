# ⚖️ Alpha Council
### *Not a chatbot. A council.*

> An Open-Weights, High-Velocity Multi-Agent Swarm for Institutional-Grade Financial Signal Generation — powered entirely by **Llama-3.1-8b-instant on Groq**, governed by code-enforced reasoning limits, Constitutional Data anchors, and structured adversarial debate.

---

## Table of Contents

1. [The Problem: LLM Fickleness in Finance](#1-the-problem-llm-fickleness-in-finance)
2. [Architecture Overview](#2-architecture-overview)
3. [Agent Roster & Schemas](#3-agent-roster--schemas)
4. [Constitutional Data — The Truth Anchor](#4-constitutional-data--the-truth-anchor)
5. [The Persistence Mandate](#5-the-persistence-mandate)
6. [The Three-Tier Adjustment Scale](#6-the-three-tier-adjustment-scale)
7. [Chain-of-Thought (CoT) Guardrails](#7-chain-of-thought-cot-guardrails)
8. [The State-Accumulation Pipeline — Node-by-Node](#8-the-state-accumulation-pipeline--node-by-node)
9. [AgentState — Canonical Data Model](#9-agentstate--canonical-data-model)
10. [API Output Contract](#10-api-output-contract)
11. [Installation & Quickstart](#11-installation--quickstart)
12. [Design Philosophy](#12-design-philosophy)

---

## 1. The Problem: LLM Fickleness in Finance

Large Language Models are, by default, sycophants. Present a bearish argument to a model that just generated a bullish thesis, and it will capitulate — not because the underlying data changed, but because the conversational pressure did. In finance, this is not a UX inconvenience. It is a catastrophic failure mode.

**Alpha Council was engineered to solve this.** Every agent in the swarm is subject to programmatic reasoning constraints that prevent opinion drift based purely on social pressure. Confidence scores are not soft suggestions — they are code-enforced outputs that must be justified against `Constitutional Data`. Signals cannot flip unless specific, measurable chart or fundamental criteria are met. The system does not ask LLMs to *try* to be rigorous. It *forces* them to be, at the code layer.

---

## 2. Architecture Overview — State-Accumulation Pipeline

Alpha Council implements a six-node **State-Accumulation Pipeline**, defined as a strict linear chain of directed edges in `agent/graph.py`. There are no parallel branches and no shared memory bus — the single `AgentState` object is the exclusive communication channel between all nodes. Each node receives the full state, appends its output fields, and passes the enriched state to the next node via a directed edge.

The six nodes divide into three logical phases: **Thesis Generation** (Nodes 1–2), **Adversarial Audit** (Node 3), **Rebuttal & Adjudication** (Nodes 4–5), and **Synthesis** (Node 6). The Rebuttal nodes are the architectural centrepiece — they are the only nodes permitted to write the `_final` versions of each thesis, and they are the precise location where the Persistence Mandate and Adjustment Scale are enforced.

```
  main.py — ENTRY POINT
  ══════════════════════════════════════════════════════════════
  get_constitutional_data(ticker)        ← yfinance fetch
  AgentState constructed with all fields ← injected BEFORE
  graph.invoke(state)                       graph starts
  ══════════════════════════════════════════════════════════════
        │
        ▼  add_edge(START, "technical_analyst")
┌─────────────────────────────────────────────────────────────┐
│  NODE 1 · technical_analyst               [THESIS]          │
│                                                             │
│  Reads:   pe_ratio, forward_pe, beta, sector,               │
│           debt_to_equity, rsi  (Constitutional Data)        │
│  Writes:  tech_thesis_initial                               │
│           tech_signal_initial                               │
│           tech_confidence_initial                           │
└───────────────────────────┬─────────────────────────────────┘
        │  add_edge("technical_analyst", "fundamental_analyst")
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 2 · fundamental_analyst             [THESIS]          │
│                                                             │
│  Reads:   Constitutional Data + tech_thesis_initial         │
│  Writes:  fund_thesis_initial                               │
│           fund_signal_initial                               │
│           fund_confidence_initial                           │
└───────────────────────────┬─────────────────────────────────┘
        │  add_edge("fundamental_analyst", "risk_manager")
        │  AgentState now carries both initial theses
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 3 · risk_manager   (Groq / Adversarial LLM) [ATTACK]  │
│                                                             │
│  Reads:   Both initial theses + full Constitutional Data    │
│  Writes:  risk_critique_tech                                │
│           risk_critique_fund                                │
│           risk_danger_score  (Materiality Matrix L1–L4)     │
│           adjustment_tier  (PERSISTENCE / WARNING /         │
│                             KILL_SIGNAL)                    │
└───────────────────────────┬─────────────────────────────────┘
        │  add_edge("risk_manager", "technical_rebuttal")
        │  risk_score + adjustment_tier now locked in state
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 4 · technical_rebuttal             [DEFENSE]          │
│                                                             │
│  Reads:   tech_thesis_initial + risk_critique_tech +        │
│           risk_danger_score                                 │
│  Applies: Persistence Mandate (if risk_danger_score < 35,   │
│           confidence floor = tech_confidence_initial × 0.9) │
│  Applies: Adjustment Scale tier ceiling on confidence delta │
│  Writes:  tech_thesis_final                                 │
│           tech_signal_final                                 │
│           tech_confidence_final                             │
│           persistence_mandate_applied                       │
└───────────────────────────┬─────────────────────────────────┘
        │  add_edge("technical_rebuttal", "fundamental_rebuttal")
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 5 · fundamental_rebuttal           [DEFENSE]          │
│                                                             │
│  Reads:   fund_thesis_initial + risk_critique_fund +        │
│           risk_danger_score                                 │
│  Applies: Margin of Safety Impact assessment                │
│           (risk_score > 60 triggers Valuation Rebasing)     │
│  Applies: Adjustment Scale tier ceiling on confidence delta │
│  Writes:  fund_thesis_final                                 │
│           fund_signal_final                                 │
│           fund_confidence_final                             │
└───────────────────────────┬─────────────────────────────────┘
        │  add_edge("fundamental_rebuttal", "final_node")
        │  AgentState carries all _final thesis fields
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 6 · final_node                    [SYNTHESIS]         │
│                                                             │
│  Reads:   All _final fields from AgentState                 │
│  Writes:  final_signal                                      │
│           final_confidence                                  │
│           final_explanation                                 │
│           → Returned as the API response by main.py         │
└─────────────────────────────────────────────────────────────┘
```

This is a **strict linear chain** — `graph.py` defines the full edge sequence as `START → technical_analyst → fundamental_analyst → risk_manager → technical_rebuttal → fundamental_rebuttal → final_node → END`. The Rebuttal nodes (4 and 5) are the adjudication gatekeepers: no `_final` thesis field can be written before them, and no `_initial` thesis field can be modified after them.

---

## 3. Agent Roster & Schemas

> **Inference Stack:** Every agent in Alpha Council — Technical Analyst, Fundamental Analyst, Risk Manager, and both Rebuttal nodes — runs on **`llama-3.1-8b-instant` via the Groq API**. No closed-source frontier model is used anywhere in the pipeline. This is a deliberate architectural decision: Groq's LPU (Language Processing Unit) delivers sub-second inference per node, making a 6-node sequential pipeline viable in financial market contexts where latency is a first-class constraint. The entire Tribunal — from Constitutional Data injection to `final_node` synthesis — executes in near real-time.

### 3.1 Technical Analyst
*Model: `llama-3.1-8b-instant` · Provider: Groq*

Responsible for chart-derived signals: RSI momentum, beta-relative positioning, and valuation anchoring against Constitutional Data.

**Inputs read from AgentState (Constitutional Data):**
```
rsi, pe_ratio, beta, sector, forward_pe, debt_to_equity
```

**Node output written to AgentState (Phase 1):**
```json
{
  "tech_thesis_initial":    "string",
  "tech_confidence_initial": 0.0
}
```

**Output Schema (Phase 3 — Final Rebuttal):**
```json
{
  "final_explanation": "string",
  "final_signal": "BUY | SELL | HOLD",
  "final_confidence": 0.0,
  "concession_made": true,
  "concession_rationale": "string"
}
```

### 3.2 Fundamental Analyst
*Model: `llama-3.1-8b-instant` · Provider: Groq*

Responsible for earnings-derived signals: revenue trends, margin compression, guidance revisions, P/E relative to sector, and macro sensitivity (Beta).

**Inputs read from AgentState (Constitutional Data + prior thesis):**
```
pe_ratio, forward_pe, beta, debt_to_equity, sector, rsi, tech_thesis_initial
```

**Node output written to AgentState (Phase 1):**
```json
{
  "fund_thesis_initial":    "string",
  "fund_confidence_initial": 0.0
}
```

**Output Schema (Phase 3 — Final Rebuttal):**
```json
{
  "final_explanation": "string",
  "final_signal": "BUY | SELL | HOLD",
  "final_confidence": 0.0,
  "concession_made": false,
  "concession_rationale": "string"
}
```

### 3.3 Risk Arbitrage Engine — Adversarial LLM Auditor
*Model: `llama-3.1-8b-instant` · Provider: Groq*

The Risk Arbitrage Engine is **not** a deterministic arithmetic scorer. It is an LLM-driven Adversarial Auditor — the same open-weights model running under a maximally adversarial `RISK_CRITIQUE_PROMPT` — whose sole mandate is to identify evidence that contradicts the prevailing signal. The choice of Groq here is critical: the Auditor must process both theses plus Constitutional Data and return a structured verdict fast enough to remain in-pipeline. On Groq's LPU, this node completes in well under a second.

The Auditor is constrained by a **Materiality Matrix** that forces it to classify any risk it identifies into one of four severity levels before it may contribute that risk to the `risk_score`:

```
╔═════════╦════════════════════════════════╦══════════════════════╗
║  Level  ║  Classification Criteria       ║  Score Contribution  ║
╠═════════╬════════════════════════════════╬══════════════════════╣
║   L1    ║  Noise / Unverified            ║  0 pts — discarded   ║
║   L2    ║  Confirmed but Immaterial      ║  1–20 pts            ║
║   L3    ║  Confirmed and Material        ║  21–50 pts           ║
║   L4    ║  Confirmed, Material, Urgent   ║  51–100 pts          ║
╚═════════╩════════════════════════════════╩══════════════════════╝
```

The Auditor cannot submit a risk claim at L3 or L4 without citing the specific Constitutional Data field or pre-validated news evidence that substantiates the classification. Unsubstantiated claims are forced to L1 and contribute zero points to the `risk_score`. This prevents the Auditor from inflating risk scores through confident-sounding but evidentially hollow arguments.

The `risk_score` produced by the Auditor is the direct input to the **Adjustment Scale** (§6), which is the deterministic post-processing layer that maps the score to a tier and governs the maximum confidence penalty the rebuttal agents may receive. The Auditor generates the verdict; the Adjustment Scale determines its consequences.

---

## 4. Constitutional Data — The Truth Anchor

**Fetch Timing:** Constitutional Data is retrieved in `main.py` — the entry point — *before* `agent/graph.py` is invoked and the graph begins execution. This is architecturally intentional. The data fetch is not delegated to an agent node; it is a prerequisite for graph initialization. The fully populated Constitutional Data payload is injected directly into `AgentState` at construction time, making it available to every subsequent node as immutable shared state.

```python
# main.py — executed before graph.compile() is called
constitutional_data = fetch_constitutional_data(ticker)   # yfinance
state = AgentState(ticker=ticker, **constitutional_data)  # injected at construction
graph = build_graph()
result = graph.invoke(state)
```

The payload is designated **Constitutional Data** — it cannot be overwritten by any agent node during graph execution. Every field is sourced exclusively from `yfinance` via the `get_constitutional_data(ticker)` function in `main.py`. The exact fields fetched are:

```python
CONSTITUTIONAL_DATA = {
  "ticker":          str,    # e.g. "AAPL"
  "pe_ratio":        float,  # Trailing P/E ratio
  "forward_pe":      float,  # Forward P/E (next fiscal year consensus estimate)
  "beta":            float,  # 1-year Beta vs. S&P 500
  "debt_to_equity":  float,  # Total Debt / Shareholders' Equity
  "sector":          str,    # e.g. "Technology", "Healthcare"
  "rsi":             float,  # 14-period Relative Strength Index (calculated from price history)
}
```

> **Note on SMA values:** `sma_20`, `sma_50`, raw price, and volume are **not** included in the `audit_data` dictionary passed to agents. RSI is calculated from the raw price history DataFrame returned by `yf.Ticker.history()` and is the sole price-derived metric injected into state. If chart-level analysis requiring SMA context is needed, it must be derived by the Technical Analyst from the RSI reading and Constitutional Data, not from raw SMA fields.

**Data Sovereignty Rules:**

1. **Agents may not contradict Constitutional Data.** If `rsi` is 72 (overbought), a Technical Analyst that generates a high-confidence BUY must explicitly address and reconcile the RSI reading in its thesis. An unaddressed contradiction is flagged as a CoT Guardrail violation.

2. **Constitutional Data acts as a tie-breaker in Rebuttal.** If the Risk Score falls in the Warning Zone (31–60) and the two agents' signals conflict, the agent whose thesis is *directionally consistent* with the Constitutional Data reading is granted the lower confidence penalty.

3. **Confidence scores must be numerically traceable to Constitutional Data.** An agent claiming 85% confidence on a SELL when `beta = 0.4` (low volatility) and `rsi = 45` (neutral) must provide a quantitative justification in its `final_explanation` field. The system prompt makes this a mandatory schema requirement, not a stylistic suggestion.

4. **`sector`, `pe_ratio`, `forward_pe`, and `debt_to_equity` are Fundamental Analyst anchors.** The Fundamental Analyst must benchmark `pe_ratio` against the sector median and compare `pe_ratio` vs `forward_pe` to assess whether the market is pricing in growth or deterioration. A high-confidence BUY on a stock with `debt_to_equity > 2.0` in a rising-rate environment requires explicit reconciliation in `fund_thesis_initial`.

---

## 5. The Persistence Mandate

The most critical guardrail in Alpha Council is the **Persistence Mandate**, which governs the Technical Analyst's behavior during the Rebuttal phase.

### Definition

> *The Technical Analyst is programmatically forbidden from lowering its `final_confidence` by more than 10 percentage points relative to its `initial_confidence` if the computed Risk Score is below 35.*

### Rationale

A Risk Score below 35 indicates that the opposing critique is weak — it lacks the chart evidence, concrete data references, or structural argumentation necessary to constitute a credible threat to the original thesis. In this scenario, a traditional LLM would still frequently capitulate due to the conversational framing of the critique (e.g., an authoritative tone, a longer response, or confident-sounding language). The Persistence Mandate eliminates this failure mode entirely.

**This is not a prompt instruction. It is enforced in code:**

```python
def apply_persistence_mandate(
    initial_confidence: float,
    proposed_confidence: float,
    risk_danger_score: float
) -> float:
    """
    Enforces the Persistence Mandate.
    If risk_danger_score < 35, the confidence drop is hard-capped at 10 points.
    This function is the last transformation applied before final_confidence
    is written to AgentState.
    """
    if risk_danger_score < 35:
        floor = initial_confidence - 10.0
        return max(proposed_confidence, floor)
    return proposed_confidence
```

The LLM's proposed `final_confidence` is passed through `apply_persistence_mandate()` before it is ever written to `AgentState`. The model may *attempt* to lower confidence by 30 points — the function silently corrects this to 10 points. The agent's `concession_made` field is set to `False` if a correction was applied.

### Why This Prevents Sentiment Drift

Sentiment Drift is defined as the progressive decay of a legitimate signal caused by repeated exposure to opposing arguments — not by new data. It is the LLM equivalent of a junior analyst abandoning a correct position because a senior analyst spoke confidently. The Persistence Mandate creates an asymmetry: confidence can only be substantially reduced when the Risk Score *earns* that reduction.

---

## 6. The Three-Tier Adjustment Scale

When the Rebuttal phase executes, the computed Risk Score is mapped to one of three adjudication tiers. Each tier defines the maximum allowable confidence penalty and the conditions under which a signal flip is permitted.

```
╔══════════════════════════════════════════════════════════════╗
║                   ADJUSTMENT SCALE v1.0                     ║
╠════════════════╦══════════════╦══════════════════════════════╣
║   Risk Score   ║     Zone     ║         Adjudication Rules   ║
╠════════════════╬══════════════╬══════════════════════════════╣
║    0 – 30      ║  PERSISTENCE ║  Thesis confirmed.           ║
║                ║     ZONE     ║  Signal: no flip permitted.  ║
║                ║              ║  Penalty: < 10% max.         ║
╠════════════════╬══════════════╬══════════════════════════════╣
║   31 – 60      ║   WARNING    ║  Signal flip only if chart   ║
║                ║     ZONE     ║  evidence (SMA break OR      ║
║                ║              ║  support breach) is cited.   ║
║                ║              ║  Penalty: < 25% max.         ║
╠════════════════╬══════════════╬══════════════════════════════╣
║   61 – 100     ║    KILL-     ║  Immediate downgrade.        ║
║                ║   SIGNAL     ║  Signal flip: unconditional. ║
║                ║              ║  Penalty: 50% applied.       ║
╚════════════════╩══════════════╩══════════════════════════════╝
```

### Tier Mechanics

**Persistence Zone (0–30):** The critique has failed to produce material risk evidence. The originating agent's thesis is confirmed. The agent *may* produce a concession in natural language (acknowledging a valid point), but this concession cannot manifest as a `final_confidence` reduction exceeding 10 points, and `final_signal` must match `initial_signal`.

**Warning Zone (31–60):** The critique has identified legitimate risk factors but has not provided dispositive evidence. A signal flip is *conditionally* permitted — the condition being that the critique must have explicitly cited at least one of the CoT Guardrail criteria (see §7): an SMA 20 or SMA 50 break, a support level breach, or a KPI miss. If this condition is not met, the signal holds and only the confidence penalty (< 25%) is applied.

**Kill-Signal Zone (61–100):** The critique has produced overwhelming counter-evidence. The orchestrator applies a hard 50-point confidence penalty to `initial_confidence` to derive `final_confidence`, regardless of what the LLM proposes. `final_signal` is unconditionally flipped from the original. `concession_made` is set to `True`.

```python
def apply_adjustment_scale(
    initial_signal: str,
    initial_confidence: float,
    risk_danger_score: float,
    critique_has_chart_evidence: bool
) -> tuple[str, float, bool]:
    """
    Returns (final_signal, final_confidence, concession_made)
    """
    if risk_danger_score <= 30:
        penalty = min(initial_confidence * 0.10, 10.0)
        return initial_signal, initial_confidence - penalty, False

    elif risk_danger_score <= 60:
        penalty = min(initial_confidence * 0.25, 25.0)
        if critique_has_chart_evidence:
            flipped = "SELL" if initial_signal == "BUY" else "BUY"
            return flipped, initial_confidence - penalty, True
        return initial_signal, initial_confidence - penalty, False

    else:  # Kill-Signal
        penalty = 50.0
        flipped = "SELL" if initial_signal == "BUY" else "BUY"
        return flipped, max(initial_confidence - penalty, 0.0), True
```

---

## 7. Chain-of-Thought (CoT) Guardrails

Before any agent is permitted to modify its `initial_signal` or reduce `initial_confidence` by more than a trivial margin, it must validate **three specific criteria** drawn from Constitutional Data. This requirement is embedded in the system prompt as a mandatory pre-flight checklist that the agent must complete *before* producing its final output fields.

The three criteria are:

| # | Criterion | Relevant Constitutional Field | Validation Logic |
|---|-----------|-------------------------------|-----------------|
| 1 | **RSI Threshold Breach** | `rsi` | RSI > 70 = overbought (bearish pressure). RSI < 30 = oversold (bullish reversal candidate). Any signal in tension with this reading requires a stated reconciliation. |
| 2 | **Valuation Divergence** | `pe_ratio`, `forward_pe` | `forward_pe` significantly below `pe_ratio` signals expected earnings growth (bullish). The reverse signals expected contraction. A SELL thesis on a stock where `forward_pe` < `pe_ratio` * 0.85 requires explicit justification. |
| 3 | **KPI / Leverage Risk** | `debt_to_equity`, `beta` | Elevated `debt_to_equity` (> 2.0) combined with high `beta` (> 1.5) constitutes a KPI risk flag. A BUY signal under these conditions must acknowledge the amplified downside in stress scenarios. |

**An agent that proposes a signal change without validating all three criteria produces an invalid output.** The orchestrator checks the reasoning trace against these criteria before writing to `AgentState`. If validation fails, the agent is re-prompted once with an explicit directive to complete the checklist. A second failure results in the original `initial_signal` and `initial_confidence` being preserved unchanged.

This guardrail is intentionally conservative. The system would rather preserve a stale-but-sound thesis than accept a signal change that cannot be traced to quantifiable evidence.

---

## 8. The State-Accumulation Pipeline — Node-by-Node

### Node 1: technical_analyst

The first graph node to execute. It receives `AgentState` populated exclusively with Constitutional Data. The Technical Analyst generates a momentum and sentiment thesis grounded in `rsi`, `beta`, and `pe_ratio`, then writes `tech_thesis_initial`, `tech_signal_initial`, and `tech_confidence_initial` to state. No `_final` fields are written here — this node's outputs are initial positions only, subject to revision in Node 4.

### Node 2: fundamental_analyst

Executes second, receiving `AgentState` that now contains the Technical Analyst's completed output. The Fundamental Analyst has full visibility of `tech_thesis_initial` in state — this is the correct behavior of a sequential accumulation pipeline. It is expected to produce an *independent* assessment anchored to `pe_ratio`, `forward_pe`, `debt_to_equity`, and `sector`. It writes `fund_thesis_initial`, `fund_signal_initial`, and `fund_confidence_initial` to state. Like the TA, none of these fields are final — they are the positions the Fundamental Analyst will be required to *defend* in Node 5.

### Node 3: risk_manager

The adversarial pivot point of the pipeline. With both initial theses resident in `AgentState`, the Groq-hosted Adversarial Auditor executes under the `RISK_CRITIQUE_PROMPT`. It reviews both theses against Constitutional Data and any pre-validated material evidence, classifies each risk vector via the Materiality Matrix (L1–L4), and produces two targeted critiques — `risk_critique_tech` and `risk_critique_fund` — directed at each analyst independently, plus a unified `risk_danger_score`. The Adjustment Scale maps the score to an `adjustment_tier` (`PERSISTENCE`, `WARNING`, or `KILL_SIGNAL`), which is written to state immediately. Both `risk_danger_score` and `adjustment_tier` are **immutable from this point forward** — no downstream node may alter them.

### Node 4: technical_rebuttal

This is where the **Persistence Mandate is enforced**. The `technical_rebuttal` node receives `tech_thesis_initial`, `risk_critique_tech`, and the locked `risk_danger_score` from `AgentState`. The Technical Analyst is instructed to respond to the auditor's targeted attack — but the Adjustment Scale governs what response is structurally permissible:

- If `risk_danger_score < 35` (Persistence Zone): the analyst must maintain at least 90% of `tech_confidence_initial`. The Persistence Mandate floor is applied in code. `persistence_mandate_applied` is set to `True` if the LLM's proposed confidence would have fallen below this floor.
- If `risk_danger_score` is 31–60 (Warning Zone): confidence may be reduced by up to 25%, and a signal flip requires cited evidence.
- If `risk_danger_score > 60` (Kill-Signal): a 50-point confidence penalty is applied unconditionally.

The node writes `tech_thesis_final`, `tech_signal_final`, and `tech_confidence_final` to state. These are the Technical Analyst's definitive, post-adjudication positions.

### Node 5: fundamental_rebuttal

The Fundamental Analyst's equivalent defence. This node receives `fund_thesis_initial`, `risk_critique_fund`, and `risk_danger_score`, and applies the same Adjustment Scale tier logic. Additionally, it performs a **Margin of Safety Impact** assessment: if the `risk_score` reflects a high-severity risk event (e.g., litigation discovery, fraud, structural leverage exposure surfaced at L4), the node is instructed to execute a **Valuation Rebasing** — a structured downward revision of the fundamental valuation anchor, independent of the confidence penalty. This can result in a signal flip even within the Warning Zone if the rebased valuation no longer supports the initial signal.

The node writes `fund_thesis_final`, `fund_signal_final`, and `fund_confidence_final` to state.

### Node 6: final_node

The terminal synthesis node. It reads all six `_final` fields from `AgentState` — both analysts' defended positions — and produces a single consolidated verdict. It resolves any remaining signal disagreement between the two rebuttal outputs (e.g., TA final = BUY, FA final = HOLD) using a weighted synthesis informed by the `adjustment_tier` and `risk_score`. The node writes `final_signal`, `final_confidence`, and `final_explanation` to state. `main.py` reads these three fields directly from the returned state and packages them into the API response.

---

## 9. AgentState — Canonical Data Model

`AgentState` is the single source of truth for the swarm's working memory, defined in `agent/state.py`. It is constructed in `main.py` with Constitutional Data pre-loaded before the graph executes, then passed through each node in `agent/graph.py`. Every agent reads from it and writes back to it — there is no other inter-agent communication channel.

```python
from dataclasses import dataclass
from typing import Optional, Literal

Signal = Literal["BUY", "SELL", "HOLD"]
Tier   = Literal["PERSISTENCE", "WARNING", "KILL_SIGNAL"]

@dataclass
class AgentState:
    # ── Identity ─────────────────────────────────────────────────
    ticker: str

    # ── Constitutional Data (fetched in main.py, immutable) ──────
    # Source: yfinance get_constitutional_data(ticker)
    # Injected into state BEFORE graph.invoke() is called.
    pe_ratio:        float   # Trailing P/E
    forward_pe:      float   # Forward P/E (next FY consensus)
    beta:            float   # 1-year Beta vs. S&P 500
    debt_to_equity:  float   # Total Debt / Shareholders' Equity
    sector:          str     # e.g. "Technology"
    rsi:             float   # 14-period RSI (calculated from price history)

    # ── Node 1 Output: Technical Analyst ─────────────────────────
    tech_thesis_initial:      Optional[str]    = None
    tech_confidence_initial:  Optional[float]  = None

    # ── Node 2 Output: Fundamental Analyst ───────────────────────
    fund_thesis_initial:      Optional[str]    = None
    fund_confidence_initial:  Optional[float]  = None
    fa_kpi_miss_detected:     Optional[bool]   = None

    # ── Node 3 Output: Risk Manager ──────────────────────────────
    risk_critique_tech:       Optional[str]    = None   # targeted critique of tech thesis
    risk_critique_fund:       Optional[str]    = None   # targeted critique of fund thesis
    risk_danger_score:        Optional[float]  = None   # from Materiality Matrix (L1–L4)
    adjustment_tier:          Optional[Tier]   = None   # PERSISTENCE | WARNING | KILL_SIGNAL
    # risk_danger_score and adjustment_tier are immutable after this node

    # ── Node 4 Output: Technical Rebuttal ────────────────────────
    # Written only after Persistence Mandate + Adjustment Scale applied
    tech_thesis_final:        Optional[str]    = None
    tech_signal_final:        Optional[Signal] = None
    tech_confidence_final:    Optional[float]  = None
    persistence_mandate_applied: Optional[bool] = None  # True if floor was enforced

    # ── Node 5 Output: Fundamental Rebuttal ──────────────────────
    # Written only after Margin of Safety assessment + Adjustment Scale applied
    fund_thesis_final:        Optional[str]    = None
    fund_signal_final:        Optional[Signal] = None
    fund_confidence_final:    Optional[float]  = None
    valuation_rebasing_applied: Optional[bool] = None   # True if L4 risk triggered rebase

    # ── Node 6 Output: Final Node (API-facing) ───────────────────
    final_signal:             Optional[Signal] = None   # synthesized from both _final signals
    final_confidence:         Optional[float]  = None   # weighted synthesis output
    final_explanation:        Optional[str]    = None   # consolidated verdict narrative
```

> **Field naming convention:** `_initial` fields (thesis + confidence only) are written by Nodes 1–2 and are never overwritten. `_final` fields are written exclusively by Nodes 4–5 and represent post-adjudication positions. `risk_danger_score` and `adjustment_tier` are written by Node 3 and are immutable thereafter. `risk_critique_tech` and `risk_critique_fund` are the two targeted critiques produced by the Risk Manager — one for each analyst — and are what the rebuttal nodes actually read. `final_signal`, `final_confidence`, and `final_explanation` are Node 6 outputs and the only fields `main.py` reads when constructing the API response.

---

## 10. API Output Contract

`main.py` constructs its return dictionary by reading `final_signal`, `final_confidence`, and `final_explanation` directly from the completed `AgentState`, then assembling the four sub-objects below. Every key is traceable to a specific `AgentState` field.

```json
{
  "ticker": "AAPL",

  "final_verdict": {
    "signal":      "BUY",
    "confidence":  72.0,
    "explanation": "RSI of 67.4 signals momentum without confirmed overbought breach. P/E of 28.3 vs. forward P/E of 24.1 indicates market is pricing in earnings expansion — directionally bullish. Beta of 1.21 acknowledged as elevated; confidence penalized by 12 points per WARNING tier ceiling. Persistence Mandate not triggered (risk_score: 44)."
  },

  "technical_analysis": {
    "thesis":     "Audit challenge on beta-amplified downside acknowledged. RSI not in confirmed reversal zone. Initial thesis sustained with reduced conviction.",
    "confidence": 72.0
  },

  "fundamental_analysis": {
    "thesis":     "Forward P/E compression thesis intact. No L4 risk event identified; Valuation Rebasing not triggered. Confidence adjusted per WARNING ceiling.",
    "confidence": 58.0
  },

  "risk_analysis": {
    "score":    44.0,
    "critique": "While forward P/E compression appears bullish, beta of 1.21 creates asymmetric downside in a risk-off rotation. RSI proximity to 70 is unpriced in the current confidence levels. Classified L3 — Confirmed and Material. Risk score: 44."
  },

  "constitutional_data": {
    "pe_ratio":        28.3,
    "forward_pe":      24.1,
    "beta":            1.21,
    "debt_to_equity":  1.8,
    "sector":          "Technology",
    "rsi":             67.4
  }
}
```

**Integrity guarantee:** `final_verdict.final_signal` and `final_verdict.final_confidence` are Node 6 outputs, synthesized from `tech_signal_final` / `fund_signal_final` — which are themselves the post-Persistence-Mandate, post-Adjustment-Scale outputs of Nodes 4 and 5. No LLM output reaches the API response without passing through at least one deterministic enforcement layer. Consumers should treat `final_verdict` as the sole authoritative signal; all sub-objects constitute the complete, node-by-node reasoning audit trail.

---

## 11. Installation & Quickstart

### Prerequisites

```bash
python >= 3.11
```

### Install

```bash
git clone https://github.com/your-org/alpha-council.git
cd alpha-council
pip install -r requirements.txt
```

### Environment

```bash
cp .env.example .env
# Required key:
#   GROQ_API_KEY  — Powers all six nodes: Technical Analyst, Fundamental Analyst,
#                   Risk Manager, Technical Rebuttal, Fundamental Rebuttal, Final Node.
#                   Model: llama-3.1-8b-instant
```

### Run

```bash
python main.py --ticker AAPL
```

### Run with custom risk threshold

```bash
python main.py --ticker TSLA --kill-signal-threshold 65
```

### Output

Results are written to `stdout` as JSON and optionally to `./runs/{run_id}.json`.

---

## 12. Design Philosophy

Alpha Council is predicated on a single thesis: **the problem with LLMs in high-stakes domains is not intelligence — it is accountability.**

A frontier model has sufficient reasoning capacity to produce a sound financial thesis. The failure occurs in the adversarial context: when a critique arrives, the model has no structural reason to hold its ground. It has been trained to be helpful, agreeable, and cooperative. These are catastrophic properties for an analyst.

Alpha Council's architecture treats the LLM as a capable but untrustworthy sub-component. The agents are not asked to be disciplined — they are *made* disciplined by the layers above them:

- **Constitutional Data** prevents factual hallucination by providing a ground truth that cannot be argued away.
- **The Persistence Mandate** prevents confidence collapse under low-quality adversarial pressure.
- **The Adjustment Scale** prevents arbitrary signal flips by requiring proportionate evidence for proportionate changes.
- **CoT Guardrails** prevent hand-wavy reasoning by mandating specific, verifiable criteria before any modification is accepted.
- **Inference Efficiency via Groq LPU** proves that deterministic multi-agent debate does not require closed-source frontier latency. By running `llama-3.1-8b-instant` on Groq's Language Processing Unit — purpose-built silicon optimised for sequential token generation — the entire six-node Tribunal executes in near real-time. This is not a prototype trade-off; it is the thesis: open-weights models, constrained by rigorous architecture, outperform unconstrained closed-source models on structured reasoning tasks where the evaluation criteria are deterministic. Speed and rigor are not in tension. On the right hardware stack, they are the same thing.

The result is a system where the LLM's primary contribution is language and reasoning fluency — and the system's architecture provides the rigor, the speed, and the accountability that language models alone cannot guarantee.

> *Not a chatbot. A council. Not a frontier model. An open-weights logic engine.*

---

## License

MIT License. See `LICENSE` for details.

---

## Contributing

Pull requests are welcome. For architectural changes to the adjudication pipeline — particularly the Adjustment Scale thresholds or Persistence Mandate parameters — please open an issue first to discuss the empirical basis for the proposed change.

---

*Alpha Council is not financial advice. It is a research framework for studying deterministic constraint mechanisms in multi-agent LLM systems.*
