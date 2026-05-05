import json
from datetime import date, datetime

import streamlit as st

st.set_page_config(page_title="TPM Executive Status", layout="wide")

# -----------------------------
# Theme / Styling
# -----------------------------
if "light_mode" not in st.session_state:
    st.session_state["light_mode"] = False
if "section_focus" not in st.session_state:
    st.session_state["section_focus"] = "all"

bg = "#ffffff" if st.session_state["light_mode"] else "#0b1020"
panel = "#f8fafc" if st.session_state["light_mode"] else "#111827"
border = "#e5e7eb" if st.session_state["light_mode"] else "#374151"
text_muted = "#475569" if st.session_state["light_mode"] else "#9ca3af"

st.markdown(
    f"""
<style>
.main .block-container {{
    max-width: 1200px;
}}
.status-card {{
    padding: 14px 16px;
    border-radius: 10px;
    background: {panel};
    border: 1px solid {border};
    margin-bottom: 12px;
}}
.badge {{
    display:inline-block;
    padding:2px 10px;
    border-radius:999px;
    font-weight:700;
    font-size:12px;
    margin-right:8px;
}}
.badge-green {{background:#064e3b; color:#a7f3d0;}}
.badge-yellow {{background:#78350f; color:#fde68a;}}
.badge-red {{background:#7f1d1d; color:#fecaca;}}
.small-muted {{color:{text_muted}; font-size:12px;}}
.tile-note {{font-size:12px; color:{text_muted}; margin-top:2px;}}
.section-card {{
    border: 1px solid {border};
    border-radius: 10px;
    padding: 16px;
    margin-top: 10px;
    background: {panel};
}}
.table-pill {{
    font-weight:700;
    padding:2px 8px;
    border-radius:999px;
}}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Data Model
# -----------------------------
DEFAULT_SIGNALS = {
    "program_name": "Enterprise Data Platform Modernization",
    "org": "Data & AI Platform",
    "quarter": "Q2 FY2026",
    "sprint_label": "Sprint 24 | Week of May 5, 2026",
    "prepared_by": "Pompee Chakraborty, TPM",
    "report_version": "v1.3",
    "reporting_date": str(date.today()),
    "big_rock_status": "Green",
    "initiative_status": "Yellow",
    "jira": {
        "sprint_completion_pct": 78,
        "target_completion_pct": 85,
        "sprint_delta_vs_last_week": -4,
    },
    "defects": {
        "sev1_current": 5,
        "sev1_last_week": 3,
        "open_total": 23,
    },
    "use_cases": {
        "live_current": 2,
        "live_target_q_end": 8,
    },
    "workstreams": [
        {
            "name": "Zero Copy Connectors",
            "status": "Green",
            "update": "Connector build complete; OAuth federation integrated.",
            "next": "Delta/Iceberg UX complete by May 10, 2026.",
        },
        {
            "name": "Trino Runtime",
            "status": "Green",
            "update": "Operational in core region; expansion pending compliance signoff.",
            "next": "Secondary region target May 12, 2026.",
        },
        {
            "name": "Data Product Experience",
            "status": "Yellow",
            "update": "Scope and sequencing decisions still open.",
            "next": "Scope baseline signoff at steering review on May 12, 2026.",
        },
    ],
    "risks": [
        {
            "id": "RSK-101",
            "description": "Scope/timeline misalignment may impact downstream milestones.",
            "impact": "High",
            "mitigation": "Finalize scope baseline, dependency sequencing, and design signoff.",
            "owner": "Program PM",
            "due": "May 12, 2026",
            "status": "WIP",
        },
        {
            "id": "RSK-088",
            "description": "Platform modernization scope-resource tradeoff risk.",
            "impact": "High",
            "mitigation": "Escalate priority decisions and rebalance capacity.",
            "owner": "Engineering Director",
            "due": "May 9, 2026",
            "status": "Mitigated",
        },
    ],
    "decisions_needed": [
        {
            "decision": "Approve temporary capacity shift to Sev-1/Sev-2 defect reduction for one sprint.",
            "owner": "Engineering Director",
            "due": "May 9, 2026",
            "implication": "Prevents quality spillover into Sprint 25 and protects release confidence.",
        },
        {
            "decision": "Approve contingency sequencing plan for external dependency variance.",
            "owner": "Portfolio Steering Committee",
            "due": "May 12, 2026",
            "implication": "Maintains milestone confidence if dependency slips by >5 business days.",
        },
    ],
}

# -----------------------------
# Helpers
# -----------------------------
def status_badge(label: str, status: str) -> str:
    lower = status.lower()
    if "green" in lower or "mitigated" in lower:
        cls = "badge-green"
    elif "yellow" in lower or "risk" in lower or "wip" in lower:
        cls = "badge-yellow"
    else:
        cls = "badge-red"
    return f'<span class="badge {cls}">{label}: {status}</span>'


def status_pill(status: str) -> str:
    lower = status.lower()
    if "green" in lower:
        return f"<span class='table-pill' style='background:#064e3b;color:#a7f3d0'>{status}</span>"
    if "yellow" in lower:
        return f"<span class='table-pill' style='background:#78350f;color:#fde68a'>{status}</span>"
    return f"<span class='table-pill' style='background:#7f1d1d;color:#fecaca'>{status}</span>"


def health_summary(signals: dict) -> tuple[str, str]:
    sev1 = signals["defects"]["sev1_current"]
    sprint = signals["jira"]["sprint_completion_pct"]
    target = signals["jira"]["target_completion_pct"]
    yellow_streams = sum(1 for w in signals["workstreams"] if w["status"].lower() == "yellow")

    if sev1 >= 5 or sprint < target - 5:
        health = "Yellow"
    else:
        health = "Green"

    narrative = (
        f"{len(signals['workstreams']) - yellow_streams} of {len(signals['workstreams'])} workstreams are on track; "
        "Data Product Experience scope risk is being resolved in the next steering review, "
        "with decision required by May 12, 2026."
    )
    return health, narrative


def insights_block(signals: dict) -> str:
    sprint = signals["jira"]["sprint_completion_pct"]
    target = signals["jira"]["target_completion_pct"]
    sprint_delta = signals["jira"]["sprint_delta_vs_last_week"]
    sev1_now = signals["defects"]["sev1_current"]
    sev1_prev = signals["defects"]["sev1_last_week"]
    sev1_delta = sev1_now - sev1_prev

    sprint_implication = (
        "At current burn, milestone confidence is reduced; scope tiering needed to recover by Sprint 25."
        if sprint < target
        else "Delivery is aligned with target trajectory."
    )
    sev1_implication = (
        "Quality pressure is increasing; defect swarming required to avoid carryover risk."
        if sev1_delta > 0
        else "Quality trend is stabilizing."
    )

    sprint_delta_txt = f"{sprint_delta:+d} pts vs last week"
    sev1_delta_txt = f"{sev1_delta:+d} vs last week"

    return f"""
- **Sprint completion:** {sprint}% vs target {target}% (**{sprint_delta_txt}**)  
  *So what:* {sprint_implication}
- **Sev-1 defects:** {sev1_now} (**{sev1_delta_txt}**)  
  *So what:* {sev1_implication}
- **Execution signal:** Architecture and dependency governance reviews completed; gated execution is continuing.
"""


def render_workstream_table(workstreams: list[dict]) -> str:
    rows = []
    for w in workstreams:
        rows.append(
            f"| {w['name']} | {status_pill(w['status'])} | {w['update']} | {w['next']} |"
        )
    return (
        "| Workstream | Status | Current update | Next milestone |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows)
    )


def render_risk_table(risks: list[dict]) -> str:
    rows = []
    for r in risks:
        rows.append(
            f"| {r['id']} | {r['impact']} | {r['description']} | {r['mitigation']} | {r['status']} | {r['owner']} | {r['due']} |"
        )
    return (
        "| Risk ID | Impact | Description | Mitigation | Status | Owner | Due |\n"
        "|---|---|---|---|---|---|---|\n"
        + "\n".join(rows)
    )


def render_decisions(decisions: list[dict]) -> str:
    lines = []
    for d in decisions:
        lines.append(
            f"- **Decision:** {d['decision']}\n"
            f"  - Owner: {d['owner']}\n"
            f"  - Due: {d['due']}\n"
            f"  - Implication: {d['implication']}"
        )
    return "\n".join(lines)


def metric_tile(col, label: str, value: str, key: str, note: str):
    if col.button(f"{value}\n{label}", use_container_width=True, key=f"tile_{key}"):
        st.session_state["section_focus"] = key
    col.markdown(f"<div class='tile-note'>{note}</div>", unsafe_allow_html=True)


def build_report(signals: dict):
    health, narrative = health_summary(signals)
    report = {
        "summary": narrative,
        "health": health,
        "highlights": insights_block(signals),
        "timeline": render_workstream_table(signals["workstreams"]),
        "risks": render_risk_table(signals["risks"]),
        "decisions": render_decisions(signals["decisions_needed"]),
    }
    return report


# -----------------------------
# Header / Context
# -----------------------------
top_left, top_right = st.columns([3, 1])
with top_left:
    st.title("Program Portfolio — Executive Status Brief")
    st.caption(
        f"Program: **{DEFAULT_SIGNALS['program_name']}** | Org: **{DEFAULT_SIGNALS['org']}** | "
        f"{DEFAULT_SIGNALS['quarter']} | {DEFAULT_SIGNALS['sprint_label']}"
    )
with top_right:
    if st.toggle("Light export view", value=st.session_state["light_mode"]):
        st.session_state["light_mode"] = True
    else:
        st.session_state["light_mode"] = False

report = build_report(DEFAULT_SIGNALS)
health = report["health"]

summary_html = (
    "<div class='status-card'><strong>Executive Summary</strong><br><br>"
    + status_badge("Strategic Use Cases", DEFAULT_SIGNALS["big_rock_status"])
    + status_badge("Platform Initiatives", DEFAULT_SIGNALS["initiative_status"])
    + status_badge("Overall Health", health)
    + f"<div style='margin-top:10px'>{report['summary']}</div>"
    + f"<div class='small-muted'>Prepared by: {DEFAULT_SIGNALS['prepared_by']} | "
      f"Report date: {DEFAULT_SIGNALS['reporting_date']} | Version: {DEFAULT_SIGNALS['report_version']}</div></div>"
)
st.markdown(summary_html, unsafe_allow_html=True)

# -----------------------------
# Progress Metric Visualization
# -----------------------------
live = DEFAULT_SIGNALS["use_cases"]["live_current"]
target_live = DEFAULT_SIGNALS["use_cases"]["live_target_q_end"]
progress_pct = int((live / target_live) * 100) if target_live else 0

st.markdown("### Success Trajectory")
st.progress(progress_pct, text=f"Use cases live: {live}/{target_live} ({progress_pct}%) toward quarter target")

# -----------------------------
# Quick Navigation / Filtering
# -----------------------------
st.markdown("### Quick Navigation")
c1, c2, c3, c4, c5 = st.columns(5)
metric_tile(c1, "Highlights", "01", "highlights", "Click to focus section")
metric_tile(c2, "Timeline", "02", "timeline", "Click to focus section")
metric_tile(c3, "Risks", "03", "risks", "Click to focus section")
metric_tile(c4, "Decisions", "04", "decisions", "Click to focus section")
metric_tile(c5, "Metrics", "05", "metrics", "Click to focus section")

if st.button("Show full report", use_container_width=True):
    st.session_state["section_focus"] = "all"

focus = st.session_state["section_focus"]
if focus != "all":
    st.info(f"Focused view: {focus.title()}")

# -----------------------------
# Section Rendering
# -----------------------------
def section(title: str, content: str):
    st.markdown(f"<div class='section-card'><h2>{title}</h2>{content}</div>", unsafe_allow_html=True)

if focus in ("all", "highlights"):
    section("Key Highlights", st.markdown(report["highlights"]) or "")
    st.markdown(report["highlights"])

if focus in ("all", "timeline"):
    st.markdown("## Program Timeline & Status")
    st.markdown(report["timeline"], unsafe_allow_html=True)

if focus in ("all", "risks"):
    st.markdown("## Top Issues and Risks")
    st.markdown(report["risks"], unsafe_allow_html=True)

if focus in ("all", "decisions"):
    st.markdown("## Decisions Required from Leadership")
    st.markdown(report["decisions"])

if focus in ("all", "metrics"):
    st.markdown("## Success Metrics")
    st.markdown(
        f"- **Quarter objective:** {target_live} live use cases\n"
        f"- **Current status:** {live} live ({progress_pct}%)\n"
        f"- **Trajectory:** {'On track' if progress_pct >= 50 else 'Needs acceleration'}"
    )

# -----------------------------
# Internal / TPM-only controls
# -----------------------------
with st.expander("Internal editor (for TPM use)"):
    st.caption("Optional: edit raw input signals for scenario testing.")
    raw = st.text_area("Input Signals JSON", value=json.dumps(DEFAULT_SIGNALS, indent=2), height=260)
    if st.button("Regenerate from edited signals"):
        try:
            parsed = json.loads(raw)
            report = build_report(parsed)
            st.success("Report regenerated in current session. Re-run section focus as needed.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")