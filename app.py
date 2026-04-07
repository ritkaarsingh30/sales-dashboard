"""
IVC Pharma Executive Dashboard — entry point.

All logic has been split into:
  constants.py   — shared constants (colors, FCFA rate, etc.)
  utils.py       — shared UI helpers (kpi_row, fmt_currency, etc.)
  loaders.py     — all @st.cache_data data loaders
  name_map.py    — MR / Doctor / Product normalization
  tabs/
    tab1_performance.py
    tab2_doctor_spend.py
    tab3_mr_performance.py
    tab4_cm_spend.py
    tab5_visit_timeline.py
    tab6_injectable.py
"""

import streamlit as st
import pandas as pd

from name_map import normalize_mr, build_doctor_index
from loaders import (
    load_sales,
    load_projection,
    load_expense,
    load_monthly_reports,
    load_visit_tracker,
    load_copy_report,
    load_tour_plan,
)
from utils import placeholder_tab
from tabs.tab1_performance   import render_tab1
from tabs.tab2_doctor_spend  import render_tab2
from tabs.tab3_mr_performance import render_tab3
from tabs.tab4_cm_spend      import render_tab4
from tabs.tab5_visit_timeline import render_tab5
from tabs.tab6_injectable    import render_tab6


def main():
    st.set_page_config(
        page_title="IVC Pharma Executive Dashboard",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Global styles ──
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

        f_sales      = st.file_uploader("Sales File (IVC_SALES…xlsx)",                        type=["xlsx"], key="sales")
        f_proj       = st.file_uploader("Projection & Activity Plan (IVC_PROJECTION…xlsx)",    type=["xlsx"], key="proj")
        f_expense    = st.file_uploader("Expense & Activity Sheet (IVC_EXPENSE…xlsx)",          type=["xlsx"], key="expense")
        f_monthly    = st.file_uploader("Monthly Reports (IVC_MONTHLY…xlsx)",                  type=["xlsx"], key="monthly")
        f_visits_feb = st.file_uploader("Visit Tracker — Feb (Ivory_coast_visit_tracker…xlsx)", type=["xlsx"], key="visits_feb")
        f_visits_mar = st.file_uploader("Visit Tracker — Mar (IVC MARCH REPORT.xlsx)",
                                        type=["xlsx"], key="visits_mar")
        f_copy       = st.file_uploader("Copy of Report (Copy_of_report…xlsx)",                type=["xlsx"], key="copy")
        f_tour_plan  = st.file_uploader("Tour Plan (IVC TOUR PLAN VS WORKING AREA.xlsx)",      type=["xlsx"], key="tour_plan")

        st.markdown("---")
        st.markdown(
            '<p style="color:#3a5070;font-size:11px;">'
            "All processing is local. No data is sent externally.</p>",
            unsafe_allow_html=True,
        )

    # ── Load Data ──
    sales_data     = load_sales(f_sales.read())           if f_sales      else None
    proj_data      = load_projection(f_proj.read())       if f_proj       else None
    expense_data   = load_expense(f_expense.read())       if f_expense    else None
    monthly_data   = load_monthly_reports(f_monthly.read()) if f_monthly  else None
    copy_data      = load_copy_report(f_copy.read())      if f_copy       else None
    tour_plan_data = load_tour_plan(f_tour_plan.read())   if f_tour_plan  else None

    tracker_inputs = []
    if f_visits_feb:
        tracker_inputs.append((f_visits_feb.read(), "Feb"))
    if f_visits_mar:
        tracker_inputs.append((f_visits_mar.read(), "Mar"))
    visit_data = (
        load_visit_tracker(tracker_inputs) if tracker_inputs
        else pd.DataFrame(columns=["MR_ID","MR","Doctor","Speciality","Clinic","Visit_Date","Month"])
    )

    # Build doctor fuzzy index from visit tracker
    if not visit_data.empty:
        build_doctor_index(visit_data["Doctor"].dropna().tolist())

    # Normalise delegate MR_IDs from monthly report
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
            placeholder_tab("Performance Overview", f"Please upload: {', '.join(missing)}")

    with tab2:
        if proj_data and expense_data:
            render_tab2(proj_data, expense_data, copy_data or {
                "product_perf": pd.DataFrame(),
                "plan_activities": pd.DataFrame(),
                "actual_activities": pd.DataFrame(),
            }, currency)
        else:
            placeholder_tab("Doctor Spend", "Upload Projection & Activity Plan + Expense files.")

    with tab3:
        if monthly_data and expense_data:
            render_tab3(monthly_data, expense_data, visit_data, tour_plan_data, currency)
        else:
            placeholder_tab("MR Performance", "Upload Monthly Reports + Expense files.")

    with tab4:
        if expense_data:
            render_tab4(expense_data, monthly_data or {
                "delegates": pd.DataFrame(),
                "budget_analysis": pd.DataFrame(),
            }, currency)
        else:
            placeholder_tab("CM Spend", "Upload the Expense & Activity Sheet file.")

    with tab5:
        render_tab5(visit_data)

    with tab6:
        render_tab6()


if __name__ == "__main__":
    main()
