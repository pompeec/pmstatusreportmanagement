cd /Users/pompee/Documents/GitHub/pmstatusreportmanagement

cat > app.py << 'EOF'
import json
from datetime import date

import streamlit as st

st.set_page_config(page_title="TPM Executive Status", layout="wide")

st.title("Program Portfolio — Executive Status Brief")
st.caption("Objective: Provide a concise, decision-ready summary of portfolio health, risks, and actions.")

DEFAULT_SIGNALS = {
    "week_of": str(date.today()),
    "objective": "Drive delivery predictability and business outcome adoption",
    "big_rock_status": "Green",
    "initiative_status": "Yellow",
    "jira": {"sprint_completion_pct": 78, "target_completion_pct": 85},
    "defects": {"open_total": 23, "sev1": 5},
    "okrs": [
        {"name": "Adoption target", "status": "At risk", "note": "Flagship use case launch remains dependent on platform readiness milestones."},
        {"name": "Use cases delivered", "status": "1/8", "note": "Two use cases are live; broader pipeline is in staged rollout."},
    ],
    "workstreams": [
        {
            "name": "Zero Copy Connectors",
            "status": "Green",
            "update": "Amazon S3 connector implemented; OAuth federation added.",
            "next": "Delta/Iceberg UX complete by Oct 10.",
        },
        {
            "name": "Trino Runtime",
            "status": "Green",
            "update": "Operational in GCC; SPP-AU deployed pending compliance signoff.",
            "next": "SPP-SG operational target Oct 1.",
        },
        {
            "name": "Data Product Experience",
            "status": "Yellow",
            "update": "Carries delivery risk due to unresolved scope and sequencing decisions.",
            "next": "Scope definition and workflow signoff in progress.",
        },
    ],
    "risks": [
        {
            "id": "RSK-101",
            "description": "Scope and timeline misalignment may impact downstream milestones",
            "impact": "High",
            "mitigation": "Finalize scope baseline, dependency sequencing, and design signoff",
            "owner": "Program PM",
            "due": "Next review",
            "status": "WIP",
        },
        {
            "id": "RSK-088",
            "description": "Platform modernization scope/resource tradeoff risk",
            "impact": "High",
            "mitigation": "Escalate priority decisions and rebalance capacity",
            "owner": "Engineering Director",
            "due": "Mitigated",
            "status": "Mitigated",
        },
    ],
    "decisions_needed": [
        "Approve temporary capacity shift to defect reduction for one sprint.",
        "Approve contingency sequencing plan for external dependency variance.",
    ],
}


def health_summary(signals: dict) -> tuple[str, str]:
    sev1 = signals.get("defects", {}).get("sev1", 0)
    sprint = signals.get("jira", {}).get("sprint_completion_pct", 0)
    target = signals.get("jira", {}).get("target_completion_pct", 0)

    if sev1 >= 5 or sprint < target - 7:
        return "🟡 Yellow", "Overall program remains at risk but trending upward with mitigations in flight."
    return "🟢 Green", "Execution is on track with manageable operational risk."


def render_workstream_table(workstreams: list[dict]) -> str:
    header = "| Program | Status | Key update | Next milestone |\n|---|---|---|---|"
    rows = [
        f"| {w['name']} | {w['status']} | {w['update']} | {w['next']} |"
        for w in workstreams
    ]
    return "\n".join([header, *rows])


def render_risk_table(risks: list[dict]) -> str:
    header = "| Risk | Impact | Mitigation | Status | Owner | Due |\n|---|---|---|---|---|---|"
    rows = [
        f"| {r['id']}: {r['description']} | {r['impact']} | {r['mitigation']} | {r['status']} | {r['owner']} | {r['due']} |"
        for r in risks
    ]
    return "\n".join([header, *rows])


def generate_exec_report(signals: dict) -> str:
    health, narrative = health_summary(signals)
    big_rock = signals.get("big_rock_status", "Green")
    init_status = signals.get("initiative_status", "Yellow")

    sprint = signals.get("jira", {}).get("sprint_completion_pct", 0)
    target = signals.get("jira", {}).get("target_completion_pct", 0)
    sev1 = signals.get("defects", {}).get("sev1", 0)

    okr_lines = "\n".join(
        [f"- **{o['name']}**: {o['status']} — {o['note']}" for o in signals.get("okrs", [])]
    )

    decision_lines = "\n".join([f"- {d}" for d in signals.get("decisions_needed", [])])

    return f"""## Executive Summary
- **Strategic Use Cases: {big_rock}**
- **Platform Initiatives: {init_status}**
- **Overall Program Health: {health}**
- **Assessment:** {narrative}

## Key Highlights
- Sprint completion is **{sprint}%** versus **{target}%** target.
- Current Sev-1 defect count is **{sev1}**.
- Architecture and dependency reviews completed; execution is proceeding with monitored gates.

## Program Timeline & Status
{render_workstream_table(signals.get('workstreams', []))}

## Top Issues and Risks
{render_risk_table(signals.get('risks', []))}

## Decisions Required from Leadership
{decision_lines}

## Success Metrics
{okr_lines}
"""


st.markdown("### Leadership View")
report_container = st.container(border=True)
with report_container:
    st.markdown(generate_exec_report(DEFAULT_SIGNALS))

with st.expander("TPM Controls (show only when needed)"):
    st.caption("Input signals are hidden in leadership view. Use this section for editing/testing.")
    raw = st.text_area("Input Signals JSON", value=json.dumps(DEFAULT_SIGNALS, indent=2), height=280)
    if st.button("Regenerate report from edited signals"):
        try:
            parsed = json.loads(raw)
            report_container.markdown(generate_exec_report(parsed))
            st.success("Report regenerated.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")

            EOF

