import json
from datetime import date

import streamlit as st

st.set_page_config(page_title="TPM Executive Status", layout="wide")

st.markdown(
    """
<style>
.status-card {padding: 14px 16px; border-radius: 10px; background: #111827; border: 1px solid #374151; margin-bottom: 12px;}
.badge {display:inline-block; padding:2px 10px; border-radius:999px; font-weight:700; font-size:12px; margin-right:8px;}
.badge-green {background:#064e3b; color:#a7f3d0;}
.badge-yellow {background:#78350f; color:#fde68a;}
.badge-red {background:#7f1d1d; color:#fecaca;}
.small-muted {color:#9ca3af; font-size:12px;}
.tile-note {font-size:12px; color:#9ca3af; margin-top:2px;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Program Portfolio — Executive Status Brief")
st.caption("Objective: Provide a concise, decision-ready summary of portfolio health, risks, and actions.")

DEFAULT_SIGNALS = {
    "week_of": str(date.today()),
    "big_rock_status": "Green",
    "initiative_status": "Yellow",
    "jira": {"sprint_completion_pct": 78, "target_completion_pct": 85},
    "defects": {"open_total": 23, "sev1": 5},
    "okrs": [
        {"name": "Adoption target", "status": "At risk", "note": "Flagship use case launch remains dependent on platform readiness milestones."},
        {"name": "Use cases delivered", "status": "2/8", "note": "Two use cases are live; broader pipeline is in staged rollout."},
    ],
    "workstreams": [
        {"name": "Zero Copy Connectors", "status": "Green", "update": "Connector build complete; auth federation integrated.", "next": "Delta/Iceberg UX complete by Oct 10."},
        {"name": "Trino Runtime", "status": "Green", "update": "Operational in core region; expansion pending compliance signoff.", "next": "Secondary region target Oct 1."},
        {"name": "Data Product Experience", "status": "Yellow", "update": "Scope and sequencing decisions still open.", "next": "Scope baseline signoff in next steering review."},
    ],
    "risks": [
        {"id": "RSK-101", "description": "Scope/timeline misalignment may impact downstream milestones", "impact": "High", "mitigation": "Finalize scope baseline and dependency sequencing", "owner": "Program PM", "due": "Next review", "status": "WIP"},
        {"id": "RSK-088", "description": "Platform modernization scope-resource tradeoff risk", "impact": "High", "mitigation": "Escalate priority decisions and rebalance capacity", "owner": "Engineering Director", "due": "Mitigated", "status": "Mitigated"},
    ],
    "decisions_needed": [
        "Approve temporary capacity shift to defect reduction for one sprint.",
        "Approve contingency sequencing plan for external dependency variance.",
    ],
}


def status_badge(label: str, status: str) -> str:
    lower = status.lower()
    if "green" in lower or "mitigated" in lower:
        cls = "badge-green"
    elif "yellow" in lower or "risk" in lower or "wip" in lower:
        cls = "badge-yellow"
    else:
        cls = "badge-red"
    return f'<span class="badge {cls}">{label}: {status}</span>'


def health_summary(signals: dict) -> tuple[str, str]:
    sev1 = signals.get("defects", {}).get("sev1", 0)
    sprint = signals.get("jira", {}).get("sprint_completion_pct", 0)
    target = signals.get("jira", {}).get("target_completion_pct", 0)
    if sev1 >= 5 or sprint < target - 7:
        return "Yellow", "Program is at risk but trending up with mitigation actions underway."
    return "Green", "Execution is on track with manageable operational risk."


def render_workstream_table(workstreams: list[dict]) -> str:
    rows = "\n".join(
        [f"| {w['name']} | {w['status']} | {w['update']} | {w['next']} |" for w in workstreams]
    )
    return "| Workstream | Status | Current update | Next milestone |\n|---|---|---|---|\n" + rows


def render_risk_table(risks: list[dict]) -> str:
    rows = "\n".join(
        [f"| {r['id']} | {r['impact']} | {r['description']} | {r['mitigation']} | {r['status']} | {r['owner']} | {r['due']} |" for r in risks]
    )
    return "| Risk ID | Impact | Description | Mitigation | Status | Owner | Due |\n|---|---|---|---|---|---|---|\n" + rows


def metric_tile(col, label: str, value: str, key: str, note: str):
    if col.button(f"{value}\n{label}", use_container_width=True, key=f"tile_{key}"):
        st.session_state["section_focus"] = key
    col.markdown(f"<div class='tile-note'>{note}</div>", unsafe_allow_html=True)


def generate_exec_report(signals: dict):
    health, narrative = health_summary(signals)
    big_rock = signals.get("big_rock_status", "Green")
    init_status = signals.get("initiative_status", "Yellow")
    sprint = signals.get("jira", {}).get("sprint_completion_pct", 0)
    target = signals.get("jira", {}).get("target_completion_pct", 0)
    sev1 = signals.get("defects", {}).get("sev1", 0)

    okr_lines = "\n".join([f"- **{o['name']}**: {o['status']} — {o['note']}" for o in signals.get("okrs", [])])
    decision_lines = "\n".join([f"- {d}" for d in signals.get("decisions_needed", [])])

    report = f"""<a id='highlights'></a>
## Key Highlights
- Sprint completion: **{sprint}%** (target: **{target}%**)
- Sev-1 defects: **{sev1}**
- Dependency governance reviews completed; execution proceeding with stage gates.

<a id='timeline'></a>
## Program Timeline & Status
{render_workstream_table(signals.get('workstreams', []))}

<a id='risks'></a>
## Top Issues and Risks
{render_risk_table(signals.get('risks', []))}

<a id='decisions'></a>
## Decisions Required from Leadership
{decision_lines}

<a id='metrics'></a>
## Success Metrics
{okr_lines}
"""
    return report, health, narrative, big_rock, init_status


if "section_focus" not in st.session_state:
    st.session_state["section_focus"] = "all"

report, health, narrative, big_rock, init_status = generate_exec_report(DEFAULT_SIGNALS)

summary_html = (
    "<div class='status-card'><strong>Executive Summary</strong><br><br>"
    + status_badge("Strategic Use Cases", big_rock)
    + status_badge("Platform Initiatives", init_status)
    + status_badge("Overall Health", health)
    + f"<div style='margin-top:10px'>{narrative}</div>"
    + f"<div class='small-muted'>Reporting period ending {DEFAULT_SIGNALS['week_of']}</div></div>"
)
st.markdown(summary_html, unsafe_allow_html=True)

# Tiles + section filters
st.markdown("### Quick Navigation")
c1, c2, c3, c4, c5 = st.columns(5)
metric_tile(c1, "Highlights", "01", "highlights", "Click to focus")
metric_tile(c2, "Timeline", "02", "timeline", "Click to focus")
metric_tile(c3, "Risks", "03", "risks", "Click to focus")
metric_tile(c4, "Decisions", "04", "decisions", "Click to focus")
metric_tile(c5, "Metrics", "05", "metrics", "Click to focus")

if st.button("Show full report", use_container_width=True):
    st.session_state["section_focus"] = "all"

focus = st.session_state["section_focus"]

if focus != "all":
    st.info(f"Filtered view: {focus.title()} section")

with st.container(border=True):
    if focus == "all":
        st.markdown(report, unsafe_allow_html=True)
    else:
        if focus == "highlights":
            st.markdown(report.split("<a id='timeline'></a>")[0], unsafe_allow_html=True)
        elif focus == "timeline":
            section = report.split("<a id='timeline'></a>")[1].split("<a id='risks'></a>")[0]
            st.markdown("## Program Timeline & Status\n" + section.split("## Program Timeline & Status")[-1], unsafe_allow_html=True)
        elif focus == "risks":
            section = report.split("<a id='risks'></a>")[1].split("<a id='decisions'></a>")[0]
            st.markdown("## Top Issues and Risks\n" + section.split("## Top Issues and Risks")[-1], unsafe_allow_html=True)
        elif focus == "decisions":
            section = report.split("<a id='decisions'></a>")[1].split("<a id='metrics'></a>")[0]
            st.markdown("## Decisions Required from Leadership\n" + section.split("## Decisions Required from Leadership")[-1], unsafe_allow_html=True)
        elif focus == "metrics":
            section = report.split("<a id='metrics'></a>")[1]
            st.markdown("## Success Metrics\n" + section.split("## Success Metrics")[-1], unsafe_allow_html=True)

with st.expander("TPM Controls (show only when needed)"):
    st.caption("Input signals are hidden in leadership view. Use this section for editing/testing.")
    raw = st.text_area("Input Signals JSON", value=json.dumps(DEFAULT_SIGNALS, indent=2), height=280)
    if st.button("Regenerate report from edited signals"):
        try:
            parsed = json.loads(raw)
            report, health, narrative, big_rock, init_status = generate_exec_report(parsed)
            st.success("Report regenerated. Use Quick Navigation tiles to jump/filter sections.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
