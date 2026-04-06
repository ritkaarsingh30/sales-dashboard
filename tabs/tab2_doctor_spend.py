"""
Tab 2 — Doctor Spend
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from constants import FCFA_TO_EUR, TEMPLATE, CLR_BLUE, CLR_ORANGE, CLR_GREEN, CLR_RED
from name_map import mr_display_name, MR_CANONICAL
from utils import fmt_currency, kpi_row

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

    # ── Planned vs Actual per Doctor ──
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
        st.plotly_chart(fig_doc, use_container_width=True)
    st.markdown("---")

    # ── Spend Breakdown: donut + by MR ──
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
            st.plotly_chart(fig_donut, use_container_width=True)
    with col2:
        st.markdown("**By Responsible MR (Attributed)**")
        if not ae.empty and "MR_IDs" in ae.columns:
            individual_mr_spend = {}
            for _, row in ae.iterrows():
                ids = [i.strip() for i in row["MR_IDs"].split(",") if i.strip()]
                share = row["Amount_FCFA_Share"]
                for mid in ids:
                    name = mr_display_name(mid) if mid in MR_CANONICAL else mid
                    individual_mr_spend[name] = individual_mr_spend.get(name, 0) + share
            
            mr_plot_df = pd.DataFrame([{"MR": k, "Amount": v * mul} for k, v in individual_mr_spend.items()])
            if not mr_plot_df.empty:
                mr_plot_df = mr_plot_df.sort_values("Amount", ascending=False)
                fig_mr = px.bar(mr_plot_df, x="MR", y="Amount",
                                template=TEMPLATE, height=360,
                                color="Amount", color_continuous_scale="Blues",
                                labels={"Amount": f"({unit})", "MR": "MR / CM"})
                fig_mr.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                     margin=dict(t=20, b=60), xaxis_tickangle=-30, showlegend=False)
                st.plotly_chart(fig_mr, use_container_width=True)
            else:
                st.info("No MR attribution data found.")
    st.markdown("---")

    # ── Detail Table ──
    st.subheader("📋 Doctor Spend Detail")
    if not ae.empty:
        display = ae.copy()
        display["Planned_FCFA"] = display["Doctor"].apply(
            lambda d: plan_agg.loc[plan_agg["Doctor"] == d, "Planned_FCFA"].sum()
            if not plan_agg.empty else 0
        )
        display["Planned"] = display["Planned_FCFA"].apply(lambda v: fmt_currency(v*mul, unit))
        display["Actual"]  = display["Amount_FCFA_Share"].apply(lambda v: fmt_currency(v*mul, unit))
        st.dataframe(
            display[["Doctor","Hospital","Speciality","Activity",
                      "Products","Planned","Actual","Responsible"]].rename(columns={
                "Planned": f"Planned ({unit})", "Actual": f"Actual Share ({unit})",
                "Responsible": "Responsible"}),
            width='stretch', hide_index=True)
