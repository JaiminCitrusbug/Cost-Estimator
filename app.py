# ai_project_estimator_app.py
# Complete Streamlit app — copy-paste this file and run with: streamlit run ai_project_estimator_app.py
# Requirements: streamlit, openai (official OpenAI Python lib), python-dotenv, pandas
# Make sure OPENAI_API_KEY is set in your environment or in a .env file.

import streamlit as st
import openai
import os
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Project Estimation Generator", layout="centered", page_icon="🤖"
)

# --- CSS STYLING (Professional Look) ---
st.markdown(
    """
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
        color: #111827;
    }

    h1, h2, h3, h4, h5 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #111827;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        text-align: left;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 0.95rem;
        color: #555;
        margin-bottom: 1.5rem;
    }

    .form-card {
        background: #f9fafb;
        padding: 2rem 2.5rem;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.04);
        width: 100%;
        max-width: 700px;
        margin: 0 auto;
    }

    label {
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: #1f2937 !important;
    }

    input, textarea, select {
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        background-color: #f3f4f6 !important;
        color: #111827 !important;
        padding: 0.6rem !important;
    }

    textarea {
        min-height: 120px !important;
    }

    div.stButton > button:first-child {
        background-color: #111827;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        width: 100%;
        transition: all 0.2s ease;
        margin-top: 1rem;
    }

    div.stButton > button:first-child:hover {
        background-color: #1e293b;
        transform: translateY(-1px);
    }

    .result-section {
        background: #f9fafb;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
        margin-top: 2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #111827;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .warning {
        background: #fff7ed;
        border-left: 4px solid #f59e0b;
        padding: .6rem;
        border-radius: 6px;
    }

</style>
""",
    unsafe_allow_html=True,
)

# --- HEADER ---
st.markdown(
    "<div class='main-title'>🤖 AI Project Estimation Generator</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>Plan, estimate, and structure your project like a pro — powered by GPT-5.</div>",
    unsafe_allow_html=True,
)

# --- API KEY ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY not found. Please set it as an environment variable (or add to a .env file).")
    st.stop()

# --- INPUT FORM ---
st.markdown("<div class='form-card'>", unsafe_allow_html=True)
with st.form("estimation_form"):
    st.subheader("📋 Project Input Details")

    title = st.text_input("🧾 Project Title (optional)")
    description = st.text_area("📝 Project Description (required)", height=150)
    product_level = st.selectbox("⚙️ Product Level", ["POC", "MVP", "Full Product"])
    ui_level = st.selectbox("🎨 UI Level", ["Simple", "Polished"])
    platforms = st.multiselect(
        "💻 App Platform(s)", ["Web", "iOS", "Android", "Desktop"]
    )
    target_audience = st.text_input("🎯 Target Audience (optional)")
    competitors = st.text_input("🏁 Competitors (optional)")
    budget = st.text_input(
        "💰 Estimated Budget (optional)", placeholder="e.g. $15,000 – $25,000"
    )

    generate = st.form_submit_button("🚀 Generate Estimation")
st.markdown("</div>", unsafe_allow_html=True)

# --- HELPER: robust JSON extraction ---
def extract_first_json(text: str):
    """
    Scan text and extract the first valid JSON object using json.JSONDecoder.raw_decode.
    Returns parsed object or None.
    """
    decoder = json.JSONDecoder()
    idx = 0
    length = len(text)
    while idx < length:
        try:
            obj, end = decoder.raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            idx += 1
    return None

# --- RATES (only roles that are costed at feature-level) ---
RATES = {"fullstack": 25, "ai": 30, "ui_ux": 30}
# Note: PM & QA hours will be returned as cumulative totals but their costs are excluded.

# --- FULL PROMPT (the user requested the full prompt included exactly) ---
FULL_PROMPT_TEMPLATE = r"""
Act like a senior Product Strategist and AI-Powered Software Architect (expert in software planning, sprint design, and JSON documentation). Your task: only produce one pure JSON object (no markdown, no prose). Use the inputs inside `{{json_data}}` to plan and estimate a software product.

------------------------------------------------------------
OBJECTIVE:
Generate one valid JSON object with exactly four top-level keys: `features`, `resources`, `tech`, and `budget`.

------------------------------------------------------------
INPUT ({{json_data}}):
- project_title (optional)
- project_description (required)
- product_level ("POC", "MVP", or "Full Product")
- ui_level ("Simple" or "Polished")
- platforms (array, e.g. ["Web","iOS"])
- target_audience (optional)
- competitors (optional)
- budget (optional, numeric or string)
- feature_count (optional integer; if provided, honor unless infeasible)

IMPORTANT CHANGE (PM & QA handling):
- Do NOT include `pm` or `qa` hours inside any individual **feature** resource lists.
- Instead compute cumulative `pm_total_hours` and `qa_total_hours` for the **whole project** and return these inside the `budget` object (see BUDGET FORMAT below).
- **Do not** include `pm` and `qa` costs in the budget calculations — exclude PM and QA cost from all cost totals for now.

------------------------------------------------------------
OUTPUT FORMAT:
{
  "features": [ /* feature objects */ ],
  "resources": [ /* role + count */ ],
  "tech": [ /* strings */ ],
  "budget": { /* budget object, must include pm_total_hours & qa_total_hours */ }
}

------------------------------------------------------------
FEATURE OBJECT FORMAT (updated):
{
  "feature_name": "<string>",
  "description": "<string>",
  "acceptance_criteria": ["<string>","<string>","<string>"],
  "user_story": "<string>",
  "dependencies": "<string>",
  "deliverables": "<string or array>",
  "resources": [
    {"role":"fullstack","hours":<number_or_N/A>},
    {"role":"ai","hours":<number_or_N/A>},
    {"role":"ui_ux","hours":<number_or_N/A>}
  ],
  "timeline": {
    "phase": "<string>",
    "duration_hours": <number>,   /* MUST equal sum of the above role-hours for the feature */
    "tasks": [
      {"hour_range":"<e.g. 8-24>","responsible_role":"<role>","tasks_summary":"<string>"}
    ]
  },
  "cost_estimate": {
    "fullstack_cost_usd": <number>,
    "ai_cost_usd": <number>,
    "ui_ux_cost_usd": <number>,
    "total_feature_cost_usd": <number>  /* PM & QA costs NOT included */
  }
}

------------------------------------------------------------
RESOURCES FORMAT:
[
  {"role":"fullstack","count":<int>},
  {"role":"ai","count":<int>},
  {"role":"ui_ux","count":<int>},
  {"role":"pm","count":<int>},
  {"role":"qa","count":<int>}
]

(You may include pm/qa headcount here for planning/headcount purposes; hours for pm/qa must be returned only in budget as cumulative totals.)

------------------------------------------------------------
TECH FORMAT:
["<tech_string_1>", "<tech_string_2>", "<tech_string_3>"]

------------------------------------------------------------
BUDGET FORMAT (updated — must include PM/QA totals and indicate exclusion):
{
  "currency": "USD",
  "per_feature": [
    {"feature_name": "<string>", "total_feature_cost_usd": <number>}
  ],
  "total_estimated_cost_usd": <number>,   /* SUM of feature costs only: fullstack + ai + ui_ux */
  "budget_provided": <original_budget_value_or_null>,
  "within_budget": <true|false|null>,
  "pm_total_hours": <number>,             /* cumulative PM hours for whole project (not costed) */
  "qa_total_hours": <number>,             /* cumulative QA hours for whole project (not costed) */
  "pm_qa_costs_excluded": true,
  "notes": "<string>"
}

------------------------------------------------------------
HOURLY RATES (USD) — used to compute feature-level costs only (PM and QA costs intentionally excluded from budget):
fullstack = 25
ai = 30
ui_ux = 30
/* PM and QA exist in planning but their costs are excluded. Compute pm_total_hours and qa_total_hours as aggregates. */

------------------------------------------------------------
FEATURE COUNT & COMPLEXITY RULES:
(Keep the same full logic as originally specified — compute complexity_score, budget_factor, derive feature_count, clamp and adjust by product_level, decompose monolithic projects, ensure auth/core/admin exist, etc.)

------------------------------------------------------------
HOURS & COST DISTRIBUTION (adapted for PM/QA change):
- Use the same SMART HOUR RANGE MODEL and module_type mapping as before to determine *base feature hours*.
- Apply complexity multipliers, reuse_factor, and dynamic ratios **for per-feature allocation only** but do NOT place PM and QA hours per feature in the output.
- After computing total_project_hours (sum of all feature duration_hours), compute:
    pm_total_hours = round( total_project_hours * pm_project_ratio )
    qa_total_hours = round( total_project_hours * qa_project_ratio )
  where pm_project_ratio and qa_project_ratio should respect the original minimal/typical project allocations (commonly 10% each), but adjust slightly if features are trivial (ensure QA >=8% for tiny projects).
- Ensure each feature.timeline.duration_hours equals the sum of its fullstack + ai + ui_ux hours.
- Costs: compute costs only for fullstack, ai, ui_ux using the HOURLY RATES above. **PM & QA costs must not be included.**

------------------------------------------------------------
FEATURE COMPLEXITY MULTIPLIER, REUSE FACTOR, DYNAMIC ROLE RATIOS:
(Keep the same rules and numbers as before for complexity levels, reuse_factor, and the role ratios for distributing feature hours.
When ratios previously referenced PM and QA percentages, distribute the feature hours proportionally only among fullstack, ai, ui_ux and keep PM/QA out of per-feature allocations — their effort will be calculated as cumulative totals as described above.)

------------------------------------------------------------
VALIDATION & AUTO-CORRECTIONS (guardrails):
- Auto-flag and correct:
  - Any feature total hours must equal the sum of the feature's role hours (fullstack+ai+ui_ux). Snap to nearest bound if outside allowed buffers.
  - UI/UX or QA guidance thresholds: since QA is not per-feature, ensure QA project total meets minimum thresholds (e.g., QA hours >= 8% of total_project_hours for tiny projects; otherwise raise and annotate in notes).
  - Any internal inconsistency should be corrected, with rationale in `budget.notes`.

------------------------------------------------------------
BUDGET RULES:
- If numeric budget provided:
  - within_budget = True if numeric_budget >= total_estimated_cost_usd ELSE False.
- PM and QA costs are excluded from `total_estimated_cost_usd`. If client wants PM/QA costed later, include as a separate option.

------------------------------------------------------------
RESOURCES RULES:
- Scale role counts realistically based on scope & budget. Round staff up to nearest integer.

------------------------------------------------------------
TECH SELECTION:
- Low budget → managed, lower-cost stack.
- High budget → scalable, enterprise-grade stack.

------------------------------------------------------------
VALIDATION:
- All keys in snake_case.
- Duration values in hours only.
- Costs are numbers, no currency symbols.
- Output = valid JSON only (no markdown or commentary).
- If you encounter ambiguity in inputs, analyze them deeply, then decide and proceed — but do NOT add unnecessary complexity for simple modules (e.g., simple auth = sign up + login; don't invent advanced flows unless description requires them).

------------------------------------------------------------
FINAL INSTRUCTIONS:
1. Use all logic above to generate complete JSON.
2. Only output the JSON (features, resources, tech, budget).
3. Include cumulative `pm_total_hours` and `qa_total_hours` in `budget`.
4. Exclude PM & QA costs from totals — set "pm_qa_costs_excluded": true.
5. When in doubt, simplify logically but remain consistent.
"""

# --- MODEL CALL wrapper ---
def call_model_with_full_prompt(json_input_str: str):
    """
    Builds the full prompt by injecting user's JSON into FULL_PROMPT_TEMPLATE and calls the model.
    Returns the raw model text.
    """
    prompt_with_input = FULL_PROMPT_TEMPLATE.replace("{{json_data}}", json_input_str)
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict JSON-only generator for project estimations. "
                        "Return exactly one valid JSON object with top-level keys: features, resources, tech, budget. "
                        "Follow the prompt instructions exactly. PM & QA hours must NOT be present per-feature; instead include pm_total_hours and qa_total_hours under budget. PM & QA costs must be excluded from budget totals."
                    ),
                },
                {"role": "user", "content": prompt_with_input},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        # propagate for the UI to handle
        raise RuntimeError(f"Model/API error: {e}")

# --- GENERATE LOGIC ---
if generate:
    if not description.strip():
        st.warning("⚠️ Please provide a project description before generating.")
        st.stop()

    # Prepare input JSON
    data = {
        "project_title": title.strip(),
        "project_description": description.strip(),
        "product_level": product_level.strip(),
        "ui_level": ui_level.strip(),
        "platforms": platforms,
        "target_audience": target_audience.strip(),
        "competitors": competitors.strip(),
        "budget": budget.strip(),
    }

    json_data = json.dumps(data, indent=2)
    with st.spinner("🧠 Generating estimation using GPT-5..."):
        try:
            response = call_model_with_full_prompt(json_data)
        except Exception as e:
            st.error(str(e))
            st.stop()

    # --- DISPLAY OUTPUT ---
    st.markdown("<div class='result-section'>", unsafe_allow_html=True)
    st.success("✅ Estimation Generated Successfully!")

    # Extract JSON robustly
    parsed_json = None
    try:
        parsed_json = extract_first_json(response)
        if parsed_json is None:
            # fallback: try to salvage with previous heuristics
            json_start = response.find("{")
            json_end = response.rfind("}")
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response[json_start:json_end + 1]
                parsed_json = json.loads(json_str)
    except Exception as e:
        st.warning(f"⚠️ Could not parse JSON automatically: {e}")
        parsed_json = None

    st.subheader("📘 Readable Markup (if any)")
    # Show any text before JSON if present (often none because we enforce JSON-only)
    try:
        if parsed_json is None:
            st.info("No valid JSON parsed from model response. Showing raw response below.")
            st.code(response, language="text")
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()
    except Exception:
        pass

    # Continue with parsed_json rendering
    try:
        expected = {"features", "resources", "tech", "budget"}
        if not expected.issubset(parsed_json.keys()):
            st.warning(
                "⚠️ Parsed JSON missing some expected top-level keys (features/resources/tech/budget). Rendering available keys."
            )

        # ---- FEATURES TABLE ----
        st.markdown(
            "<div class='section-title'>🏗️ Features Overview (PM & QA excluded per feature)</div>",
            unsafe_allow_html=True,
        )

        features = parsed_json.get("features", [])
        if features and isinstance(features, list):
            feature_rows = []
            for f in features:

                def parse_hours(v):
                    try:
                        if isinstance(v, (int, float)):
                            return float(v)
                        if isinstance(v, str):
                            s = v.strip()
                            if s.lower() in ("n/a", "na", "-", ""):
                                return None
                            # support ranges like "20-30" by taking average
                            if "-" in s:
                                parts = s.split("-", 1)
                                try:
                                    a = float(parts[0].strip())
                                    b = float(parts[1].strip())
                                    return (a + b) / 2.0
                                except:
                                    return None
                            return float(s)
                    except:
                        return None
                    return None

                resources_list = f.get("resources", [])
                res_map = {
                    r.get("role", "").lower(): parse_hours(r.get("hours", "N/A"))
                    for r in resources_list
                }

                fullstack_h = res_map.get("fullstack")
                ai_h = res_map.get("ai")
                ui_ux_h = res_map.get("ui_ux")

                duration_hours = sum(
                    h
                    for h in [fullstack_h, ai_h, ui_ux_h]
                    if isinstance(h, (int, float))
                )

                # Compute total cost using hourly rates (pm/qa excluded intentionally)
                def compute_cost(hours, rate):
                    return (
                        round(hours * rate, 2)
                        if isinstance(hours, (int, float))
                        else 0.0
                    )

                total_feature_cost = (
                    compute_cost(fullstack_h, RATES["fullstack"])
                    + compute_cost(ai_h, RATES["ai"])
                    + compute_cost(ui_ux_h, RATES["ui_ux"])
                )
                total_feature_cost = round(total_feature_cost, 2)

                feature_rows.append(
                    {
                        "feature_name": f.get("feature_name", ""),
                        "description": (
                            f.get("description", "")[:250]
                            + ("..." if len(f.get("description", "")) > 250 else "")
                        ),
                        "phase": f.get("timeline", {}).get("phase", ""),
                        "duration_hours": duration_hours,
                        "fullstack_hours": fullstack_h if fullstack_h is not None else "N/A",
                        "ai_hours": ai_h if ai_h is not None else "N/A",
                        "ui_ux_hours": ui_ux_h if ui_ux_h is not None else "N/A",
                        "total_feature_cost_usd": total_feature_cost,
                    }
                )

            df_features = pd.DataFrame(feature_rows)
            # Only show columns relevant now (no pm/qa columns)
            if not df_features.empty:
                df_features = df_features[
                    [
                        "feature_name",
                        "description",
                        "phase",
                        "duration_hours",
                        "fullstack_hours",
                        "ai_hours",
                        "ui_ux_hours",
                        "total_feature_cost_usd",
                    ]
                ]
            st.dataframe(df_features, use_container_width=True)
        else:
            st.info("No features found in parsed JSON.")

        # ---- RESOURCES TABLE ----
        st.markdown(
            "<div class='section-title'>👥 Resource Summary (headcounts)</div>",
            unsafe_allow_html=True,
        )
        resources = parsed_json.get("resources", [])
        if resources and isinstance(resources, list):
            processed = []
            for r in resources:
                role = r.get("role", "")
                count = r.get("count", 0)
                try:
                    count_num = int(count)
                except:
                    count_num = 0
                processed.append({"role": role, "count": count_num})
            st.dataframe(pd.DataFrame(processed), use_container_width=True)
        else:
            st.info("No resources found in parsed JSON.")

        # ---- TECH STACK TABLE ----
        st.markdown(
            "<div class='section-title'>⚙️ Technology Stack</div>",
            unsafe_allow_html=True,
        )
        tech = parsed_json.get("tech", [])
        if tech and isinstance(tech, list):
            st.dataframe(
                pd.DataFrame({"technology_tool": tech}), use_container_width=True
            )
        else:
            st.info("No tech stack found in parsed JSON.")

        # ---- BUDGET SUMMARY ----
        st.markdown(
            "<div class='section-title'>💰 Budget & PM/QA Summary</div>", unsafe_allow_html=True
        )
        budget_obj = parsed_json.get("budget", {})
        if budget_obj and isinstance(budget_obj, dict):
            currency = budget_obj.get("currency", "USD")
            per_feature = budget_obj.get("per_feature", [])
            total_estimated = budget_obj.get("total_estimated_cost_usd", None)
            budget_provided = budget_obj.get("budget_provided", None)
            within_budget = budget_obj.get("within_budget", None)
            notes = budget_obj.get("notes", "")
            pm_total_hours = budget_obj.get("pm_total_hours", None)
            qa_total_hours = budget_obj.get("qa_total_hours", None)
            pm_qa_excluded = budget_obj.get("pm_qa_costs_excluded", True)

            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            with c1:
                st.metric("Currency", currency)
            with c2:
                st.metric(
                    "Total Estimated (USD)",
                    str(total_estimated if total_estimated is not None else "N/A"),
                )
            with c3:
                st.metric(
                    "Budget Provided",
                    str(budget_provided if budget_provided is not None else "null"),
                )
            with c4:
                st.metric("PM/QA Costed?", "No" if pm_qa_excluded else "Yes")

            # Show PM and QA cumulative hours (these are not costed in totals)
            c5, c6 = st.columns([2, 2])
            with c5:
                st.metric("PM Total Hours (project)", str(pm_total_hours if pm_total_hours is not None else "N/A"))
            with c6:
                st.metric("QA Total Hours (project)", str(qa_total_hours if qa_total_hours is not None else "N/A"))

            st.write(f"**Within budget?** {within_budget}")

            if per_feature and isinstance(per_feature, list):
                df_pf = pd.DataFrame(per_feature)
                if "total_feature_cost_usd" in df_pf.columns:
                    df_pf["total_feature_cost_usd"] = pd.to_numeric(
                        df_pf["total_feature_cost_usd"], errors="coerce"
                    ).fillna(0)
                st.dataframe(df_pf, use_container_width=True)
            else:
                st.info("No per-feature budget breakdown found in parsed JSON.")

            if notes:
                st.markdown("**Notes:**")
                st.write(notes)
        else:
            st.info("No budget object found in parsed JSON.")

        # ---- LOCAL CONSISTENCY CHECKS & WARNINGS ----
        # Compute local sums to ensure budgets match (note: PM/QA excluded)
        try:
            local_total = 0.0
            if features and isinstance(features, list):
                for f in features:
                    # compute per-feature cost from parsed role hours
                    resources_list = f.get("resources", [])
                    res_map = {r.get("role", "").lower(): r.get("hours", 0) for r in resources_list}
                    def to_float(v):
                        try:
                            return float(v)
                        except:
                            return 0.0
                    fs = to_float(res_map.get("fullstack", 0))
                    ai_h = to_float(res_map.get("ai", 0))
                    ui = to_float(res_map.get("ui_ux", 0))
                    local_total += round(fs * RATES["fullstack"] + ai_h * RATES["ai"] + ui * RATES["ui_ux"], 2)

            local_total = round(local_total, 2)
            if total_estimated is not None:
                # total_estimated might be string; try parse
                try:
                    total_est_val = float(total_estimated)
                except:
                    total_est_val = None

                if total_est_val is not None and abs(local_total - total_est_val) > 1.0:
                    st.warning(f"⚠️ Estimated total from model ({total_estimated}) differs from locally computed total ({local_total}). We display the model total but local recomputation is shown here for comparison.")
                    st.info(f"Local recomputed total (excl. PM/QA): {local_total} USD")
        except Exception as e:
            st.info("Could not run local consistency checks: " + str(e))

    except Exception as e:
        st.warning(
            f"⚠️ Could not parse JSON properly — showing raw output below.\n\nParsing error: {e}"
        )
        st.code(response, language="text")

    st.markdown("</div>", unsafe_allow_html=True)
