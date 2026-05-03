import json
from datetime import date

import streamlit as st

st.set_page_config(page_title="TPM Status Report Reviewer", layout="wide")

st.title("TPM Status Report Reviewer")
st.caption("Local demo UI for leaders to review AI-generated executive status updates.")

DEFAULT_SIGNALS = {
    "week_of": str(date.today()),
    "jira": {
        "epics_in_flight": 4,
        "delayed_items": ["Platform API dependency"],
        "sprint_completion_pct": 78,
        "target_completion_pct": 85,
        "cycle_time_days": {"previous": 6.2, "current": 8.1},
    },
    "defects": {
        "open_total": 23,
        "sev1": 5,
        "sev2": 7,
        "sev3": 11,
        "sev1_aging_over_10_days": 2,
    },
    "okrs": [
        {"name": "O1 KR1", "progress_pct": 62, "confidence": "medium"},
        {"name": "O2 KR2", "progress_pct": 41, "confidence": "low"},
    ],
    "meetings_dependencies": [
        "Security review moved from May 1 to May 8",
        "Vendor SSO integration decision pending by May 6",
    ],
}


def infer_health(signals: dict) -> tuple[str, str]:
    sev1 = signals.get("defects", {}).get("sev1", 0)
    sprint = signals.get("jira", {}).get("sprint_completion_pct", 0)
    target = signals.get("jira", {}).get("target_completion_pct", 0)
    cycle = signals.get("jira", {}).get("cycle_time_days", {})
    previous = float(cycle.get("previous", 0) or 0)
    current = float(cycle.get("current", 0) or 0)

    if sev1 >= 5 or sprint < target - 10:
        return "🔴 Red", "Execution risk is high due to severe defects and delivery slippage."
    if sev1 >= 2 or current > previous:
        return "🟡 Yellow", "Program is at risk with quality/throughput signals trending negatively."
    return "🟢 Green", "Program is on track with manageable quality and delivery risk."


def generate_report(signals: dict) -> str:
    health, rationale = infer_health(signals)
    deps = signals.get("meetings_dependencies", [])
    top_dep = deps[0] if deps else "No major dependency updates."

    return f"""## 1) Program Health
**{health}** — {rationale}

## 2) Highlights
- Sprint completion is {signals['jira']['sprint_completion_pct']}% against target of {signals['jira']['target_completion_pct']}%.
- {signals['defects']['open_total']} open defects tracked; Sev-1 count is {signals['defects']['sev1']}.
- OKR progress includes {signals['okrs'][0]['name']} at {signals['okrs'][0]['progress_pct']}%.

## 3) Risks & Blockers
1. **Sev-1 defect load remains elevated** (Impact: High, Likelihood: Medium, Owner: Eng Manager, Mitigation: Daily bug triage + swarming).
2. **Dependency timing risk** — {top_dep} (Impact: High, Likelihood: Medium, Owner: TPM, Mitigation: Escalate in weekly staff sync).
3. **Cycle time regression** from {signals['jira']['cycle_time_days']['previous']}d to {signals['jira']['cycle_time_days']['current']}d (Impact: Medium, Likelihood: Medium, Owner: Team Leads, Mitigation: WIP limits + blocker SLA).

## 4) Decisions Required
- **SSO integration scope decision** (Owner: Product + Security, Due: This week, Recommendation: Approve MVP scope to protect milestone date).
- **Defect burn focus** (Owner: Engineering Director, Due: Next staff meeting, Recommendation: Dedicate 20% sprint capacity to Sev-1/2 reduction).

## 5) Next 2 Weeks
- Complete security review and finalize SSO integration path.
- Reduce Sev-1 defects from {signals['defects']['sev1']} to <=2.
- Recover sprint completion from {signals['jira']['sprint_completion_pct']}% toward {signals['jira']['target_completion_pct']}% target.
"""


left, right = st.columns([1, 1])

with left:
    st.subheader("Input Signals (JSON)")
    raw = st.text_area(
        "Paste or edit program signals",
        value=json.dumps(DEFAULT_SIGNALS, indent=2),
        height=520,
    )
    use_demo = st.toggle("Use demo generated report", value=True)

with right:
    st.subheader("Executive Status Output")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON: {exc}")
        parsed = DEFAULT_SIGNALS

    if use_demo:
        st.markdown(generate_report(parsed))
    else:
        st.info("Replace demo mode with your LLM/API call and render the model output here.")

st.divider()
st.caption("Tip: run with `streamlit run app.py` and share localhost via your preferred tunnel or internal hosting.")