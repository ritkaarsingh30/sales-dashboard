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
from tabs.tab_trends         import render_tab_trends


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
        st.markdown("### 📁 Master Files")
        f_sales = st.file_uploader("Sales File (IVC_Sales_Data_2026.xlsx)", type=["xlsx"], key="master_sales")
        f_copy  = st.file_uploader("Copy of Report (IVC_Copy_Of_Report_2026.xlsx)", type=["xlsx"], key="master_copy")
        st.markdown("---")
        st.markdown(
            '<p style="color:#3a5070;font-size:11px;">'
            "All processing is local. No data is sent externally.</p>",
            unsafe_allow_html=True,
        )

    def render_month_dashboard(month: str, prev_month: str = None):
        st.markdown(f"### 📁 Upload {month} Files")
        col1, col2, col3 = st.columns(3)
        with col1:
            f_proj = st.file_uploader(f"Projection & Activity Plan", type=["xlsx"], key=f"proj_{month}")
            f_expense = st.file_uploader(f"Expense & Activity Sheet", type=["xlsx"], key=f"exp_{month}")
        with col2:
            f_monthly = st.file_uploader(f"Monthly Reports", type=["xlsx"], key=f"month_{month}")
            f_visits = st.file_uploader(f"Visit Tracker", type=["xlsx"], key=f"visit_{month}")
        with col3:
            f_tour = st.file_uploader(f"Tour Plan", type=["xlsx"], key=f"tour_{month}")
            
        if not (f_sales and f_copy and f_proj and f_expense and f_monthly and f_visits and f_tour):
            st.warning(f"Please upload all Master files (Sidebar) and Monthly files above to view the {month} dashboard.")
            return None  # Signal: data not ready

        # ── Load Data ──
        current_sheet_sales = f"{month[:3].upper()}-26"
        prev_sheet_sales = f"{prev_month[:3].upper()}-26" if prev_month else None
        
        sales_data     = load_sales(f_sales.getvalue(), current_sheet_sales, prev_sheet_sales)
        proj_data      = load_projection(f_proj.getvalue())
        expense_data   = load_expense(f_expense.getvalue())
        monthly_data   = load_monthly_reports(f_monthly.getvalue())
        copy_data      = load_copy_report(f_copy.getvalue(), month)
        tour_plan_data = load_tour_plan(f_tour.getvalue())
        
        visit_data = load_visit_tracker([(f_visits.getvalue(), month[:3])])

        # Build doctor fuzzy index from visit tracker
        if not visit_data.empty:
            build_doctor_index(visit_data["Doctor"].dropna().tolist())

        # Normalise delegate MR_IDs from monthly report
        if monthly_data and monthly_data["delegates"] is not None and not monthly_data["delegates"].empty:
            monthly_data["delegates"]["MR_ID"] = (
                monthly_data["delegates"]["Delegate"].apply(normalize_mr)
            )

        # ── Missing-sheet sidebar warning ──
        all_missing = (
            proj_data.get("missing_sheets", [])
            + expense_data.get("missing_sheets", [])
            + monthly_data.get("missing_sheets", [])
            + copy_data.get("missing_sheets", [])
        )
        if all_missing:
            with st.sidebar:
                st.markdown("---")
                st.warning(
                    "⚠️ **Missing sheets detected:**\n\n"
                    + "\n".join(f"• `{s}`" for s in all_missing)
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
            render_tab1(sales_data, proj_data, copy_data, currency, month)
        with tab2:
            render_tab2(proj_data, expense_data, copy_data, currency, month)
        with tab3:
            render_tab3(monthly_data, expense_data, visit_data, tour_plan_data, currency, month)
        with tab4:
            render_tab4(expense_data, monthly_data, currency, month)
        with tab5:
            render_tab5(visit_data, month)
        with tab6:
            render_tab6(month)

        # Return loaded data bundle for cross-month trends
        return {
            "monthly": monthly_data,
            "expense": expense_data,
            "proj":    proj_data,
            "visit":   visit_data,
        }

    # Top-level Tabs
    tab_jan, tab_feb, tab_mar, tab_trends = st.tabs(
        ["January", "February", "March", "📈 Month Trends"]
    )

    all_months_data = {}
    all_visits = []

    with tab_jan:
        data = render_month_dashboard("January", prev_month=None)
        if data:
            all_months_data["January"] = data
            if data["visit"] is not None and not data["visit"].empty:
                all_visits.append(data["visit"])
    with tab_feb:
        data = render_month_dashboard("February", prev_month="January")
        if data:
            all_months_data["February"] = data
            if data["visit"] is not None and not data["visit"].empty:
                all_visits.append(data["visit"])
    with tab_mar:
        data = render_month_dashboard("March", prev_month="February")
        if data:
            all_months_data["March"] = data
            if data["visit"] is not None and not data["visit"].empty:
                all_visits.append(data["visit"])

    with tab_trends:
        combined_visits = pd.concat(all_visits, ignore_index=True) if all_visits else pd.DataFrame()
        render_tab_trends(all_months_data, combined_visits, currency)


if __name__ == "__main__":
    main()
