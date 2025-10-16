import streamlit as st
import openai
import os
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Project Estimation Generator", layout="centered", page_icon="🤖")

# --- CSS STYLING (Professional Look) ---
st.markdown("""
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
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='main-title'>🤖 AI Project Estimation Generator</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Plan, estimate, and structure your project like a pro — powered by GPT-5.</div>", unsafe_allow_html=True)

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
    platforms = st.multiselect("💻 App Platform(s)", ["Web", "iOS", "Android", "Desktop"])
    target_audience = st.text_input("🎯 Target Audience (optional)")
    competitors = st.text_input("🏁 Competitors (optional)")
    budget = st.text_input("💰 Estimated Budget (optional)", placeholder="e.g. $15,000 – $25,000")

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
        "budget": budget.strip()
    }

    json_data = json.dumps(data, indent=2)


    PROMPT_TEMPLATE = f"""
Act like a senior **Product Strategist** and **AI-Powered Software Architect** with expertise in software planning, sprint design, and JSON documentation.

Your goal is to generate a **single JSON object only** (no markdown, no prose, no additional text) that contains four top-level keys: **features**, **resources**, **tech**, and **budget**.  
- `features`: an array of feature objects (use the existing feature JSON format below).  
- `resources`: an array of resource objects (each resource entry should be simple — role + count).  
- `tech`: an array of technical dependency strings.  
- `budget`: an object with detailed cost estimations for the project.  

------------------------------------------------------------
## USER INPUTS : {json_data}
- Project Title (optional)
- Project Description (required)
- Product Level (POC / MVP / Full Product)
- UI Level (Simple / Polished)
- Platforms (e.g., Web / iOS / Android / Desktop)
- Target Audience (optional)
- Competitors (optional)
- Budget (optional) — numerical or string (currency). If present, factor this into features, resource allocations, and tech choices.

------------------------------------------------------------
## HOW TO RESPOND
1. Use the input data in `{json_data}`, including `budget` if present.
2. If **budget** is provided, adapt feature count, scope, and technical depth:
   - Low budget → focus on core validation, essential features, and limited tech stack.
   - Moderate budget → build MVP scope with balanced resource hours and managed services.
   - High budget → include advanced automation, AI, and analytics features.
3. Produce **only one output**:  
   A single, valid JSON object with **exactly** the following four top-level keys:
   - `features`
   - `resources`
   - `tech`
   - `budget`
4. The response must be **pure JSON** — no markdown, no code blocks, no explanations.

------------------------------------------------------------
## HOURLY RATES (for Budget Calculation)
Use these standardized hourly rates (USD):

| Role | Hourly Rate (USD) |
|------|-------------------|
| fullstack | 25 |
| ai | 30 |
| ui_ux | 30 |
| pm | 40 |
| qa | 20 |

------------------------------------------------------------
## FEATURE OBJECT FORMAT
Each feature inside the `features` array must use the **exact structure below**.  
Replace angle-bracket placeholders with relevant values or generated data based on `{json_data}` and budget considerations.  
Use **hours** for all time values (no weeks).

{{
  "feature_name": "<feature_name_placeholder>",
  "description": "<feature_description_placeholder>",
  "acceptance_criteria": [
    "<criterion_placeholder_1>",
    "<criterion_placeholder_2>",
    "<criterion_placeholder_3>"
  ],
  "user_story": "<user_story_placeholder>",
  "dependencies": "<dependencies_placeholder>",
  "deliverables": "<deliverables_placeholder>",
  "resources": [
    {{
      "role": "fullstack",
      "hours": "<fullstack_hours_or_N/A>"
    }},
    {{
      "role": "ai",
      "hours": "<ai_hours_or_N/A>"
    }},
    {{
      "role": "ui_ux",
      "hours": "<ui_ux_hours_or_N/A>"
    }},
    {{
      "role": "pm",
      "hours": "<pm_hours_or_N/A>"
    }},
    {{
      "role": "qa",
      "hours": "<qa_hours_or_N/A>"
    }}
  ],
  "timeline": {{
    "phase": "<phase_placeholder>",
    "duration_hours": "<duration_hours_placeholder>",
    "tasks": [
      {{
        "hour_range": "<hour_range_placeholder>",
        "responsible_role": "<responsible_role_placeholder>",
        "tasks_summary": "<task_summary_placeholder>"
      }}
    ]
  }},
  "cost_estimate": {{
    "fullstack_cost_usd": "<fullstack_cost_numeric_or_0>",
    "ai_cost_usd": "<ai_cost_numeric_or_0>",
    "ui_ux_cost_usd": "<ui_ux_cost_numeric_or_0>",
    "pm_cost_usd": "<pm_cost_numeric_or_0>",
    "qa_cost_usd": "<qa_cost_numeric_or_0>",
    "total_feature_cost_usd": "<total_feature_cost_numeric>"
  }}
}}

### Feature Rules:
- Generate **8–12 features**, unless limited by budget.
- Each feature **must include all roles** listed above.  
  If a role is not used, set its `"hours"` to `"N/A"` and its cost to 0 in `cost_estimate`.
- `duration_hours` = total numeric hours for that feature (ignore "N/A").
- Costs must be computed using the hourly rates table above.
- All cost values must be **plain numbers** (no commas or currency symbols).

------------------------------------------------------------
## RESOURCES ARRAY FORMAT (Top-level)
Provide the team composition for the project in this simplified structure:

[
  {{
    "role": "fullstack",
    "count": "<count_placeholder>"
  }},
  {{
    "role": "ai",
    "count": "<count_placeholder>"
  }},
  {{
    "role": "ui_ux",
    "count": "<count_placeholder>"
  }},
  {{
    "role": "pm",
    "count": "<count_placeholder>"
  }},
  {{
    "role": "qa",
    "count": "<count_placeholder>"
  }}
]

### Resource Notes:
- Use realistic counts (e.g., 2 fullstack developers, 1 designer, 1 PM, 1 QA).
- Reflect staffing level appropriate for the project’s product stage and budget.

------------------------------------------------------------
## TECH ARRAY FORMAT (Top-level)
Provide the project’s technical stack as a simple array of strings:

"tech": [
  "<tech_placeholder_1>",
  "<tech_placeholder_2>",
  "<tech_placeholder_3>"
]

### Tech Selection Rules:
- For smaller budgets, use lower-cost or managed tools.
- For higher budgets, use scalable or enterprise-grade tools.
- Keep the list relevant to `{json_data}` context.

------------------------------------------------------------
## BUDGET OBJECT FORMAT (Top-level)
Include a detailed cost analysis as follows:

{{
  "budget": {{
    "currency": "USD",
    "per_feature": [
      {{
        "feature_name": "<feature_name_placeholder>",
        "total_feature_cost_usd": "<numeric_placeholder>"
      }}
    ],
    "total_estimated_cost_usd": "<numeric_placeholder>",
    "budget_provided": "<original_budget_value_or_null>",
    "within_budget": "<true_or_false_or_null>",
    "notes": "<budget_notes_placeholder>"
  }}
}}

### Budget Rules:
- Compute all costs using the hourly rates table.  
- If a `budget` is provided:
  - `within_budget` = true if provided numeric budget >= total_estimated_cost_usd, else false.
  - If provided budget is non-numeric, set to null.
- Always include all roles in `resources` per feature, even if they’re `"N/A"`.
- If `"N/A"`, cost = 0.
- Summarize per-feature costs under `"per_feature"`, and include total in `"total_estimated_cost_usd"`.

------------------------------------------------------------
## FINAL OUTPUT STRUCTURE (exact)
Output **only** the following JSON object structure — nothing else:

{{
  "features": [ /* feature objects as defined above */ ],
  "resources": [ /* simplified role-count objects */ ],
  "tech": [ /* array of strings */ ],
  "budget": {{ /* budget object as defined above */ }}
}}

------------------------------------------------------------
## RULES & VALIDATION
- All JSON keys must be **snake_case**.
- The entire output must be **valid JSON** — no comments, no trailing commas.
- `features`, `resources`, `tech`, and `budget` are mandatory top-level keys.
- Costs must be accurate based on the provided hourly rates.
- Timeline durations are in **hours** only.
- Each feature includes the **fullstack role** instead of separate backend/frontend roles.
- **Do not output anything else** — no markdown, no commentary, no additional wrapping.

Take a deep breath and work on this problem step-by-step.
"""


    # --- OPENAI CALL ---
    with st.spinner("🧠 Generating estimation using GPT-5..."):
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": PROMPT_TEMPLATE}]
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
            json_part = response[json_start:json_end + 1].strip()
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
        json_cleaned = json_part.strip().replace("```json", "").replace("```", "").strip()
        if not (json_cleaned.startswith("{") and json_cleaned.endswith("}")):
            s = json_cleaned.find("{")
            e = json_cleaned.rfind("}")
            if s != -1 and e != -1 and e > s:
                json_cleaned = json_cleaned[s:e+1]

        parsed_json = json.loads(json_cleaned)

        expected = {"features", "resources", "tech", "budget"}
        if not expected.issubset(parsed_json.keys()):
            st.warning("⚠️ Parsed JSON missing some expected top-level keys (features/resources/tech/budget). Rendering available keys.")

        RATES = {"fullstack": 25, "ai": 30, "ui_ux": 30, "pm": 40, "qa": 20}

        # ---- FEATURES TABLE ----
        st.markdown("<div class='section-title'>🏗️ Features Overview</div>", unsafe_allow_html=True)
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
                res_map = {r.get("role", "").lower(): parse_hours(r.get("hours", "N/A")) for r in resources_list}

                fullstack_h = res_map.get("fullstack")
                ai_h = res_map.get("ai")
                ui_ux_h = res_map.get("ui_ux")
                pm_h = res_map.get("pm")
                qa_h = res_map.get("qa")

                duration_hours = sum(h for h in [fullstack_h, ai_h, ui_ux_h, pm_h, qa_h] if isinstance(h, (int, float)))

                # Compute total cost using hourly rates
                def compute_cost(hours, rate):
                    return round(hours * rate, 2) if isinstance(hours, (int, float)) else 0.0

                total_feature_cost = (
                    compute_cost(fullstack_h, RATES["fullstack"]) +
                    compute_cost(ai_h, RATES["ai"]) +
                    compute_cost(ui_ux_h, RATES["ui_ux"]) +
                    compute_cost(pm_h, RATES["pm"]) +
                    compute_cost(qa_h, RATES["qa"])
                )
                total_feature_cost = round(total_feature_cost, 2)

                feature_rows.append({
                    "feature_name": f.get("feature_name", ""),
                    "description": (f.get("description", "")[:250] + ("..." if len(f.get("description",""))>250 else "")),
                    "phase": f.get("timeline", {}).get("phase", ""),
                    "duration_hours": duration_hours,
                    "fullstack_hours": fullstack_h if fullstack_h is not None else "N/A",
                    "ai_hours": ai_h if ai_h is not None else "N/A",
                    "ui_ux_hours": ui_ux_h if ui_ux_h is not None else "N/A",
                    "pm_hours": pm_h if pm_h is not None else "N/A",
                    "qa_hours": qa_h if qa_h is not None else "N/A",
                    "total_feature_cost_usd": total_feature_cost
                })

            df_features = pd.DataFrame(feature_rows)
            df_features = df_features[
                ["feature_name", "description", "phase", "duration_hours",
                 "fullstack_hours", "ai_hours", "ui_ux_hours", "pm_hours", "qa_hours",
                 "total_feature_cost_usd"]
            ]
            st.dataframe(df_features, use_container_width=True)
        else:
            st.info("No features found in parsed JSON.")

        # ---- RESOURCES TABLE ----
        st.markdown("<div class='section-title'>👥 Resource Summary</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='section-title'>⚙️ Technology Stack</div>", unsafe_allow_html=True)
        tech = parsed_json.get("tech", [])
        if tech and isinstance(tech, list):
            st.dataframe(pd.DataFrame({"technology_tool": tech}), use_container_width=True)
        else:
            st.info("No tech stack found in parsed JSON.")

        # ---- BUDGET SUMMARY ----
        st.markdown("<div class='section-title'>💰 Budget Summary</div>", unsafe_allow_html=True)
        budget_obj = parsed_json.get("budget", {})
        if budget_obj and isinstance(budget_obj, dict):
            currency = budget_obj.get("currency", "USD")
            per_feature = budget_obj.get("per_feature", [])
            total_estimated = budget_obj.get("total_estimated_cost_usd", None)
            budget_provided = budget_obj.get("budget_provided", None)
            within_budget = budget_obj.get("within_budget", None)
            notes = budget_obj.get("notes", "")

            c1, c2, c3 = st.columns([2,2,4])
            with c1:
                st.metric("Currency", currency)
            with c2:
                st.metric("Total Estimated (USD)", str(total_estimated if total_estimated is not None else "N/A"))
            with c3:
                st.metric("Budget Provided", str(budget_provided if budget_provided is not None else "null"))

            st.write(f"**Within budget?** {within_budget}")

            if per_feature and isinstance(per_feature, list):
                df_pf = pd.DataFrame(per_feature)
                if "total_feature_cost_usd" in df_pf.columns:
                    df_pf["total_feature_cost_usd"] = pd.to_numeric(df_pf["total_feature_cost_usd"], errors="coerce").fillna(0)
                st.dataframe(df_pf, use_container_width=True)
            else:
                st.info("No per-feature budget breakdown found in parsed JSON.")

            if notes:
                st.markdown("**Notes:**")
                st.write(notes)
        else:
            st.info("No budget object found in parsed JSON.")

    except Exception as e:
        st.warning(f"⚠️ Could not parse JSON properly — showing raw output below.\n\nParsing error: {e}")
        st.code(response, language="text")

    st.markdown("</div>", unsafe_allow_html=True)



