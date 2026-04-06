"""
Tab 3 — MR Performance
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from constants import (
    FCFA_TO_EUR, TEMPLATE, _NON_MR_IDS,
    CLR_BLUE, CLR_TEAL, CLR_GREEN, CLR_ORANGE, CLR_PURPLE,
)
from utils import fmt_currency, kpi_row
from name_map import MR_CANONICAL, mr_display_name, normalize_territory, territory_display_name


def render_tab3(monthly_data, expense_data, visit_data, tour_plan_data, currency):
    delegates = monthly_data["delegates"]
    ae = expense_data["activity_exp"]
    visits = visit_data
    mul = 1 if currency == "FCFA" else (1 / FCFA_TO_EUR)
    unit = currency

    if delegates.empty:
        st.info("Upload Monthly Reports file to see MR performance.")
        return

    # Exclude non-field MRs (CM, Agent)
    field_delegates = delegates[~delegates["MR_ID"].isin(_NON_MR_IDS)].copy()
    if field_delegates.empty:
        st.info("No field MR data found after filtering.")
        return

    # ── Build spend map ──
    mr_spend_map = {}
    if not ae.empty and "MR_IDs" in ae.columns:
        for _, row in ae.iterrows():
            mr_ids = [i.strip() for i in str(row["MR_IDs"]).split(",")
                      if i.strip() and i.strip() != "UNKNOWN"]
            if not mr_ids:
                continue
            split_amount = row["Amount_FCFA"] / len(mr_ids)
            for mr_id in mr_ids:
                mr_spend_map[mr_id] = mr_spend_map.get(mr_id, 0) + split_amount

    # ── Build visit count map ──
    visit_count_map = {}
    if not visits.empty and "MR_ID" in visits.columns:
        feb_visits = visits[visits["Month"] == "Feb"] if "Month" in visits.columns else visits
        visit_count_map = feb_visits.groupby("MR_ID").size().to_dict()

    # ── Per-MR KPI cards ──
    st.subheader("👥 MR Individual KPIs")
    for _, row in field_delegates.iterrows():
        mr_id = row["MR_ID"]
        display_name = mr_display_name(mr_id) if mr_id in MR_CANONICAL else row["Delegate"]
        spend = mr_spend_map.get(mr_id, 0)
        territory = territory_display_name(normalize_territory(row["Territory"]))
        st.markdown(f"##### {display_name} — *{territory}*")
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

    # ── Reported vs Verified ──
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

    # ── Spend & Converted charts ──
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💸 Total Spend per MR")
        spend_df = pd.DataFrame([
            {"MR": mr_display_name(k), "Spend": v*mul}
            for k, v in mr_spend_map.items() if k not in _NON_MR_IDS
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

    # ── Summary Table ──
    st.subheader("📋 MR Summary Table")
    summary = field_delegates.copy()
    summary["Display"] = summary["MR_ID"].apply(
        lambda i: mr_display_name(i) if i in MR_CANONICAL
        else summary.loc[summary["MR_ID"]==i, "Delegate"].values[0]
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
        tp_mr = tour_plan_data.groupby('MR').agg(
            Total_Plans=('MR', 'count'),
            Covered_Plans=('Covered', 'sum')
        ).reset_index()
        tp_mr['Coverage_%'] = (tp_mr['Covered_Plans'] / tp_mr['Total_Plans'] * 100).round(1)
        tp_mr['MR_Display'] = tp_mr['MR'].apply(
            lambda i: mr_display_name(i) if i in MR_CANONICAL else i)

        col_tp1, col_tp2 = st.columns([1, 2])
        with col_tp1:
            st.dataframe(
                tp_mr[['MR_Display','Total_Plans','Covered_Plans','Coverage_%']].rename(columns={
                    'MR_Display': 'MR', 'Total_Plans': 'Total Days Planned',
                    'Covered_Plans': 'Days Covered Area', 'Coverage_%': 'Coverage %'
                }),
                width='stretch', hide_index=True)
        with col_tp2:
            fig_tp = px.bar(tp_mr, x="MR_Display", y="Coverage_%", template=TEMPLATE, height=340,
                            color="Coverage_%", color_continuous_scale="Teal",
                            labels={"Coverage_%": "Coverage %", "MR_Display": "MR"})
            fig_tp.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(t=20, b=60), showlegend=False, xaxis_tickangle=-20)
            st.plotly_chart(fig_tp, width='stretch')

        st.markdown("**Detail: Tour Plan Coverage**")
        tp_detail = tour_plan_data.copy()
        tp_detail['MR'] = tp_detail['MR'].apply(
            lambda i: mr_display_name(i) if i in MR_CANONICAL else i)
        import pandas as _pd
        tp_detail['Date'] = _pd.to_datetime(tp_detail['Date']).dt.strftime('%Y-%m-%d')
        st.dataframe(
            tp_detail.rename(columns={
                'Planned_Area': 'Planned Area',
                'Actual_Area': 'Actual Area',
                'Joint_Working': 'Joint Working'
            }),
            width='stretch', hide_index=True)
    else:
        st.info("Upload 'Tour Plan' file to see area coverage metrics.")
