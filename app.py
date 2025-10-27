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
    st.error("❌ OPENAI_API_KEY not found. Please set it as an environment variable.")
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

    PROMPT_TEMPLATE = f"""
Act like a senior Product Strategist and AI-Powered Software Architect (expert in software planning, sprint design, and JSON documentation). Your task: only produce one pure JSON object (no markdown, no prose). Use the inputs inside `{{json_data}}` to plan and estimate a software product.

------------------------------------------------------------
OBJECTIVE:
Generate one valid JSON object with exactly four top-level keys: `features`, `resources`, `tech`, and `budget`.

------------------------------------------------------------
INPUT ({json_data}):
- project_title (optional)
- project_description (required)
- product_level ("POC", "MVP", or "Full Product")
- ui_level ("Simple" or "Polished")
- platforms (array, e.g. ["Web","iOS"])
- target_audience (optional)
- competitors (optional)
- budget (optional, numeric or string)
- feature_count (optional integer; if provided, honor unless infeasible)

------------------------------------------------------------
OUTPUT FORMAT:
{{
  "features": [ /* feature objects */ ],
  "resources": [ /* role + count */ ],
  "tech": [ /* strings */ ],
  "budget": {{ /* budget object */ }}
}}

------------------------------------------------------------
FEATURE OBJECT FORMAT:
{{
  "feature_name": "<string>",
  "description": "<string>",
  "acceptance_criteria": ["<string>","<string>","<string>"],
  "user_story": "<string>",
  "dependencies": "<string>",
  "deliverables": "<string or array>",
  "resources": [
    {{"role":"fullstack","hours":"<number_or_N/A>"}},
    {{"role":"ai","hours":"<number_or_N/A>"}},
    {{"role":"ui_ux","hours":"<number_or_N/A>"}},
    {{"role":"pm","hours":"<number_or_N/A>"}},
    {{"role":"qa","hours":"<number_or_N/A>"}}
  ],
  "timeline": {{
    "phase": "<string>",
    "duration_hours": <number>,
    "tasks": [
      {{"hour_range":"<e.g. 8-24>","responsible_role":"<role>","tasks_summary":"<string>"}}
    ]
  }},
  "cost_estimate": {{
    "fullstack_cost_usd": <number>,
    "ai_cost_usd": <number>,
    "ui_ux_cost_usd": <number>,
    "pm_cost_usd": <number>,
    "qa_cost_usd": <number>,
    "total_feature_cost_usd": <number>
  }}
}}

------------------------------------------------------------
RESOURCES FORMAT:
[
  {{"role":"fullstack","count":<int>}},
  {{"role":"ai","count":<int>}},
  {{"role":"ui_ux","count":<int>}},
  {{"role":"pm","count":<int>}},
  {{"role":"qa","count":<int>}}
]

------------------------------------------------------------
TECH FORMAT:
["<tech_string_1>", "<tech_string_2>", "<tech_string_3>"]

------------------------------------------------------------
BUDGET FORMAT:
{{
  "currency": "USD",
  "per_feature": [
    {{"feature_name": "<string>", "total_feature_cost_usd": <number>}}
  ],
  "total_estimated_cost_usd": <number>,
  "budget_provided": <original_budget_value_or_null>,
  "within_budget": <true|false|null>,
  "notes": "<string>"
}}

------------------------------------------------------------
HOURLY RATES (USD):
fullstack = 25
ai = 30
ui_ux = 30
pm = 40
qa = 20

------------------------------------------------------------
FEATURE COUNT & COMPLEXITY RULES:

1. Compute complexity_score:
   - product_level_weight: POC=1, MVP=2, Full Product=3
   - ui_level_weight: Simple=0.8, Polished=1.2
   - platforms_factor = 1 + 0.25 * (number_of_platforms - 1)
   - description_density = clamp(len(project_description.split()) / 100, 0.2, 3.0)
   - keyword_multiplier = +0.5 per keyword in ["marketplace","payments","multi-tenant","integrations","real-time","ML","RAG","chatbot","mental health","analytics"], capped at +2.0
   - complexity_score = product_level_weight * ui_level_weight * platforms_factor * description_density + keyword_multiplier

2. Apply budget_factor:
   - budget_factor defaults:
       - <10,000 USD → 0.6
       - 10,000–75,000 USD → 1.0
       - >75,000 USD → 1.5
   - If no numeric budget, use 1.0
   - If cost estimate > provided budget, scale budget_factor proportionally

3. feature_count = round(complexity_score * budget_factor)
   - Clamp: min=1, max=25 (or 50 if user explicitly requested more)
   - Adjust by product_level:
       - POC: prefer 3–8 atomic features
       - MVP: 5–12
       - Full Product: 6–20
   - If single-deliverable project (title/desc includes “POC” or is monolithic), decompose into atomic features (e.g., ingestion, retrieval, UI, analytics)
   - Always ensure minimum viable functional decomposition (e.g., auth, core, admin)

------------------------------------------------------------
HOURS & COST DISTRIBUTION:
- total_project_hours proportional to complexity_score and product_level.
- Sum of feature.duration_hours = total_project_hours.
- For each feature:
  - Assign higher ai/fullstack hours for core/AI features.
  - Assign higher ui_ux hours for UI-heavy ones.
  - Assign “N/A” and 0 cost to unused roles.
- cost = sum(hours * rate).
- Sum of all feature costs = total_estimated_cost_usd.

------------------------------------------------------------
BUDGET RULES:
- If budget provided:
  - within_budget = True if numeric_budget >= total_estimated_cost_usd else False.
- If non-numeric, set within_budget = null.
- Include reasoning in `notes` if scope trimmed for budget.

------------------------------------------------------------
RESOURCES RULES:
- Scale team size realistically based on scope & budget.
- Round fractional staffing up to nearest integer but adjust hours accordingly.

------------------------------------------------------------
TECH SELECTION:
- Low budget → managed, low-cost stack.
- High budget → scalable, enterprise-grade stack.

------------------------------------------------------------
VALIDATION:
- All keys in snake_case.
- Duration values in hours only.
- Costs are numbers, no currency symbols.
- Every feature includes all five roles.
- Output = valid JSON only (no markdown or commentary).

------------------------------------------------------------
FINAL INSTRUCTIONS:
1. Use all logic above to generate complete JSON.
2. Never emit explanations or extra text.
3. Output must contain only JSON with:
   - features
   - resources
   - tech
   - budget
4. All cost computations must match the hourly rates table.
5. When in doubt, simplify logically but remain consistent.

Take a deep breath and work on this problem step-by-step.
"""

    # --- OPENAI CALL ---
    with st.spinner("🧠 Generating estimation using GPT-5..."):
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": PROMPT_TEMPLATE}]
        )

    response = completion.choices[0].message.content

    # --- DISPLAY OUTPUT ---
    st.markdown("<div class='result-section'>", unsafe_allow_html=True)
    st.success("✅ Estimation Generated Successfully!")

    # Robust JSON extraction
    if "Full JSON Object" in response:
        parts = response.split("Full JSON Object", 1)
        markdown_part = parts[0].strip()
        json_part = parts[1].strip()
    else:
        json_start = response.find("{")
        json_end = response.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            markdown_part = response[:json_start].strip()
            json_part = response[json_start : json_end + 1].strip()
        else:
            markdown_part = response
            json_part = ""

    st.subheader("📘 Readable Markdown Summary")
    if markdown_part:
        st.markdown(markdown_part)
    else:
        st.info("No Markdown summary found in response.")

    st.subheader("📊 Structured Estimation Tables")

    try:
        json_cleaned = (
            json_part.strip().replace("```json", "").replace("```", "").strip()
        )
        if not (json_cleaned.startswith("{") and json_cleaned.endswith("}")):
            s = json_cleaned.find("{")
            e = json_cleaned.rfind("}")
            if s != -1 and e != -1 and e > s:
                json_cleaned = json_cleaned[s : e + 1]

        parsed_json = json.loads(json_cleaned)

        expected = {"features", "resources", "tech", "budget"}
        if not expected.issubset(parsed_json.keys()):
            st.warning(
                "⚠️ Parsed JSON missing some expected top-level keys (features/resources/tech/budget). Rendering available keys."
            )

        RATES = {"fullstack": 25, "ai": 30, "ui_ux": 30, "pm": 40, "qa": 20}

        # ---- FEATURES TABLE ----
        st.markdown(
            "<div class='section-title'>🏗️ Features Overview</div>",
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
                pm_h = res_map.get("pm")
                qa_h = res_map.get("qa")

                duration_hours = sum(
                    h
                    for h in [fullstack_h, ai_h, ui_ux_h, pm_h, qa_h]
                    if isinstance(h, (int, float))
                )

                # Compute total cost using hourly rates
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
                    + compute_cost(pm_h, RATES["pm"])
                    + compute_cost(qa_h, RATES["qa"])
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
                        "fullstack_hours": (
                            fullstack_h if fullstack_h is not None else "N/A"
                        ),
                        "ai_hours": ai_h if ai_h is not None else "N/A",
                        "ui_ux_hours": ui_ux_h if ui_ux_h is not None else "N/A",
                        "pm_hours": pm_h if pm_h is not None else "N/A",
                        "qa_hours": qa_h if qa_h is not None else "N/A",
                        "total_feature_cost_usd": total_feature_cost,
                    }
                )

            df_features = pd.DataFrame(feature_rows)
            df_features = df_features[
                [
                    "feature_name",
                    "description",
                    "phase",
                    "duration_hours",
                    "fullstack_hours",
                    "ai_hours",
                    "ui_ux_hours",
                    "pm_hours",
                    "qa_hours",
                    "total_feature_cost_usd",
                ]
            ]
            st.dataframe(df_features, use_container_width=True)
        else:
            st.info("No features found in parsed JSON.")

        # ---- RESOURCES TABLE ----
        st.markdown(
            "<div class='section-title'>👥 Resource Summary</div>",
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
            "<div class='section-title'>💰 Budget Summary</div>", unsafe_allow_html=True
        )
        budget_obj = parsed_json.get("budget", {})
        if budget_obj and isinstance(budget_obj, dict):
            currency = budget_obj.get("currency", "USD")
            per_feature = budget_obj.get("per_feature", [])
            total_estimated = budget_obj.get("total_estimated_cost_usd", None)
            budget_provided = budget_obj.get("budget_provided", None)
            within_budget = budget_obj.get("within_budget", None)
            notes = budget_obj.get("notes", "")

            c1, c2, c3 = st.columns([2, 2, 4])
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

    except Exception as e:
        st.warning(
            f"⚠️ Could not parse JSON properly — showing raw output below.\n\nParsing error: {e}"
        )
        st.code(response, language="text")

    st.markdown("</div>", unsafe_allow_html=True)
