"""
IVC Pharma Executive Dashboard
Streamlit + Plotly + Pandas — single-file app
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re
from io import BytesIO
from name_map import (
    normalize_mr, mr_display_name, MR_CANONICAL,
    normalize_product, product_display_name, product_category,
    normalize_activity, activity_display_name,
    normalize_territory, territory_display_name,
    normalize_doctor, build_doctor_index,
    normalize_distributor, distributor_display_name,
)

# IDs that are NOT field MRs — exclude from MR Performance tab
_NON_MR_IDS = {"MR_006", "AGT_001", "UNKNOWN"}

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
FCFA_TO_EUR = 655.97
TEMPLATE = "plotly_dark"

DISTRIBUTORS = [
    "UBIPHARM/LABOREX",
    "COPHARMED/LABOREX",
    "TEDIS",
    "DPCI",
]

# Color palette
CLR_GREEN  = "#00C49A"
CLR_RED    = "#FF4C61"
CLR_BLUE   = "#4C9FFF"
CLR_ORANGE = "#FF9F40"
CLR_PURPLE = "#B57BFF"
CLR_TEAL   = "#26C6DA"
CLR_YELLOW = "#FFD166"

DIST_COLORS = {
    "UBIPHARM/LABOREX":  CLR_BLUE,
    "COPHARMED/LABOREX": CLR_GREEN,
    "TEDIS":             CLR_ORANGE,
    "DPCI":              CLR_PURPLE,
}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def to_eur(fcfa: float) -> float:
    return round(fcfa / FCFA_TO_EUR, 2)


def fmt_currency(val: float, unit: str) -> str:
    if unit == "EUR":
        return f"€ {val:,.2f}"
    return f"FCFA {val:,.0f}"


def safe_num(val):
    try:
        return float(val)
    except Exception:
        return 0.0




def placeholder_tab(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:400px;">
            <div style="background:linear-gradient(135deg,#1e2a3a,#2a3a50);
                        border:1px solid #3a5070;border-radius:16px;
                        padding:48px 64px;text-align:center;max-width:500px;">
                <div style="font-size:48px;margin-bottom:16px;">🚧</div>
                <h2 style="color:#4C9FFF;margin:0 0 8px 0;">{title}</h2>
                <p style="color:#8899aa;margin:0;">{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(cards: list):
    """
    cards = [{"label": str, "value": str, "delta": str|None, "color": str}, ...]
    """
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        color = card.get("color", CLR_BLUE)
        delta_html = ""
        if card.get("delta"):
            delta_color = CLR_GREEN if "+" in str(card["delta"]) else CLR_RED
            delta_html = f'<div style="color:{delta_color};font-size:13px;margin-top:4px;">{card["delta"]}</div>'
        col.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1a2535,#1e2e42);
                        border-left:4px solid {color};border-radius:10px;
                        padding:18px 20px;margin-bottom:8px;">
                <div style="color:#8899aa;font-size:12px;text-transform:uppercase;
                            letter-spacing:1px;margin-bottom:6px;">{card['label']}</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700;">{card['value']}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_sales(file_bytes: bytes) -> dict:
    """
    Returns dict with keys 'jan' and 'feb', each a DataFrame:
    columns: Product, Category, RATE,
             UBIPHARM/LABOREX_SALES, COPHARMED/LABOREX_SALES, TEDIS_SALES, DPCI_SALES,
             UBIPHARM/LABOREX_CLOSING, ...  TOTAL_SALES, TOTAL_VALUE_EUR
    """
    results = {}
    for sheet, month in [("JAN-26", "jan"), ("FEB-26", "feb")]:
        raw = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet, header=None)
        # Row 2 = distributor names (spread across merged cells), Row 3 = sub-cols
        # Data rows start at row 4 (index 4)
        rows = []
        current_category = "TABLET"
        for i, row in raw.iterrows():
            if i < 4:
                continue
            sr = row.iloc[1]
            product = str(row.iloc[2]).strip()
            # detect category change
            cat_label = str(row.iloc[0]).strip().upper()
            if "INJECTABLE" in cat_label:
                current_category = "INJECTABLE"
            elif "TABLET" in cat_label:
                current_category = "TABLET"
            # skip totals / non-product rows
            if not isinstance(sr, (int, float)) or pd.isna(sr):
                continue
            if sr > 17:  # skip TOTAL (A+B) row which has sr=20
                continue
            if "TOTAL" in str(product).upper() or str(product).upper() in ("NAN", ""):
                continue
            rate = safe_num(row.iloc[3])
            # Column layout per distributor: SALES(4), CLOSING(5), ORDER(6) | next dist +3
            rec = {
                "Product": product,
                "Category": current_category,
                "RATE": rate,
            }
            base = 4
            for dist in DISTRIBUTORS:
                rec[f"{dist}_SALES"]   = safe_num(row.iloc[base])
                rec[f"{dist}_CLOSING"] = safe_num(row.iloc[base + 1])
                rec[f"{dist}_ORDER"]   = safe_num(row.iloc[base + 2])
                base += 3
            # TOTAL SALES
            rec["TOTAL_SALES"] = sum(rec[f"{d}_SALES"] for d in DISTRIBUTORS)
            # TOTAL VALUE EUR (last col)
            rec["TOTAL_VALUE_EUR"] = safe_num(row.iloc[-1])
            rows.append(rec)
        results[month] = pd.DataFrame(rows)
    return results


@st.cache_data(show_spinner=False)
def load_projection(file_bytes: bytes) -> dict:
    """
    Returns dict:
      'projection': DataFrame — Product, RATE, Target_Units, Target_Value_EUR
      'activity_plan': DataFrame — SN, Doctor, Hospital, Speciality, Delegate, Area, Activity, Amount_FCFA, Focus_Products
    """
    xl = pd.ExcelFile(BytesIO(file_bytes))

    # ── PROJECTION sheet ──
    raw_p = pd.read_excel(xl, sheet_name="PROJECTION", header=None)
    proj_rows = []
    for i, row in raw_p.iterrows():
        if i < 3:
            continue
        sn = row.iloc[0]
        if not isinstance(sn, (int, float)) or pd.isna(sn):
            continue
        product = str(row.iloc[1]).strip()
        if not product or product.upper() in ("NAN",):
            continue
        proj_rows.append({
            "Product": product,
            "RATE": safe_num(row.iloc[2]),
            "Target_Units": safe_num(row.iloc[3]),
            "Target_Value_EUR": safe_num(row.iloc[4]),
        })
    proj_df = pd.DataFrame(proj_rows)

    # ── ACTIVITY PLAN sheet ──
    sheet_name = [s for s in xl.sheet_names if "ACTIVITY" in s.upper()][0]
    raw_a = pd.read_excel(xl, sheet_name=sheet_name, header=None)
    act_rows = []
    for i, row in raw_a.iterrows():
        if i < 2:
            continue
        sn = row.iloc[0]
        if not isinstance(sn, (int, float)) or pd.isna(sn):
            continue
        act_rows.append({
            "SN": int(sn),
            "Doctor": normalize_doctor(str(row.iloc[1]).strip()),
            "Hospital": str(row.iloc[2]).strip(),
            "Speciality": str(row.iloc[3]).strip(),
            "Delegate": normalize_mr(str(row.iloc[4]).strip()),
            "Area": normalize_territory(str(row.iloc[5]).strip()),
            "Activity": normalize_activity(str(row.iloc[6]).strip()),
            "Amount_FCFA": safe_num(row.iloc[7]),
            "Focus_Products": normalize_product(str(row.iloc[8]).strip()),
        })
    act_df = pd.DataFrame(act_rows)
    return {"projection": proj_df, "activity_plan": act_df}


@st.cache_data(show_spinner=False)
def load_expense(file_bytes: bytes) -> dict:
    """
    Returns dict:
      'activity_exp': DataFrame — SN, Doctor, Hospital, Speciality, Activity, Products, Amount_FCFA, Contact, Responsible
      'other_exp': DataFrame — SN, Country, Details, Amount_FCFA, Amount_EUR, Comments, Category
      'money_received': DataFrame — Date, Source, Amount_FCFA, Amount_EUR, Description
      'total_received_fcfa', 'total_spent_fcfa', 'balance_fcfa'
    """
    xl = pd.ExcelFile(BytesIO(file_bytes))

    # ── MONEY RECEIVED ──
    raw_mr = pd.read_excel(xl, sheet_name="MONEY RECEIVED", header=None)
    mr_rows = []
    for i, row in raw_mr.iterrows():
        if i < 2:
            continue
        date_val = row.iloc[0]
        if pd.isna(date_val) or str(date_val).strip() in ("", "NaN", "Date"):
            continue
        if "TOTAL" in str(date_val).upper():
            continue
        try:
            date_val = pd.to_datetime(date_val)
        except Exception:
            continue
        mr_rows.append({
            "Date": date_val,
            "Source": str(row.iloc[1]).strip(),
            "Amount_FCFA": safe_num(row.iloc[2]),
            "Amount_EUR": safe_num(row.iloc[3]),
            "Description": str(row.iloc[4]).strip(),
        })
    mr_df = pd.DataFrame(mr_rows)

    # Pull summary totals from the sheet
    total_received_fcfa = 0
    total_spent_fcfa = 0
    balance_fcfa = 0
    for i, row in raw_mr.iterrows():
        label = str(row.iloc[0]).upper()
        col5  = str(row.iloc[5]).upper() if len(row) > 5 else ""
        # Total received appears in col 2 on the TOTALFCFA/EURO row
        if "TOTAL" in label and ("RECEIV" in label or "FCFA" in label):
            v = safe_num(row.iloc[2])
            if v > 0:
                total_received_fcfa = v
        if "TOTAL SPENT" in col5:
            total_spent_fcfa = safe_num(row.iloc[6])
        if "BALANCE" in col5:
            balance_fcfa = safe_num(row.iloc[6])
    # Fallback: derive received from money_received rows
    if total_received_fcfa == 0 and not mr_df.empty:
        total_received_fcfa = mr_df["Amount_FCFA"].sum()

    # ── ACTIVITY EXP ──
    raw_ae = pd.read_excel(xl, sheet_name="ACTIVITY EXP.", header=None)
    ae_rows = []
    for i, row in raw_ae.iterrows():
        if i < 2:
            continue
        sn = row.iloc[0]
        if not isinstance(sn, (int, float)) or pd.isna(sn):
            continue
        raw_resp = str(row.iloc[8]).strip()
        # Resolve joint entries like "JITENDRA/CLEMANCE" → ["MR_006", "MR_002"]
        if "/" in raw_resp:
            mr_ids = ",".join(normalize_mr(p.strip()) for p in raw_resp.split("/"))
        else:
            mr_ids = normalize_mr(raw_resp)
        ae_rows.append({
            "SN": int(sn),
            "Doctor": normalize_doctor(str(row.iloc[1]).strip()),
            "Hospital": str(row.iloc[2]).strip(),
            "Speciality": str(row.iloc[3]).strip(),
            "Activity": str(row.iloc[4]).strip(),
            "Activity_ID": normalize_activity(str(row.iloc[4]).strip()),
            "Products": normalize_product(str(row.iloc[5]).strip()),
            "Amount_FCFA": safe_num(row.iloc[6]),
            "Contact": str(row.iloc[7]).strip(),
            "Responsible": raw_resp,
            "MR_IDs": mr_ids,  # normalized, comma-sep for joint entries
        })
    ae_df = pd.DataFrame(ae_rows)
    # Apply proper Activity names
    ae_df["Activity"] = ae_df["Activity_ID"].apply(activity_display_name)

    # ── OTHER EXP ──
    raw_oe = pd.read_excel(xl, sheet_name="OTHER EXP.", header=None)
    oe_rows = []
    for i, row in raw_oe.iterrows():
        if i < 2:
            continue
        sn = row.iloc[0]
        if not isinstance(sn, (int, float)) or pd.isna(sn):
            continue
        amount_fcfa = safe_num(row.iloc[3])
        if amount_fcfa == 0:
            continue
        oe_rows.append({
            "SN": int(sn),
            "Country": str(row.iloc[1]).strip(),
            "Details": str(row.iloc[2]).strip(),
            "Amount_FCFA": amount_fcfa,
            "Amount_EUR": safe_num(row.iloc[4]),
            "Comments": str(row.iloc[5]).strip(),
            "Category": str(row.iloc[6]).strip(),
        })
    oe_df = pd.DataFrame(oe_rows)

    return {
        "activity_exp": ae_df,
        "other_exp": oe_df,
        "money_received": mr_df,
        "total_received_fcfa": total_received_fcfa,
        "total_spent_fcfa": total_spent_fcfa,
        "balance_fcfa": balance_fcfa,
    }


@st.cache_data(show_spinner=False)
def load_monthly_reports(file_bytes: bytes) -> dict:
    """
    Returns dict:
      'delegates': DataFrame — SN, Delegate, Territory, NonPrescriber, Prescriber,
                               DrsConverted, TotalCalls, PharmacyCalls, DaysTarget,
                               DaysWorked, AvgCallsPerDay, TotalOrders, CTC
      'budget_analysis': DataFrame — Doctor, Area, MR, ActivityType, Value_FCFA
    """
    xl = pd.ExcelFile(BytesIO(file_bytes))

    # ── Delegates ──
    raw_d = pd.read_excel(xl, sheet_name="Delegates Reports", header=None)
    del_rows = []
    for i, row in raw_d.iterrows():
        if i < 3:
            continue
        sn = row.iloc[0]
        if not isinstance(sn, (int, float)) or pd.isna(sn):
            continue
        delegate = str(row.iloc[1]).strip()
        if any(k in delegate.upper() for k in ("TOTAL", "TARGET")):
            continue
        del_rows.append({
            "SN": int(sn),
            "Delegate": delegate,
            "Territory": str(row.iloc[2]).strip(),
            "NonPrescriber": safe_num(row.iloc[3]),
            "Prescriber": safe_num(row.iloc[4]),
            "DrsConverted": safe_num(row.iloc[5]),
            "TotalCalls": safe_num(row.iloc[6]),
            "PharmacyCalls": safe_num(row.iloc[7]),
            "DaysTarget": safe_num(row.iloc[8]),
            "DaysWorked": safe_num(row.iloc[9]),
            "AvgCallsPerDay": safe_num(row.iloc[10]),
            "TotalOrders": safe_num(row.iloc[11]),
            "CTC": safe_num(row.iloc[12]),
        })
    del_df = pd.DataFrame(del_rows)

    # ── Budget Analysis ──
    raw_b = pd.read_excel(xl, sheet_name="Budget Analysis", header=None)
    ba_rows = []
    for i, row in raw_b.iterrows():
        if i < 2:
            continue
        doctor = str(row.iloc[0]).strip()
        if not doctor or doctor.upper() in ("NAN", "DR. NAME"):
            continue
        ba_rows.append({
            "Doctor": normalize_doctor(doctor),
            "Area": normalize_territory(str(row.iloc[1]).strip()),
            "MR": normalize_mr(str(row.iloc[2]).strip()),
            "ActivityType": normalize_activity(str(row.iloc[3]).strip()),
            "Value_FCFA": safe_num(row.iloc[4]),
        })
    ba_df = pd.DataFrame(ba_rows)

    return {"delegates": del_df, "budget_analysis": ba_df}


@st.cache_data(show_spinner=False)
def load_visit_tracker(files_and_months: list) -> pd.DataFrame:
    """
    files_and_months: list of (file_bytes, month_label) tuples e.g. [(bytes,'Feb'), (bytes,'Mar')]
    Returns flat DataFrame: MR_ID, MR, Doctor, Speciality, Clinic, Visit_Date, Month
    """
    all_rows = []
    for file_bytes, month_label in files_and_months:
        xl = pd.ExcelFile(BytesIO(file_bytes))
        for sheet in xl.sheet_names:
            raw = pd.read_excel(xl, sheet_name=sheet, header=None)
            try:
                mr_name = str(raw.iloc[0, 2]).strip()
            except Exception:
                mr_name = sheet
            if not mr_name or mr_name.upper() in ("NAN", ""):
                mr_name = sheet
            mr_id = normalize_mr(mr_name)

            header_row = raw.iloc[3]
            visit_cols = [
                c for c in raw.columns
                if "visit" in str(header_row[c]).lower()
            ]
            doc_col = next(
                (c for c in raw.columns if "NOM" in str(header_row[c]).upper()), None
            )
            spec_col = next(
                (c for c in raw.columns if "SPEC" in str(header_row[c]).upper()), None
            )
            clinic_col = next(
                (c for c in raw.columns
                 if "CLINIC" in str(header_row[c]).upper()
                 or "HOSPITAL" in str(header_row[c]).upper()
                 or "CSPS" in str(header_row[c]).upper()), None
            )

            for vc in visit_cols:
                raw[vc] = pd.to_datetime(raw[vc], errors="coerce")

            for i, row in raw.iterrows():
                if i <= 3:
                    continue
                doctor = str(row[doc_col]).strip() if doc_col is not None else ""
                if not doctor or doctor.upper() in ("NAN", "NOM /PERNOM", ""):
                    continue
                speciality = str(row[spec_col]).strip() if spec_col is not None else ""
                clinic = str(row[clinic_col]).strip() if clinic_col is not None else ""
                for vc in visit_cols:
                    vdate = row[vc]
                    if pd.isna(vdate):
                        continue
                    all_rows.append({
                        "MR_ID": mr_id,
                        "MR": mr_display_name(mr_id) if mr_id not in ("UNKNOWN",) else mr_name,
                        "Doctor": doctor,
                        "Speciality": speciality,
                        "Clinic": clinic,
                        "Visit_Date": vdate,
                        "Month": month_label,
                    })
    if all_rows:
        df = pd.DataFrame(all_rows)
        df["Visit_Date"] = pd.to_datetime(df["Visit_Date"])
        return df
    return pd.DataFrame(columns=["MR_ID","MR","Doctor","Speciality","Clinic","Visit_Date","Month"])


def is_covered(plan, actual):
    if not plan or not actual or str(plan).strip() in ('nan', '') or str(actual).strip() in ('nan', ''):
        return False

    p_up = str(plan).upper()
    a_up = str(actual).upper()

    # Strip common generic words that might cause false positives
    stopwords = {"ZONE", "DE", "DU", "LA", "LE", "LES"}

    p_words = set(w for w in re.findall(r'[A-Z0-9]{3,}', p_up) if w not in stopwords)
    a_words = set(w for w in re.findall(r'[A-Z0-9]{3,}', a_up) if w not in stopwords)

    if not p_words or not a_words:
        return p_up == a_up

    # Covered if intersection is not empty
    return len(p_words & a_words) > 0

@st.cache_data(show_spinner=False)
def load_tour_plan(file_bytes: bytes) -> pd.DataFrame:
    raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0)

    # Assuming columns: Date, Name, Joint working, Tour plan, Working Area
    # We will rename to standard keys if they match the expected format
    cols = list(raw.columns)

    rows = []
    for i, row in raw.iterrows():
        name = str(row.iloc[1]).strip() if len(cols) > 1 else ""
        if not name or name.upper() in ("NAN", "NAME"):
            continue

        plan = str(row.iloc[3]).strip() if len(cols) > 3 else ""
        actual = str(row.iloc[4]).strip() if len(cols) > 4 else ""
        joint = str(row.iloc[2]).strip() if len(cols) > 2 else ""

        # Check coverage
        coverage = is_covered(plan, actual)

        rows.append({
            "Date": row.iloc[0],
            "MR": normalize_mr(name),
            "Joint_Working": joint,
            "Planned_Area": plan,
            "Actual_Area": actual,
            "Covered": coverage
        })

    df = pd.DataFrame(rows)
    return df

@st.cache_data(show_spinner=False)
def load_copy_report(file_bytes: bytes) -> dict:
    """
    Returns dict:
      'product_perf': DataFrame — Product, RATE, Target_Units, Achieved_Units
      'plan_activities': DataFrame — Doctor, Hospital, Speciality, Activity, Amount_FCFA (planned)
      'actual_activities': DataFrame — Doctor, Hospital, Speciality, Activity, Amount_FCFA (actual), Remarks, VisitedBy, NoOfVisits
    """
    raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)

    prod_rows = []
    plan_rows = []
    actual_rows = []

    for i, row in raw.iterrows():
        if i < 2:
            continue
        sn = row.iloc[0]
        if isinstance(sn, (int, float)) and not pd.isna(sn):
            product = str(row.iloc[1]).strip()
            if product and product.upper() not in ("NAN", "PRODUCTS"):
                prod_rows.append({
                    "Product": product,
                    "RATE": safe_num(row.iloc[2]),
                    "Target_Units": safe_num(row.iloc[3]),
                    "Achieved_Units": safe_num(row.iloc[4]),
                })

        # RIGHT-PLAN (cols 5-9)
        doc_plan = str(row.iloc[5]).strip()
        if doc_plan and doc_plan.upper() not in ("NAN", "NAME OF DOCTOR", ""):
            plan_rows.append({
                "Doctor": normalize_doctor(doc_plan),
                "Hospital": str(row.iloc[6]).strip(),
                "Speciality": str(row.iloc[7]).strip(),
                "Activity": normalize_activity(str(row.iloc[8]).strip()),
                "Amount_FCFA": safe_num(row.iloc[9]),
            })

        # RIGHT-ACTUAL (cols 10-17)
        doc_actual = str(row.iloc[10]).strip()
        if doc_actual and doc_actual.upper() not in ("NAN", "DOCTOR NAME", ""):
            actual_rows.append({
                "Doctor": normalize_doctor(doc_actual),
                "Hospital": str(row.iloc[11]).strip(),
                "Speciality": str(row.iloc[12]).strip(),
                "Activity": normalize_activity(str(row.iloc[13]).strip()),
                "Amount_FCFA": safe_num(row.iloc[14]),
                "Remarks": str(row.iloc[15]).strip(),
                "VisitedBy": normalize_mr(str(row.iloc[16]).strip()),
                "NoOfVisits": safe_num(row.iloc[17]),
            })

    return {
        "product_perf": pd.DataFrame(prod_rows),
        "plan_activities": pd.DataFrame(plan_rows),
        "actual_activities": pd.DataFrame(actual_rows),
    }

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — PERFORMANCE OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

def render_tab1(sales_data, proj_data, copy_data, currency):
    feb = sales_data["feb"]
    jan = sales_data["jan"]
    proj = proj_data["projection"]
    prod_perf = copy_data["product_perf"]

    # ── KPI cards ──
    total_feb_eur = feb["TOTAL_VALUE_EUR"].sum()
    total_target_eur = proj["Target_Value_EUR"].sum()
    ach_pct = (total_feb_eur / total_target_eur * 100) if total_target_eur else 0
    color_ach = CLR_GREEN if ach_pct >= 100 else CLR_RED

    if currency == "EUR":
        feb_val  = fmt_currency(total_feb_eur, "EUR")
        tgt_val  = fmt_currency(total_target_eur, "EUR")
    else:
        feb_val  = fmt_currency(total_feb_eur * FCFA_TO_EUR, "FCFA")
        tgt_val  = fmt_currency(total_target_eur * FCFA_TO_EUR, "FCFA")

    kpi_row([
        {"label": "Total Feb Sales", "value": feb_val, "color": CLR_BLUE},
        {"label": "Feb Target", "value": tgt_val, "color": CLR_ORANGE},
        {"label": "Achievement %", "value": f"{ach_pct:.1f}%",
         "delta": f"+{ach_pct-100:.1f}%" if ach_pct >= 100 else f"{ach_pct-100:.1f}%",
         "color": color_ach},
    ])
    st.markdown("---")

    # ── Target vs Achieved — grouped bar (from copy report) ──
    st.subheader("🎯 Target vs Achieved Units")
    if not prod_perf.empty:
        pp = prod_perf.copy()
        pp["short"] = pp["Product"].apply(lambda x: x[:18])
        fig_ta = go.Figure()
        fig_ta.add_bar(
            name="Target Units", x=pp["short"], y=pp["Target_Units"],
            marker_color=CLR_ORANGE, text=pp["Target_Units"].astype(int),
            textposition="outside",
        )
        fig_ta.add_bar(
            name="Achieved Units", x=pp["short"], y=pp["Achieved_Units"],
            marker_color=pp["Achieved_Units"].apply(
                lambda v: CLR_GREEN if v >= pp["Target_Units"].mean() else CLR_RED
            ),
            text=pp["Achieved_Units"].astype(int), textposition="outside",
        )
        fig_ta.update_layout(
            barmode="group", template=TEMPLATE, height=380,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.12),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig_ta, width='stretch')
    else:
        st.info("Upload 'Copy of Report' file to see this chart.")

    st.markdown("---")

    # ── Jan vs Feb line chart per product ──
    st.subheader("📈 Jan → Feb Sales Trend (Units)")
    if not jan.empty and not feb.empty:
        jan_s = jan[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Jan"})
        feb_s = feb[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Feb"})
        trend = jan_s.merge(feb_s, on="Product", how="outer").fillna(0)
        trend_long = trend.melt(id_vars="Product", var_name="Month", value_name="Units")
        fig_trend = px.line(
            trend_long, x="Month", y="Units", color="Product",
            markers=True, template=TEMPLATE, height=400,
        )
        fig_trend.update_traces(line_width=2.5)
        fig_trend.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20), legend_title="Product",
        )
        st.plotly_chart(fig_trend, width='stretch')

    # Jan vs Feb comparison line
    if not jan.empty and not feb.empty:
        st.subheader("📊 Jan vs Feb Sales Comparison (Units)")
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatter(name="Jan", x=trend["Product"], y=trend["Jan"],
                                     mode='lines+markers', line=dict(color=CLR_BLUE, width=2)))
        fig_cmp.add_trace(go.Scatter(name="Feb", x=trend["Product"], y=trend["Feb"],
                                     mode='lines+markers', line=dict(color=CLR_TEAL, width=2)))
        fig_cmp.update_layout(
            template=TEMPLATE, height=360,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=40), xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_cmp, width='stretch')

    st.markdown("---")

    # ── Distributor 2x2 subplots with MoM Growth ──
    st.subheader("🏭 Sales by Distributor (Units) with MoM Growth")
    if not feb.empty and not jan.empty:
        fig_dist = make_subplots(
            rows=2, cols=2,
            subplot_titles=DISTRIBUTORS,
            shared_yaxes=False,
            vertical_spacing=0.25,
            horizontal_spacing=0.08,
        )
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for (r, c), dist in zip(positions, DISTRIBUTORS):
            col_key = f"{dist}_SALES"
            if col_key not in feb.columns or col_key not in jan.columns:
                continue

            # Merge Jan and Feb for this distributor
            d_jan = jan[["Product", col_key]].rename(columns={col_key: "Jan_Sales"})
            d_feb = feb[["Product", col_key]].rename(columns={col_key: "Feb_Sales"})
            sub = pd.merge(d_feb, d_jan, on="Product", how="left").fillna(0)

            # Filter where there is at least some sale
            sub = sub[(sub["Feb_Sales"] > 0) | (sub["Jan_Sales"] > 0)].copy()
            sub = sub.sort_values("Feb_Sales", ascending=True)

            # Calculate MoM growth percentage
            sub["MoM_Text"] = sub.apply(
                lambda row: f"+{((row['Feb_Sales'] - row['Jan_Sales'])/row['Jan_Sales']*100):.0f}%" if row['Jan_Sales'] > 0 and row['Feb_Sales'] > row['Jan_Sales'] else (
                            f"{((row['Feb_Sales'] - row['Jan_Sales'])/row['Jan_Sales']*100):.0f}%" if row['Jan_Sales'] > 0 else "New"),
                axis=1
            )

            # Create text to display value and MoM
            sub["Display_Text"] = sub["Feb_Sales"].astype(int).astype(str) + " (" + sub["MoM_Text"] + ")"

            trace = go.Bar(
                name=dist,
                x=sub["Feb_Sales"],
                y=sub["Product"],
                orientation="h",
                marker_color=DIST_COLORS[dist],
                text=sub["Display_Text"],
                textposition="outside",
                showlegend=False,
            )
            fig_dist.add_trace(trace, row=r, col=c)

        fig_dist.update_layout(
            template=TEMPLATE, height=700,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig_dist, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — DOCTOR SPEND
# ─────────────────────────────────────────────────────────────────────────────

def render_tab2(proj_data, expense_data, copy_data, currency):
    act_plan = proj_data["activity_plan"]
    ae = expense_data["activity_exp"]

    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    # ── KPI cards ──
    total_planned = act_plan["Amount_FCFA"].sum()
    total_actual  = ae["Amount_FCFA"].sum()
    gap           = total_planned - total_actual

    kpi_row([
        {"label": "Total Planned Spend", "value": fmt_currency(total_planned * mul, unit),
         "color": CLR_ORANGE},
        {"label": "Total Actual Spend",  "value": fmt_currency(total_actual * mul, unit),
         "color": CLR_BLUE},
        {"label": "Gap (Planned − Actual)",
         "value": fmt_currency(abs(gap) * mul, unit),
         "delta": f"+{'Surplus' if gap > 0 else 'Over-spend'}",
         "color": CLR_GREEN if gap >= 0 else CLR_RED},
    ])
    st.markdown("---")

    # ── Planned vs Actual per doctor ──
    st.subheader("👨‍⚕️ Planned vs Actual Spend per Doctor")
    plan_agg = act_plan.groupby("Doctor")["Amount_FCFA"].sum().reset_index()
    plan_agg.columns = ["Doctor", "Planned_FCFA"]
    act_agg  = ae.groupby("Doctor")["Amount_FCFA"].sum().reset_index()
    act_agg.columns = ["Doctor", "Actual_FCFA"]

    merged = plan_agg.merge(act_agg[["Doctor", "Actual_FCFA"]], on="Doctor", how="outer").fillna(0)
    merged = merged[(merged["Planned_FCFA"] > 0) | (merged["Actual_FCFA"] > 0)]
    merged = merged.sort_values("Planned_FCFA", ascending=True)

    if not merged.empty:
        fig_doc = go.Figure()
        fig_doc.add_bar(
            name="Planned", x=merged["Planned_FCFA"] * mul,
            y=merged["Doctor"], orientation="h", marker_color=CLR_ORANGE,
        )
        fig_doc.add_bar(
            name="Actual", x=merged["Actual_FCFA"] * mul,
            y=merged["Doctor"], orientation="h", marker_color=CLR_BLUE,
        )
        fig_doc.update_layout(
            barmode="group", template=TEMPLATE, height=max(400, len(merged) * 28),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=f"Amount ({unit})", margin=dict(l=160, t=20, b=20),
        )
        st.plotly_chart(fig_doc, width='stretch')
    st.markdown("---")

    # ── Spend by Activity Type (donut) ──
    st.subheader("🍩 Actual Spend by Activity Type")
    col1, col2 = st.columns([1, 1])
    with col1:
        if not ae.empty:
            act_type = ae.groupby("Activity")["Amount_FCFA"].sum().reset_index()
            act_type["Amount"] = act_type["Amount_FCFA"] * mul
            fig_donut = px.pie(
                act_type, names="Activity", values="Amount",
                hole=0.5, template=TEMPLATE, height=380,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_donut.update_traces(textposition="outside", textinfo="percent+label")
            fig_donut.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True, margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig_donut, width='stretch')

    with col2:
        # Spend by Responsible MR
        if not ae.empty:
            mr_spend = ae.groupby("Responsible")["Amount_FCFA"].sum().reset_index()
            mr_spend["Amount"] = mr_spend["Amount_FCFA"] * mul
            mr_spend = mr_spend.sort_values("Amount", ascending=False)
            fig_mr = px.bar(
                mr_spend, x="Responsible", y="Amount",
                template=TEMPLATE, height=380, color="Amount",
                color_continuous_scale="Blues",
                labels={"Amount": f"Amount ({unit})", "Responsible": "MR / CM"},
            )
            fig_mr.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=40), xaxis_tickangle=-30, showlegend=False,
            )
            st.plotly_chart(fig_mr, width='stretch')

    st.markdown("---")

    # ── Data table ──
    st.subheader("📋 Doctor Spend Detail")
    if not ae.empty and not act_plan.empty:
        display = ae.copy()
        display["Planned_FCFA"] = display["Doctor"].apply(
            lambda d: plan_agg[plan_agg["Doctor"] == d]["Planned_FCFA"].sum() if not plan_agg.empty else 0
        )
        display["Planned"] = display["Planned_FCFA"].apply(
            lambda v: fmt_currency(v * mul, unit)
        )
        display["Actual"] = display["Amount_FCFA"].apply(
            lambda v: fmt_currency(v * mul, unit)
        )
        show_cols = {
            "Doctor": "Doctor", "Hospital": "Hospital",
            "Speciality": "Speciality", "Activity": "Activity",
            "Products": "Products", "Planned": f"Planned ({unit})",
            "Actual": f"Actual ({unit})", "Responsible": "MR",
        }
        st.dataframe(
            display.rename(columns=show_cols)[[v for v in show_cols.values()]],
            width='stretch', hide_index=True,
        )
    elif not ae.empty:
        st.dataframe(ae, width='stretch', hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — MR PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def render_tab3(monthly_data, expense_data, visit_data, tour_plan_data, currency):
    delegates = monthly_data["delegates"]
    ae = expense_data["activity_exp"]
    visits = visit_data

    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    if delegates.empty:
        st.info("Upload Monthly Reports file to see MR performance.")
        return

    # ── Per-MR KPI cards row ──
    st.subheader("👥 MR Individual Performance")

    # Spend per MR from activity expense
    mr_spend_map = {}
    if not ae.empty:
        for _, row in ae.iterrows():
            for mr in delegates["Delegate"].tolist():
                if any(part.upper() in str(row["Responsible"]).upper()
                       for part in mr.split()):
                    mr_spend_map[mr] = mr_spend_map.get(mr, 0) + row["Amount_FCFA"]

    # Visit tracker count per MR
    visit_count_map = {}
    if not visits.empty:
        for mr in delegates["Delegate"].tolist():
            # fuzzy match MR name to visit tracker sheet names
            matched = [v for v in visits["MR"].unique()
                       if any(p.upper() in v.upper() or v.upper() in p.upper()
                              for p in mr.split())]
            if matched:
                visit_count_map[mr] = visits[visits["MR"].isin(matched)].shape[0]

    for _, row in delegates.iterrows():
        mr = row["Delegate"]
        spend = mr_spend_map.get(mr, 0)
        vcount = visit_count_map.get(mr, "N/A")
        st.markdown(f"**{mr}** — {row['Territory']}")
        kpi_row([
            {"label": "Total Calls",     "value": f"{int(row['TotalCalls'])}",
             "color": CLR_BLUE},
            {"label": "Prescriber Calls","value": f"{int(row['Prescriber'])}",
             "color": CLR_TEAL},
            {"label": "Drs Converted",   "value": f"{int(row['DrsConverted'])}",
             "color": CLR_GREEN},
            {"label": "Days Worked",     "value": f"{int(row['DaysWorked'])}/{int(row['DaysTarget'])}",
             "color": CLR_ORANGE},
            {"label": "Spend",           "value": fmt_currency(spend * mul, unit),
             "color": CLR_PURPLE},
        ])
        st.markdown("")

    st.markdown("---")

    # ── Reported vs Verified Visits ──
    st.subheader("📊 Reported vs Verified Visits per MR")
    if not visits.empty:
        reported = delegates[["Delegate", "TotalCalls"]].copy()
        reported.columns = ["MR_Report", "Reported"]

        visit_agg = []
        for _, d_row in delegates.iterrows():
            mr = d_row["Delegate"]
            cnt = visit_count_map.get(mr, 0)
            visit_agg.append({"MR_Report": mr, "Verified": cnt})
        verified_df = pd.DataFrame(visit_agg)

        comparison = reported.merge(verified_df, on="MR_Report")
        fig_cmp = go.Figure()
        fig_cmp.add_bar(name="Reported (Self)", x=comparison["MR_Report"],
                        y=comparison["Reported"], marker_color=CLR_ORANGE)
        fig_cmp.add_bar(name="Verified (Tracker)", x=comparison["MR_Report"],
                        y=comparison["Verified"], marker_color=CLR_TEAL)
        fig_cmp.update_layout(
            barmode="group", template=TEMPLATE, height=360,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-15, margin=dict(t=20, b=60),
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_cmp, width='stretch')
    else:
        st.info("Upload Visit Tracker to see verified vs reported calls.")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # ── Spend per MR bar ──
    with col1:
        st.subheader("💸 Total Spend per MR")
        spend_df = pd.DataFrame([
            {"MR": mr, "Spend": amt * mul}
            for mr, amt in mr_spend_map.items()
        ])
        if not spend_df.empty:
            fig_sp = px.bar(spend_df, x="MR", y="Spend", template=TEMPLATE,
                            color="Spend", color_continuous_scale="Viridis",
                            labels={"Spend": f"({unit})"}, height=340)
            fig_sp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20,
            )
            st.plotly_chart(fig_sp, width='stretch')
        else:
            st.info("No MR spend data available.")

    # ── Drs Converted per MR ──
    with col2:
        st.subheader("�� Doctors Converted per MR")
        conv = delegates[["Delegate", "DrsConverted"]].sort_values(
            "DrsConverted", ascending=False)
        fig_conv = px.bar(conv, x="Delegate", y="DrsConverted",
                          template=TEMPLATE, height=340,
                          color="DrsConverted",
                          color_continuous_scale="Teal",
                          labels={"DrsConverted": "Converted", "Delegate": "MR"})
        fig_conv.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20,
        )
        st.plotly_chart(fig_conv, width='stretch')

    st.markdown("---")

    # ── Summary table ──
    st.subheader("📋 MR Summary Table")
    summary = delegates.copy()
    summary["Spend_FCFA"] = summary["Delegate"].map(
        lambda m: mr_spend_map.get(m, 0))
    summary["Verified_Visits"] = summary["Delegate"].map(
        lambda m: visit_count_map.get(m, 0))
    summary["Spend"] = summary["Spend_FCFA"].apply(
        lambda v: fmt_currency(v * mul, unit))
    cols_show = [
        "Delegate", "Territory", "TotalCalls", "Prescriber",
        "DrsConverted", "DaysWorked", "Verified_Visits", "Spend",
    ]
    rename_map = {
        "Delegate": "MR", "TotalCalls": "Total Calls",
        "Prescriber": "Prescriber Calls", "DrsConverted": "Drs Converted",
        "DaysWorked": "Days Worked", "Verified_Visits": "Verified Visits",
        "Spend": f"Spend ({unit})",
    }
    st.dataframe(
        summary[cols_show].rename(columns=rename_map),
        width='stretch', hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — PERFORMANCE OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

def render_tab1(sales_data, proj_data, copy_data, currency):
    feb = sales_data["feb"]
    jan = sales_data["jan"]
    proj = proj_data["projection"]
    prod_perf = copy_data["product_perf"]

    # KPI cards
    total_feb_eur = feb["TOTAL_VALUE_EUR"].sum()
    total_target_eur = proj["Target_Value_EUR"].sum()
    ach_pct = (total_feb_eur / total_target_eur * 100) if total_target_eur else 0
    color_ach = CLR_GREEN if ach_pct >= 100 else CLR_RED
    mul = 1 if currency == "EUR" else FCFA_TO_EUR
    unit = currency

    kpi_row([
        {"label": "Total Feb Sales",
         "value": fmt_currency(total_feb_eur * (1 if currency=="EUR" else FCFA_TO_EUR), unit),
         "color": CLR_BLUE},
        {"label": "Feb Target",
         "value": fmt_currency(total_target_eur * (1 if currency=="EUR" else FCFA_TO_EUR), unit),
         "color": CLR_ORANGE},
        {"label": "Achievement %",
         "value": f"{ach_pct:.1f}%",
         "delta": f"+{ach_pct-100:.1f}%" if ach_pct >= 100 else f"{ach_pct-100:.1f}%",
         "color": color_ach},
    ])
    st.markdown("---")

    # Target vs Achieved grouped bar
    st.subheader("🎯 Target vs Achieved Units")
    if not prod_perf.empty:
        pp = prod_perf.copy()
        fig_ta = go.Figure()
        fig_ta.add_bar(name="Target Units", x=pp["Product"], y=pp["Target_Units"],
                       marker_color=CLR_ORANGE,
                       text=pp["Target_Units"].astype(int), textposition="outside")
        fig_ta.add_bar(name="Achieved Units", x=pp["Product"], y=pp["Achieved_Units"],
                       marker_color=[CLR_GREEN if a >= t else CLR_RED
                                     for a, t in zip(pp["Achieved_Units"], pp["Target_Units"])],
                       text=pp["Achieved_Units"].astype(int), textposition="outside")
        fig_ta.update_layout(barmode="group", template=TEMPLATE, height=380,
                             plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                             legend=dict(orientation="h", y=1.12),
                             margin=dict(t=40, b=60), xaxis_tickangle=-25)
        st.plotly_chart(fig_ta, width='stretch')
    else:
        st.info("Upload 'Copy of Report' file to see this chart.")

    st.markdown("---")

    # Jan vs Feb line chart per product
    st.subheader("📈 Jan → Feb Sales Trend (Units per Product)")
    if not jan.empty and not feb.empty:
        jan_s = jan[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Jan"})
        feb_s = feb[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Feb"})
        trend = jan_s.merge(feb_s, on="Product", how="outer").fillna(0)
        trend_long = trend.melt(id_vars="Product", var_name="Month", value_name="Units")
        fig_trend = px.line(trend_long, x="Month", y="Units", color="Product",
                            markers=True, template=TEMPLATE, height=400)
        fig_trend.update_traces(line_width=2.5)
        fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(t=20, b=20))
        st.plotly_chart(fig_trend, width='stretch')

        # Comparison Line Graph
        st.subheader("📊 Jan vs Feb Sales Comparison (Units)")
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatter(name="Jan", x=trend["Product"], y=trend["Jan"],
                                     mode='lines+markers', line=dict(color=CLR_BLUE, width=2)))
        fig_cmp.add_trace(go.Scatter(name="Feb", x=trend["Product"], y=trend["Feb"],
                                     mode='lines+markers', line=dict(color=CLR_TEAL, width=2)))
        fig_cmp.update_layout(template=TEMPLATE, height=360,
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=20, b=60), xaxis_tickangle=-25,
                              legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_cmp, width='stretch')

    st.markdown("---")

    # Distributor 2x2 subplots with MoM Growth
    st.subheader("🏭 Sales by Distributor (Units) with MoM Growth")
    if not feb.empty and not jan.empty:
        fig_dist = make_subplots(rows=2, cols=2, subplot_titles=DISTRIBUTORS,
                                 vertical_spacing=0.25, horizontal_spacing=0.10)
        positions = [(1,1),(1,2),(2,1),(2,2)]
        for (r, c), dist in zip(positions, DISTRIBUTORS):
            col_key = f"{dist}_SALES"
            if col_key not in feb.columns or col_key not in jan.columns:
                continue

            # Merge Jan and Feb for this distributor
            d_jan = jan[["Product", col_key]].rename(columns={col_key: "Jan_Sales"})
            d_feb = feb[["Product", col_key]].rename(columns={col_key: "Feb_Sales"})
            sub = pd.merge(d_feb, d_jan, on="Product", how="left").fillna(0)

            # Filter where there is at least some sale
            sub = sub[(sub["Feb_Sales"] > 0) | (sub["Jan_Sales"] > 0)].copy()
            sub = sub.sort_values("Feb_Sales", ascending=True)

            # Calculate MoM growth percentage
            sub["MoM_Text"] = sub.apply(
                lambda row: f"+{((row['Feb_Sales'] - row['Jan_Sales'])/row['Jan_Sales']*100):.0f}%" if row['Jan_Sales'] > 0 and row['Feb_Sales'] > row['Jan_Sales'] else (
                            f"{((row['Feb_Sales'] - row['Jan_Sales'])/row['Jan_Sales']*100):.0f}%" if row['Jan_Sales'] > 0 else "New"),
                axis=1
            )

            # Create text to display value and MoM
            sub["Display_Text"] = sub["Feb_Sales"].astype(int).astype(str) + " (" + sub["MoM_Text"] + ")"

            fig_dist.add_trace(go.Bar(
                name=dist, x=sub["Feb_Sales"], y=sub["Product"], orientation="h",
                marker_color=DIST_COLORS[dist],
                text=sub["Display_Text"], textposition="outside",
                showlegend=False,
            ), row=r, col=c)
        fig_dist.update_layout(template=TEMPLATE, height=700,
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=50, b=20))
        st.plotly_chart(fig_dist, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — DOCTOR SPEND
# ─────────────────────────────────────────────────────────────────────────────

def render_tab2(proj_data, expense_data, copy_data, currency):
    act_plan = proj_data["activity_plan"]
    ae = expense_data["activity_exp"]
    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    total_planned = act_plan["Amount_FCFA"].sum()
    total_actual  = ae["Amount_FCFA"].sum()
    gap = total_planned - total_actual

    kpi_row([
        {"label": "Total Planned Spend",
         "value": fmt_currency(total_planned * mul, unit), "color": CLR_ORANGE},
        {"label": "Total Actual Spend",
         "value": fmt_currency(total_actual * mul, unit), "color": CLR_BLUE},
        {"label": "Gap (Planned − Actual)",
         "value": fmt_currency(abs(gap) * mul, unit),
         "delta": "Surplus" if gap >= 0 else "Over-spend",
         "color": CLR_GREEN if gap >= 0 else CLR_RED},
    ])
    st.markdown("---")

    # Planned vs Actual per doctor
    st.subheader("👨‍⚕️ Planned vs Actual Spend per Doctor")
    plan_agg = act_plan.groupby("Doctor")["Amount_FCFA"].sum().reset_index()
    plan_agg.columns = ["Doctor", "Planned_FCFA"]
    act_agg  = ae.groupby("Doctor")["Amount_FCFA"].sum().reset_index()
    act_agg.columns = ["Doctor", "Actual_FCFA"]
    merged = plan_agg.merge(act_agg[["Doctor","Actual_FCFA"]], on="Doctor", how="outer").fillna(0)
    merged = merged[(merged["Planned_FCFA"]>0)|(merged["Actual_FCFA"]>0)]
    merged = merged.sort_values("Planned_FCFA", ascending=True)

    if not merged.empty:
        fig_doc = go.Figure()
        fig_doc.add_bar(name="Planned", x=merged["Planned_FCFA"]*mul,
                        y=merged["Doctor"], orientation="h", marker_color=CLR_ORANGE)
        fig_doc.add_bar(name="Actual",  x=merged["Actual_FCFA"]*mul,
                        y=merged["Doctor"], orientation="h", marker_color=CLR_BLUE)
        fig_doc.update_layout(barmode="group", template=TEMPLATE,
                              height=max(400, len(merged)*28),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              xaxis_title=f"Amount ({unit})",
                              margin=dict(l=180, t=20, b=20),
                              legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig_doc, width='stretch')
    st.markdown("---")

    # Spend by Activity Type (donut) + by MR
    st.subheader("🍩 Spend Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**By Activity Type**")
        if not ae.empty:
            act_type = ae.groupby("Activity")["Amount_FCFA"].sum().reset_index()
            act_type["Amount"] = act_type["Amount_FCFA"] * mul
            fig_donut = px.pie(act_type, names="Activity", values="Amount",
                               hole=0.52, template=TEMPLATE, height=360,
                               color_discrete_sequence=px.colors.qualitative.Bold)
            fig_donut.update_traces(textposition="outside", textinfo="percent+label")
            fig_donut.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig_donut, width='stretch')
    with col2:
        st.markdown("**By Responsible MR**")
        if not ae.empty:
            mr_spend = ae.groupby("Responsible")["Amount_FCFA"].sum().reset_index()
            mr_spend["Amount"] = mr_spend["Amount_FCFA"] * mul
            mr_spend = mr_spend.sort_values("Amount", ascending=False)
            fig_mr = px.bar(mr_spend, x="Responsible", y="Amount",
                            template=TEMPLATE, height=360,
                            color="Amount", color_continuous_scale="Blues",
                            labels={"Amount": f"({unit})", "Responsible": "MR / CM"})
            fig_mr.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(t=20, b=60), xaxis_tickangle=-30,
                                 showlegend=False)
            st.plotly_chart(fig_mr, width='stretch')
    st.markdown("---")

    # Data table
    st.subheader("📋 Doctor Spend Detail")
    if not ae.empty:
        display = ae.copy()
        display["Planned_FCFA"] = display["Doctor"].apply(
            lambda d: plan_agg.loc[plan_agg["Doctor"] == d, "Planned_FCFA"].sum() if not plan_agg.empty else 0
        )
        display["Planned"] = display["Planned_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
        display["Actual"]  = display["Amount_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
        st.dataframe(
            display[["Doctor","Hospital","Speciality","Activity",
                      "Products","Planned","Actual","Responsible"]].rename(columns={
                "Planned": f"Planned ({unit})", "Actual": f"Actual ({unit})",
                "Responsible": "MR"}),
            width='stretch', hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — MR PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def render_tab3(monthly_data, expense_data, visit_data, currency):
    delegates = monthly_data["delegates"]
    ae = expense_data["activity_exp"]
    visits = visit_data
    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    if delegates.empty:
        st.info("Upload Monthly Reports file to see MR performance.")
        return

    # Exclude CM (MR_006) and ARRA BEHOU (AGT_001) — field MRs only
    field_delegates = delegates[
        ~delegates["MR_ID"].isin(_NON_MR_IDS)
    ].copy()

    if field_delegates.empty:
        st.info("No field MR data found after filtering.")
        return

    # Build spend per MR_ID from normalized MR_IDs column
    # Joint entries ("MR_006,MR_002") are split and the amount is split equally
    mr_spend_map = {}  # MR_ID -> FCFA
    if not ae.empty and "MR_IDs" in ae.columns:
        for _, row in ae.iterrows():
            mr_ids = [i.strip() for i in str(row["MR_IDs"]).split(",") if i.strip() and i.strip() != "UNKNOWN"]
            if not mr_ids:
                continue
            split_amount = row["Amount_FCFA"] / len(mr_ids)
            for mr_id in mr_ids:
                mr_spend_map[mr_id] = mr_spend_map.get(mr_id, 0) + split_amount

    # Build visit count per MR_ID from normalized visit tracker
    visit_count_map = {}  # MR_ID -> count
    if not visits.empty and "MR_ID" in visits.columns:
        feb_visits = visits[visits["Month"] == "Feb"] if "Month" in visits.columns else visits
        vc = feb_visits.groupby("MR_ID").size().to_dict()
        visit_count_map = vc

    # Per-MR KPI rows
    st.subheader("👥 MR Individual KPIs")
    for _, row in field_delegates.iterrows():
        mr_id = row["MR_ID"]
        display = mr_display_name(mr_id) if mr_id in MR_CANONICAL else row["Delegate"]
        spend = mr_spend_map.get(mr_id, 0)
        territory = territory_display_name(normalize_territory(row["Territory"]))
        st.markdown(f"##### {display} — *{territory}*")
        kpi_row([
            {"label": "Total Calls",      "value": f"{int(row['TotalCalls'])}",   "color": CLR_BLUE},
            {"label": "Prescriber Calls", "value": f"{int(row['Prescriber'])}",   "color": CLR_TEAL},
            {"label": "Drs Converted",    "value": f"{int(row['DrsConverted'])}", "color": CLR_GREEN},
            {"label": "Days Worked",
             "value": f"{int(row['DaysWorked'])}/{int(row['DaysTarget'])}",
             "color": CLR_ORANGE},
            {"label": f"Spend ({unit})",  "value": fmt_currency(spend*mul, unit), "color": CLR_PURPLE},
        ])
        st.markdown("")
    st.markdown("---")

    # Reported vs Verified
    st.subheader("📊 Reported vs Verified Visits per MR")
    if not visits.empty:
        comparison = pd.DataFrame([
            {"MR": mr_display_name(row["MR_ID"]) if row["MR_ID"] in MR_CANONICAL else row["Delegate"],
             "Reported (Self)": int(row["TotalCalls"]),
             "Verified (Tracker)": visit_count_map.get(row["MR_ID"], 0)}
            for _, row in field_delegates.iterrows()
        ])
        fig_cmp = go.Figure()
        fig_cmp.add_bar(name="Reported (Self)", x=comparison["MR"],
                        y=comparison["Reported (Self)"], marker_color=CLR_ORANGE)
        fig_cmp.add_bar(name="Verified (Tracker)", x=comparison["MR"],
                        y=comparison["Verified (Tracker)"], marker_color=CLR_TEAL)
        fig_cmp.update_layout(barmode="group", template=TEMPLATE, height=360,
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              xaxis_tickangle=-15, margin=dict(t=20, b=60),
                              legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_cmp, width='stretch')
    else:
        st.info("Upload Visit Tracker to see verified calls.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💸 Total Spend per MR")
        spend_df = pd.DataFrame([
            {"MR": mr_display_name(k), "Spend": v*mul}
            for k, v in mr_spend_map.items()
            if k not in _NON_MR_IDS
        ])
        if not spend_df.empty:
            fig_sp = px.bar(spend_df, x="MR", y="Spend", template=TEMPLATE,
                            color="Spend", color_continuous_scale="Viridis", height=340,
                            labels={"Spend": f"({unit})"})
            fig_sp.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20)
            st.plotly_chart(fig_sp, width='stretch')
        else:
            st.info("No MR spend data.")

    with col2:
        st.subheader("🩺 Doctors Converted per MR")
        conv = field_delegates[["Delegate","DrsConverted"]].copy()
        conv["MR"] = field_delegates["MR_ID"].apply(
            lambda i: mr_display_name(i) if i in MR_CANONICAL else i)
        conv = conv.sort_values("DrsConverted", ascending=False)
        fig_conv = px.bar(conv, x="MR", y="DrsConverted", template=TEMPLATE, height=340,
                          color="DrsConverted", color_continuous_scale="Teal",
                          labels={"DrsConverted": "Converted", "MR": "MR"})
        fig_conv.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20)
        st.plotly_chart(fig_conv, width='stretch')
    st.markdown("---")

    # Summary table
    st.subheader("📋 MR Summary Table")
    summary = field_delegates.copy()
    summary["Display"] = summary["MR_ID"].apply(
        lambda i: mr_display_name(i) if i in MR_CANONICAL else summary.loc[summary["MR_ID"]==i, "Delegate"].values[0]
    )
    summary["Spend"] = summary["MR_ID"].map(
        lambda i: fmt_currency(mr_spend_map.get(i, 0)*mul, unit))
    summary["Verified Visits"] = summary["MR_ID"].map(
        lambda i: visit_count_map.get(i, 0))
    st.dataframe(
        summary[["Display","Territory","TotalCalls","Prescriber",
                 "DrsConverted","DaysWorked","Verified Visits","Spend"]].rename(columns={
            "Display":"MR", "TotalCalls":"Total Calls", "Prescriber":"Prescriber Calls",
            "DrsConverted":"Drs Converted", "DaysWorked":"Days Worked",
            "Spend": f"Spend ({unit})"}),
        width='stretch', hide_index=True)

    st.markdown("---")

    # ── Tour Program Coverage ──
    st.subheader("🗺️ Tour Program Coverage (Planned vs Actual Area)")
    if tour_plan_data is not None and not tour_plan_data.empty:
        # Group by MR to show coverage %
        tp_mr = tour_plan_data.groupby('MR').agg(
            Total_Plans=('Date', 'count'),
            Covered_Plans=('Covered', 'sum')
        ).reset_index()
        tp_mr['Coverage_%'] = (tp_mr['Covered_Plans'] / tp_mr['Total_Plans'] * 100).round(1)
        tp_mr['MR_Display'] = tp_mr['MR'].apply(lambda i: mr_display_name(i) if i in MR_CANONICAL else i)

        col_tp1, col_tp2 = st.columns([1, 2])
        with col_tp1:
            st.dataframe(tp_mr[['MR_Display', 'Total_Plans', 'Covered_Plans', 'Coverage_%']].rename(
                columns={'MR_Display': 'MR', 'Total_Plans': 'Total Days Planned', 'Covered_Plans': 'Days Covered Area', 'Coverage_%': 'Coverage %'}
            ), width='stretch', hide_index=True)

        with col_tp2:
            fig_tp = px.bar(tp_mr, x="MR_Display", y="Coverage_%", template=TEMPLATE, height=340,
                            color="Coverage_%", color_continuous_scale="Teal",
                            labels={"Coverage_%": "Coverage %", "MR_Display": "MR"})
            fig_tp.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20)
            st.plotly_chart(fig_tp, width='stretch')

        st.markdown("**Detail: Tour Plan Coverage**")
        tp_detail = tour_plan_data.copy()
        tp_detail['MR'] = tp_detail['MR'].apply(lambda i: mr_display_name(i) if i in MR_CANONICAL else i)
        tp_detail['Date'] = pd.to_datetime(tp_detail['Date']).dt.strftime('%Y-%m-%d')
        st.dataframe(tp_detail.rename(columns={'Planned_Area': 'Planned Area', 'Actual_Area': 'Actual Area', 'Joint_Working': 'Joint Working'}), width='stretch', hide_index=True)
    else:
        st.info("Upload 'Tour Plan' file to see area coverage metrics.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — CM SPEND
# ─────────────────────────────────────────────────────────────────────────────

def render_tab4(expense_data, monthly_data, currency):
    ae = expense_data["activity_exp"]
    oe = expense_data["other_exp"]
    mr = expense_data["money_received"]
    total_recv  = expense_data["total_received_fcfa"]
    total_spent = expense_data["total_spent_fcfa"]
    balance     = expense_data["balance_fcfa"]
    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    util_pct = (total_spent / total_recv * 100) if total_recv else 0

    kpi_row([
        {"label": "Budget Received",
         "value": fmt_currency(total_recv * mul, unit), "color": CLR_TEAL},
        {"label": "Total Spent",
         "value": fmt_currency(total_spent * mul, unit), "color": CLR_ORANGE},
        {"label": "Balance",
         "value": fmt_currency(balance * mul, unit),
         "color": CLR_GREEN if balance >= 0 else CLR_RED},
        {"label": "Utilisation %",
         "value": f"{util_pct:.1f}%",
         "color": CLR_GREEN if util_pct <= 100 else CLR_RED},
    ])
    st.markdown("---")

    # Budget Flow bar
    st.subheader("💰 Budget Flow")
    col1, col2 = st.columns([1, 2])
    with col1:
        flow_df = pd.DataFrame({
            "Category": ["Received", "Spent", "Balance"],
            "Amount":   [total_recv * mul, total_spent * mul, balance * mul],
            "Color":    [CLR_TEAL, CLR_ORANGE, CLR_GREEN if balance >= 0 else CLR_RED],
        })
        fig_flow = go.Figure(go.Bar(
            x=flow_df["Category"], y=flow_df["Amount"],
            marker_color=flow_df["Color"],
            text=[fmt_currency(v, unit) for v in flow_df["Amount"]],
            textposition="outside",
        ))
        fig_flow.update_layout(template=TEMPLATE, height=340,
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=20, b=20), yaxis_title=f"Amount ({unit})")
        st.plotly_chart(fig_flow, width='stretch')

    # Cumulative Spend Line Chart
    with col2:
        st.markdown("**Cumulative Spend Over Feb**")
        if not ae.empty or not mr.empty:
            # Use activity expense dates if available; else just show total
            # Build spend timeline from money_received (outflows = total_spent)
            # and activity expense (no date col) — approximate from mr dates
            if not mr.empty and "Date" in mr.columns:
                mr_sorted = mr.sort_values("Date").copy()
                mr_sorted["Cumulative_FCFA"] = mr_sorted["Amount_FCFA"].cumsum()
                mr_sorted["Cumulative"] = mr_sorted["Cumulative_FCFA"] * mul
                fig_cum = px.line(mr_sorted, x="Date", y="Cumulative",
                                  markers=True, template=TEMPLATE, height=320,
                                  labels={"Cumulative": f"Cumulative ({unit})", "Date": "Date"})
                fig_cum.update_traces(line_color=CLR_TEAL, line_width=2.5)
                fig_cum.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                                      paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20))
                st.plotly_chart(fig_cum, width='stretch')
            else:
                st.info("No date-stamped data available for cumulative chart.")
        else:
            st.info("Upload Expense file to see spend timeline.")
    st.markdown("---")

    # Stacked bar: CM vs MR vs Agent vs Other (using normalized MR_IDs)
    st.subheader("📊 Spend Breakdown by Category")
    if not ae.empty and "MR_IDs" in ae.columns:
        # To avoid duplication for joint entries (e.g. JITENDRA/CLEMANCE), explode the MR_IDs
        # and distribute the Amount_FCFA evenly
        ae_exploded = ae.copy()
        ae_exploded['MR_ID_List'] = ae_exploded['MR_IDs'].apply(lambda x: [i.strip() for i in str(x).split(",") if i.strip()])
        ae_exploded['Num_MRs'] = ae_exploded['MR_ID_List'].apply(lambda x: max(1, len(x)))
        ae_exploded = ae_exploded.explode('MR_ID_List')
        ae_exploded['Amount_FCFA'] = ae_exploded['Amount_FCFA'] / ae_exploded['Num_MRs']

        def classify_spend(mr_id):
            if mr_id == "MR_006":
                return "CM Direct"
            if mr_id == "AGT_001":
                return "Agent (ARRA BEHOU)"
            if mr_id not in ("UNKNOWN",):
                return "MR Attributed"
            return "Other"

        ae_exploded["SpendType"] = ae_exploded["MR_ID_List"].apply(classify_spend)
        spend_by_type = ae_exploded.groupby("SpendType")["Amount_FCFA"].sum().reset_index()
    else:
        spend_by_type = pd.DataFrame(columns=["SpendType","Amount_FCFA"])

    other_total = oe["Amount_FCFA"].sum() if not oe.empty else 0
    spend_by_type = pd.concat([
        spend_by_type,
        pd.DataFrame([{"SpendType": "Other Expenses", "Amount_FCFA": other_total}])
    ], ignore_index=True)
    spend_by_type["Amount"] = spend_by_type["Amount_FCFA"] * mul

    colors_map = {"CM Direct": CLR_ORANGE, "MR Attributed": CLR_TEAL,
                  "Agent (ARRA BEHOU)": CLR_YELLOW, "Other Expenses": CLR_PURPLE, "Other": CLR_BLUE}
    fig_stk = go.Figure()
    for _, row in spend_by_type.iterrows():
        if row["Amount"] == 0:
            continue
        fig_stk.add_bar(name=row["SpendType"], x=["Feb 2026"],
                        y=[row["Amount"]],
                        marker_color=colors_map.get(row["SpendType"], CLR_BLUE),
                        text=[fmt_currency(row["Amount"], unit)],
                        textposition="inside")
    fig_stk.update_layout(barmode="stack", template=TEMPLATE, height=360,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           yaxis_title=f"Amount ({unit})",
                           legend=dict(orientation="h", y=1.1),
                           margin=dict(t=30, b=20))
    st.plotly_chart(fig_stk, width='stretch')
    st.markdown("---")

    # CM-level activity table
    st.subheader("📋 CM Direct Activities")
    if not ae.empty and "MR_IDs" in ae.columns:
        cm_df = ae[ae["MR_IDs"].str.contains("MR_006", na=False)].copy()
        if not cm_df.empty:
            cm_df["Amount"] = cm_df["Amount_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
            st.dataframe(
                cm_df[["Doctor","Hospital","Speciality","Activity","Products","Amount","Responsible"]]
                    .rename(columns={"Amount": f"Amount ({unit})"}),
                width='stretch', hide_index=True)
        else:
            st.info("No CM-direct entries found.")
    st.markdown("---")

    # ── Agent Activities (ARRA BEHOU = AGT_001) ──
    st.subheader("🤝 Agent Activities (ARRA BEHOU)")
    if not ae.empty and "MR_IDs" in ae.columns:
        agent_df = ae[ae["MR_IDs"].str.contains("AGT_001", na=False)].copy()
        if not agent_df.empty:
            agent_df["Amount"] = agent_df["Amount_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
            agent_total = agent_df["Amount_FCFA"].sum()
            st.caption(f"Total Agent Spend: **{fmt_currency(agent_total*mul, unit)}**")
            st.dataframe(
                agent_df[["Doctor","Hospital","Speciality","Activity","Products","Amount"]]
                    .rename(columns={"Amount": f"Amount ({unit})"}),
                width='stretch', hide_index=True)
        else:
            st.info("No agent activity entries found.")
    st.markdown("---")

    # Other Expenses table — full columns as specified
    st.subheader("📋 Other Expenses")
    if not oe.empty:
        oe_display = oe.copy()
        oe_display[f"Amount ({unit})"] = oe_display["Amount_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
        oe_display["Amount EUR"] = oe_display["Amount_EUR"].apply(lambda v: fmt_currency(v, "EUR"))
        st.dataframe(
            oe_display[["Country","Details",f"Amount ({unit})","Amount EUR","Comments","Category"]],
            width='stretch', hide_index=True)
    else:
        st.info("No other expense data.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — VISIT TIMELINE
# ─────────────────────────────────────────────────────────────────────────────

def render_tab5(visit_data):
    if visit_data.empty:
        placeholder_tab("Visit Timeline", "Upload at least one Visit Tracker file to see this tab.")
        return

    visits = visit_data.copy()
    visits["Day"] = visits["Visit_Date"].dt.day

    # ── Controls ──
    ctrl1, ctrl2 = st.columns([1, 2])
    with ctrl1:
        available_months = sorted(visits["Month"].unique()) if "Month" in visits.columns else ["Feb"]
        selected_month = st.selectbox("📅 Month", available_months, index=0)
    with ctrl2:
        mr_list = sorted(visits["MR"].unique().tolist())
        selected_mr = st.selectbox("👤 MR", ["All"] + mr_list)

    month_visits = visits[visits["Month"] == selected_month].copy() if "Month" in visits.columns else visits
    filtered = month_visits if selected_mr == "All" else month_visits[month_visits["MR"] == selected_mr]
    st.markdown("---")

    # ── Daily Visit Line Chart (above heatmap as specified) ──
    st.subheader(f"📈 Daily Visit Count — {selected_month} 2026")
    if not filtered.empty:
        daily = filtered.groupby(["MR", "Visit_Date"]).size().reset_index(name="Count")
        fig_line = px.line(daily, x="Visit_Date", y="Count",
                           color="MR", markers=True, template=TEMPLATE, height=360,
                           labels={"Visit_Date": "Date", "Count": "Visits per Day"})
        fig_line.update_traces(line_width=2.5)
        fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1),
                               xaxis_tickformat="%d %b")
        st.plotly_chart(fig_line, width='stretch')

    # ── Calendar Heatmap ──
    st.subheader(f"📅 Visit Calendar Heatmap — {selected_month} 2026")
    if not filtered.empty:
        hm_data = filtered.groupby(["MR", "Day"]).size().reset_index(name="Visits")
        fig_hm = px.density_heatmap(
            hm_data, x="Day", y="MR", z="Visits",
            color_continuous_scale="Teal", template=TEMPLATE, height=360,
            labels={"Day": "Day of Month", "MR": "MR"},
            title=f"Visit Density — {selected_month} 2026",
        )
        fig_hm.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                             margin=dict(t=50, b=20))
        st.plotly_chart(fig_hm, width='stretch')
    st.markdown("---")

    # ── Doctor Repeat (> 2 times) ──
    st.subheader("🔄 Doctor Repeat Visits (> 2 times)")
    if not month_visits.empty:
        # Calculate repetitions across the month independent of the MR selected filter above
        repeat_visits = month_visits.groupby(["Doctor", "Clinic", "Speciality"]).size().reset_index(name="Visits")
        repeat_visits = repeat_visits[repeat_visits["Visits"] > 2].sort_values("Visits", ascending=False)

        if not repeat_visits.empty:
            st.dataframe(repeat_visits.rename(columns={"Visits": "Total Visits"}), width='stretch', hide_index=True)
        else:
            st.info("No doctors were visited more than 2 times this month.")
    else:
        st.info("No visit data available to calculate repeat visits.")

    st.markdown("---")

    # ── Detail Table ──
    st.subheader("📋 Visit Details")
    if not filtered.empty:
        show = filtered[["MR","Doctor","Speciality","Clinic","Visit_Date"]].copy()
        show["Visit_Date"] = show["Visit_Date"].dt.strftime("%d-%b-%Y")
        show = show.sort_values(["MR","Visit_Date"])
        st.dataframe(show.rename(columns={"Visit_Date": "Visit Date"}),
                     width='stretch', hide_index=True)
    else:
        st.info(f"No visits found for the selected filter in {selected_month} 2026.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — INJECTABLE COMMISSION (PLACEHOLDER)
# ─────────────────────────────────────────────────────────────────────────────

def render_tab6():
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;
                    min-height:480px;">
            <div style="background:linear-gradient(135deg,#12192a,#1a2640);
                        border:1px solid #2a4060;border-radius:20px;
                        padding:56px 72px;text-align:center;max-width:560px;
                        box-shadow: 0 8px 32px rgba(76,159,255,0.12);">
                <div style="font-size:64px;margin-bottom:20px;">💉</div>
                <h2 style="color:#4C9FFF;font-size:28px;margin:0 0 12px 0;">
                    Injectable Commission ROI
                </h2>
                <div style="display:inline-block;background:#1e3050;
                            border-radius:20px;padding:6px 18px;
                            color:#B57BFF;font-size:13px;font-weight:600;
                            letter-spacing:1px;margin-bottom:20px;">
                    COMING SOON
                </div>
                <p style="color:#8899aa;font-size:15px;line-height:1.7;margin:0;">
                    This tab will display injectable product commission ROI analysis —
                    including 12-month commission trends per clinic, product-level
                    profitability, and MR attribution breakdowns.<br><br>
                    Upload <strong style="color:#cce0ff;">INJECTABLE_COMISSION_TILL_feb_2026_IVC.xlsx</strong>
                    when ready to activate.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="IVC Pharma Executive Dashboard",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Global dark CSS + typography
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: #0d1521; }
        section[data-testid="stSidebar"] { background: #111d2e !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; background: #111d2e; border-radius: 10px; padding: 6px; }
        .stTabs [data-baseweb="tab"] {
            background: transparent; border-radius: 8px; color: #8899aa;
            padding: 8px 18px; font-size: 13px; font-weight: 500; border: none;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1a3a6e, #1e4080) !important;
            color: #4C9FFF !important; font-weight: 700;
        }
        div[data-testid="metric-container"] { background: #1a2535; border-radius: 10px; }
        .stDataFrame { border-radius: 10px; overflow: hidden; }
        h1, h2, h3 { color: #e8f0ff; }
        h4, h5 { color: #c0d0ee; }
        .stSelectbox label, .stFileUploader label { color: #8899aa !important; font-size: 12px !important; }
        hr { border-color: #1e3050; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Header ──
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:16px;
                    padding:20px 0 8px 0;border-bottom:1px solid #1e3050;margin-bottom:20px;">
            <div style="font-size:36px;">💊</div>
            <div>
                <h1 style="margin:0;font-size:24px;font-weight:700;color:#e8f0ff;">
                    IVC Pharma Executive Dashboard
                </h1>
                <p style="margin:0;color:#8899aa;font-size:13px;">
                    Ivory Coast · February 2026 · Local Analytics
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        currency = st.radio("Currency Display", ["FCFA", "EUR"], horizontal=True)
        st.markdown("---")
        st.markdown("### 📁 Upload Files")

        f_sales    = st.file_uploader("Sales File (IVC_SALES…xlsx)",
                                      type=["xlsx"], key="sales")
        f_proj     = st.file_uploader("Projection & Activity Plan (IVC_PROJECTION…xlsx)",
                                      type=["xlsx"], key="proj")
        f_expense  = st.file_uploader("Expense & Activity Sheet (IVC_EXPENSE…xlsx)",
                                      type=["xlsx"], key="expense")
        f_monthly  = st.file_uploader("Monthly Reports (IVC_MONTHLY…xlsx)",
                                      type=["xlsx"], key="monthly")
        f_visits_feb = st.file_uploader("Visit Tracker — Feb (Ivory_coast_visit_tracker…xlsx)",
                                        type=["xlsx"], key="visits_feb")
        f_visits_mar = st.file_uploader("Visit Tracker — Mar (ivc_March-2026.xlsx)",
                                        type=["xlsx"], key="visits_mar")
        f_copy     = st.file_uploader("Copy of Report (Copy_of_report…xlsx)",
                                      type=["xlsx"], key="copy")
        f_tour_plan = st.file_uploader("Tour Plan (IVC TOUR PLAN VS WORKING AREA.xlsx)",
                                       type=["xlsx"], key="tour_plan")

        st.markdown("---")
        st.markdown(
            '<p style="color:#3a5070;font-size:11px;">'
            "All processing is local. No data is sent externally.</p>",
            unsafe_allow_html=True,
        )

    # ── Load Data ──
    sales_data   = load_sales(f_sales.read())     if f_sales    else None
    proj_data    = load_projection(f_proj.read()) if f_proj     else None
    expense_data = load_expense(f_expense.read()) if f_expense  else None
    monthly_data = load_monthly_reports(f_monthly.read()) if f_monthly else None
    copy_data    = load_copy_report(f_copy.read()) if f_copy    else None
    tour_plan_data = load_tour_plan(f_tour_plan.read()) if f_tour_plan else None

    # Build visit tracker from one or both uploaded files
    tracker_inputs = []
    if f_visits_feb:
        tracker_inputs.append((f_visits_feb.read(), "Feb"))
    if f_visits_mar:
        tracker_inputs.append((f_visits_mar.read(), "Mar"))
    visit_data = (
        load_visit_tracker(tracker_inputs) if tracker_inputs
        else pd.DataFrame(columns=["MR_ID","MR","Doctor","Speciality","Clinic","Visit_Date","Month"])
    )

    # Build doctor index for fuzzy normalization (from visit tracker)
    if not visit_data.empty:
        build_doctor_index(visit_data["Doctor"].dropna().tolist())

    # Normalize delegate MR_IDs in monthly report
    if monthly_data and not monthly_data["delegates"].empty:
        monthly_data["delegates"]["MR_ID"] = (
            monthly_data["delegates"]["Delegate"].apply(normalize_mr)
        )

    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Performance Overview",
        "🩺 Doctor Spend",
        "👥 MR Performance",
        "💼 CM Spend",
        "📅 Visit Timeline",
        "💉 Injectable Commission",
    ])

    with tab1:
        if sales_data and proj_data and copy_data:
            render_tab1(sales_data, proj_data, copy_data, currency)
        else:
            missing = []
            if not sales_data:  missing.append("Sales File")
            if not proj_data:   missing.append("Projection File")
            if not copy_data:   missing.append("Copy of Report")
            placeholder_tab(
                "Performance Overview",
                f"Please upload: {', '.join(missing)}")

    with tab2:
        if proj_data and expense_data:
            render_tab2(proj_data, expense_data, copy_data or
                        {"product_perf": pd.DataFrame(), "plan_activities": pd.DataFrame(),
                         "actual_activities": pd.DataFrame()}, currency)
        else:
            placeholder_tab("Doctor Spend",
                            "Upload Projection & Activity Plan + Expense files.")

    with tab3:
        if monthly_data and expense_data:
            render_tab3(monthly_data, expense_data, visit_data, tour_plan_data, currency)
        else:
            placeholder_tab("MR Performance",
                            "Upload Monthly Reports + Expense files.")

    with tab4:
        if expense_data:
            render_tab4(expense_data, monthly_data or
                        {"delegates": pd.DataFrame(), "budget_analysis": pd.DataFrame()},
                        currency)
        else:
            placeholder_tab("CM Spend", "Upload the Expense & Activity Sheet file.")

    with tab5:
        render_tab5(visit_data)

    with tab6:
        render_tab6()


if __name__ == "__main__":
    main()
