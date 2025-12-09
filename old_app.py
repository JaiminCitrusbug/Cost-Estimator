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
You are a senior Product Strategist and AI-Powered Software Architect with expertise in accurate software estimation, sprint planning, and scope management. Your task: produce one valid JSON object (no markdown, no prose) that realistically plans and estimates a software product.

------------------------------------------------------------
OBJECTIVE:
Generate one valid JSON object with exactly four top-level keys: `features`, `resources`, `tech`, and `budget`.

------------------------------------------------------------
INPUT ANALYSIS ({{json_data}}):
Required fields:
- project_description (required): The source of truth for what to build
- product_level ("POC", "MVP", or "Full Product"): Determines completeness
- ui_level ("Simple" or "Polished"): Affects UI/UX effort only
- platforms (array): Affects complexity multiplier
- feature_count (optional): Target number if provided
- budget (optional): For budget comparison
- target_audience, competitors (optional): Context for decisions

------------------------------------------------------------
CRITICAL: FEATURE IDENTIFICATION & NAMING METHODOLOGY

STEP 1 - EXTRACT BUSINESS MODULES FROM DESCRIPTION:
- Read the project_description as a product manager would
- Identify distinct functional areas or user-facing capabilities
- Think in terms of what the end-user interacts with, not how it's built
- Group related functionalities into coherent modules

STEP 2 - NAME FEATURES AS BUSINESS MODULES:
- Feature names represent user-facing modules or functional areas
- Use the business domain language from the description
- Format as natural, readable module names (Title Case recommended)
- Names should reflect WHAT users can do, not HOW it's implemented
- Avoid exposing technical implementation details (authentication methods, database types, API protocols, framework names)
- Think: "If this were a menu item or section in the app, what would it be called?"

EXAMPLES OF THINKING PROCESS:
- Description mentions "users can log in and manage accounts" → Feature name: "Auth Module" or "User Authentication"
- Description mentions "search properties and compare investments" → Feature name: "Property Search Module" or "Investment Comparison"
- Description mentions "admin can manage users and content" → Feature name: "Admin Dashboard" or "Admin Management"
- Description mentions "blog with articles and comments" → Feature name: "Blog & Content Module"
- Description mentions "contact form and support tickets" → Feature name: "Contact & Support"

COMMON MODULE PATTERNS (derive similar patterns for your domain):
- Authentication/accounts → Auth-related module name
- Administrative functions → Admin-related module name
- Core business functionality → Domain-specific module name
- Content management → Content-related module name
- Communication features → Communication-related module name
- Data visualization → Analytics/Dashboard-related module name

------------------------------------------------------------
PRODUCT LEVEL INTELLIGENCE:

Understand what each level means for scope:

**POC (Proof of Concept)**:
- Purpose: Validate core idea/feasibility quickly
- Include: Only the minimal features that prove the concept works
- Exclude: Auth (unless central to concept), admin panels, polish, analytics
- Approach: Quick and dirty, hardcoded data acceptable, minimal UI
- Feature count: Typically 2-5 core features only

**MVP (Minimum Viable Product)**:
- Purpose: First production-ready version for early users
- Include: Core features + essential supporting features
- Auth: Include if the product involves user accounts, data persistence, or personalization
- Admin: Include if there's user-generated content, user management, or moderation needs
- Exclude: Nice-to-haves, advanced features, extensive customization
- Approach: Production-quality but minimal scope
- Feature count: Typically 4-9 features

**Full Product**:
- Purpose: Complete, market-ready solution
- Include: All core features + supporting features + advanced capabilities
- Auth: Always include (with password reset, email verification, etc.)
- Admin: Always include (comprehensive management capabilities)
- Also add: Analytics, reporting, notifications, advanced settings
- Approach: Robust, scalable, polished
- Feature count: Typically 8-20 features

DECISION LOGIC:
- Read description → Identify all mentioned/implied capabilities
- Apply product_level filter → Remove features that don't fit the level
- Check dependencies → If keeping feature X, ensure its dependencies are included
- Honor feature_count if provided → Combine or split modules to match count

------------------------------------------------------------
REALISTIC HOUR ESTIMATION METHODOLOGY:

COMPLEXITY ASSESSMENT FRAMEWORK:
Evaluate each feature on these dimensions:
1. **Data Complexity**: Simple forms vs. complex data relationships
2. **Logic Complexity**: CRUD operations vs. complex algorithms
3. **Integration Complexity**: Standalone vs. requires external APIs
4. **UI Complexity**: Basic forms vs. interactive dashboards
5. **Real-time Needs**: Static vs. real-time updates

Assign complexity tier based on overall assessment:
- **Trivial**: Static content, simple display, no backend (8-16 hours)
- **Simple**: Basic CRUD, simple forms, straightforward logic (16-32 hours)
- **Moderate**: Multi-step flows, file handling, search/filter (32-56 hours)
- **Complex**: Real-time features, payment processing, advanced integrations (56-96 hours)
- **Very Complex**: AI/ML features, complex algorithms, multi-system orchestration (96-160 hours)

BASE HOUR CALCULATION:
1. Assess feature complexity → Select base hour range
2. Consider platform count → Apply multiplier (1.0x web-only, up to 1.9x multi-platform)
3. Consider product_level → Apply multiplier (0.7x POC, 1.0x MVP, 1.3x Full)
4. Result = realistic duration_hours for the feature

ROLE DISTRIBUTION LOGIC:
Analyze the feature's nature to determine role split:
- Backend-heavy (APIs, data processing, auth) → More fullstack hours
- Frontend-heavy (dashboards, visualizations, UX flows) → More UI/UX hours
- AI-powered (ML models, NLP, recommendations) → Significant AI hours
- Balanced (standard features with both logic and UI) → Even split

Typical distributions (adapt based on feature nature):
- Fullstack: 40-70% of feature hours
- AI: 0-50% of feature hours (0 if no AI mentioned)
- UI/UX: 20-50% of feature hours

Apply UI_LEVEL modifier:
- Simple UI: Use base UI/UX calculation
- Polished UI: Increase UI/UX hours by 30-50%

VALIDATION - COMMON SENSE CHECK:
- Authentication module should be 24-48 hours (not 160)
- Basic CRUD module should be 16-40 hours
- Admin dashboard should be 32-64 hours
- If any feature exceeds 120 hours, re-evaluate if it should be split

------------------------------------------------------------
PROJECT-LEVEL PM & QA CALCULATION:

After calculating all feature hours:
1. Sum all feature.timeline.duration_hours = total_project_hours
2. Calculate PM hours = 10-12% of total_project_hours (minimum 16 hours)
3. Calculate QA hours = 12-15% of total_project_hours (minimum 20 hours)
4. Round up to nearest reasonable number

Rationale:
- PM: Coordination, planning, stakeholder management grows with project size
- QA: Testing effort scales with features and complexity

------------------------------------------------------------
FEATURE OBJECT FORMAT:
{
  "feature_name": "<module_name_in_business_terms>",
  "description": "<what_this_module_enables_users_to_do>",
  "acceptance_criteria": [
    "<specific_measurable_criterion_1>",
    "<specific_measurable_criterion_2>",
    "<specific_measurable_criterion_3>"
  ],
  "user_story": "As a <user_type>, I want <capability> so that <benefit>",
  "dependencies": "<prerequisite_modules_or_none>",
  "deliverables": "<what_gets_delivered_to_user>",
  "resources": [
    {"role": "fullstack", "hours": <number>},
    {"role": "ai", "hours": <number>},
    {"role": "ui_ux", "hours": <number>}
  ],
  "timeline": {
    "phase": "<Phase_1|Phase_2|Phase_3>",
    "duration_hours": <number>,
    "tasks": [
      {
        "hour_range": "<start-end>",
        "responsible_role": "<role>",
        "tasks_summary": "<high_level_task_description>"
      }
    ]
  },
  "cost_estimate": {
    "fullstack_cost_usd": <number>,
    "ai_cost_usd": <number>,
    "ui_ux_cost_usd": <number>,
    "total_feature_cost_usd": <number>
  }
}

CRITICAL: feature.timeline.duration_hours MUST equal sum of resources[].hours

------------------------------------------------------------
RESOURCES FORMAT:
[
  {"role": "fullstack", "count": <integer>},(0 or 1 or 2 (Based on workload), max 3 for large projects(Rarely needed))
  {"role": "ai", "count": <integer>}, (0 or 1 or 2(only in case of AI heavy workload))
  {"role": "ui_ux", "count": <integer>},(0 or 1)
  {"role": "pm", "count": 1},
  {"role": "qa", "count": <integer>}
]

Count calculation approach:
- Assume 160 productive hours per person per month
- Calculate: count = ceil(total_role_hours / 160)
- Minimum count = 1 for any role with hours > 0
- Scale appropriately for project size and timeline

------------------------------------------------------------
TECH STACK SELECTION:

Build the tech stack using these foundational technologies, adapting based on project needs:

**Core Stack (Always Include):**
- UI Design: "Figma"
- Frontend: "React"
- Backend: Select based on requirements:
  - "Python FastAPI" (data-heavy, AI/ML features, complex algorithms)
  - "Node.js/Express" (real-time features, simple APIs, JavaScript-centric teams)
- Database: Select based on data needs:
  - "PostgreSQL" (complex queries, relational data, high scalability)
  - "MySQL" (standard relational needs, cost-effective)
  - "Firebase" (rapid development, real-time features, serverless preference)

**Conditional Additions (Add when requirements indicate):**
- Email functionality mentioned → Add "SendGrid"
- Payment/subscription/billing mentioned → Add "Stripe"
- Authentication needed → Add appropriate auth solution:
  - "Firebase Auth" (if using Firebase database)
  - "Auth0" (enterprise, complex auth flows)
  - "NextAuth.js" or "Passport.js" (custom auth, lower cost)
- File storage/uploads mentioned → Add "AWS S3" or "Cloudinary"
- Real-time features → Add "Socket.io" or "Firebase Realtime Database"
- AI/ML capabilities → Add "OpenAI API", "Hugging Face", or "TensorFlow"
- Analytics mentioned → Add "Google Analytics" or "Mixpanel"
- Search functionality → Add "Elasticsearch" or "Algolia"
- Mobile platforms → Add "React Native"
- Hosting/Deployment → Select based on product_level:
  - POC: "Vercel" + "Render" or "Railway"
  - MVP/Full: "AWS" or "Google Cloud" or "Digital Ocean"
- Monitoring (Full Product) → Add "Sentry"
- CI/CD (Full Product) → Add "GitHub Actions"

**Selection Logic:**
1. Start with core stack (Figma, React, Backend choice, Database choice)
2. Scan project_description for keywords (payment, email, AI, real-time, etc.)
3. Add conditional technologies based on what's mentioned
4. Consider product_level for infrastructure choices
5. Return 6-12 technologies total as array of strings

**Output Format:**
Return as array of strings, e.g.:
["Figma", "React", "Python FastAPI", "PostgreSQL", "SendGrid", "Stripe", "AWS", "Sentry"]

------------------------------------------------------------
BUDGET FORMAT:
{
  "currency": "USD",
  "per_feature": [
    {"feature_name": "<name>", "total_feature_cost_usd": <number>}
  ],
  "total_estimated_cost_usd": <number>,
  "budget_provided": <number_or_null>,
  "within_budget": <true|false|null>,
  "pm_total_hours": <number>,
  "qa_total_hours": <number>,
  "pm_qa_costs_excluded": true,
  "cost_breakdown": {
    "fullstack_total_usd": <number>,
    "ai_total_usd": <number>,
    "ui_ux_total_usd": <number>
  },
  "notes": "<concise_summary_and_recommendations>"
}

------------------------------------------------------------
HOURLY RATES (USD):
- fullstack: $25/hour
- ai: $30/hour
- ui_ux: $30/hour
(PM and QA hours tracked but costs excluded from total)

COST CALCULATION:
- Each feature cost = (fullstack_hours × 25) + (ai_hours × 30) + (ui_ux_hours × 30)
- Total cost = sum of all feature costs
- Budget comparison: within_budget = (budget_provided >= total_estimated_cost_usd) if budget provided

------------------------------------------------------------
VALIDATION & CONSISTENCY CHECKS:

Before finalizing JSON, verify:
1. ✓ Feature names are business-domain terms, not technical implementation details
2. ✓ All features mentioned in description are represented
3. ✓ No unnecessary features added beyond description + product_level requirements
4. ✓ Hour estimates are realistic (auth ≠ 160 hours)
5. ✓ Each feature.timeline.duration_hours = sum(feature.resources[].hours)
6. ✓ Total costs correctly calculated (feature costs + cost_breakdown match)
7. ✓ PM and QA hours are reasonable (10-15% of total project hours)
8. ✓ Resource counts align with total hours (using 160 hours/month guideline)
9. ✓ Tech stack matches product_level and requirements
10. ✓ If feature_count provided, output matches (or notes explain why not)

------------------------------------------------------------
EXECUTION SEQUENCE:

1. **Deep Read**: Carefully read and understand project_description
   - List every capability or feature mentioned
   - Infer implied features (e.g., "users save preferences" implies auth)
   - Note domain-specific terminology

2. **Module Extraction**: Identify business modules
   - Group related capabilities into logical modules
   - Name modules using business/domain language
   - Ensure names are user-facing, not implementation-facing

3. **Scope Filtering**: Apply product_level filter
   - POC: Keep only core concept validation features
   - MVP: Add auth/admin only if genuinely needed
   - Full Product: Include comprehensive feature set

4. **Feature Estimation**: For each feature
   - Assess complexity tier
   - Calculate base hours with multipliers
   - Distribute hours across roles intelligently
   - Validate hours are realistic

5. **Aggregate Calculations**:
   - Sum total project hours
   - Calculate PM hours (10-12% of total)
   - Calculate QA hours (12-15% of total)
   - Calculate all costs

6. **Resource Planning**: Determine headcount based on hour totals

7. **Tech Selection**: Choose appropriate stack for level and requirements

8. **Final Validation**: Run all consistency checks

9. **Output**: Generate clean, valid JSON

------------------------------------------------------------
OUTPUT REQUIREMENTS:
- Valid JSON only (no markdown, no prose, no code blocks)
- All numeric values as numbers, not strings
- All keys in snake_case
- Realistic, defensible estimates
- Feature names as business modules, not technical implementations
- Hours that reflect actual development time
- Complete mathematical consistency

------------------------------------------------------------
REMEMBER:
- Think like a product manager when naming features
- Think like a developer when estimating hours
- Be realistic, not optimistic or pessimistic
- Honor the project_description as the source of truth
- Apply product_level as a scope filter, not a feature generator
- Validate everything before output
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
            budget_provided = budget
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
