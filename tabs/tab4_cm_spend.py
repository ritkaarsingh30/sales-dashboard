"""
Tab 4 — CM Spend
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from constants import (
    FCFA_TO_EUR, TEMPLATE,
    CLR_BLUE, CLR_TEAL, CLR_GREEN, CLR_RED, CLR_ORANGE, CLR_PURPLE, CLR_YELLOW,
)
from utils import fmt_currency, kpi_row


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

    # ── Budget Flow ──
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

    with col2:
        st.markdown("**Cumulative Spend Over Feb**")
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
    st.markdown("---")

    # ── Spend Breakdown by Category ──
    st.subheader("📊 Spend Breakdown by Category")
    if not ae.empty and "MR_IDs" in ae.columns:
        ae_exploded = ae.copy()
        ae_exploded['MR_ID_List'] = ae_exploded['MR_IDs'].apply(
            lambda x: [i.strip() for i in str(x).split(",") if i.strip()])
        ae_exploded['Num_MRs'] = ae_exploded['MR_ID_List'].apply(lambda x: max(1, len(x)))
        ae_exploded = ae_exploded.explode('MR_ID_List')
        ae_exploded['Amount_FCFA'] = ae_exploded['Amount_FCFA'] / ae_exploded['Num_MRs']

        def classify_spend(mr_id):
            if mr_id == "MR_006":   return "CM Direct"
            if mr_id == "AGT_001":  return "Agent (ARRA BEHOU)"
            if mr_id != "UNKNOWN":  return "MR Attributed"
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
        fig_stk.add_bar(name=row["SpendType"], x=["Feb 2026"], y=[row["Amount"]],
                        marker_color=colors_map.get(row["SpendType"], CLR_BLUE),
                        text=[fmt_currency(row["Amount"], unit)], textposition="inside")
    fig_stk.update_layout(barmode="stack", template=TEMPLATE, height=360,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           yaxis_title=f"Amount ({unit})",
                           legend=dict(orientation="h", y=1.1),
                           margin=dict(t=30, b=20))
    st.plotly_chart(fig_stk, width='stretch')
    st.markdown("---")

    # ── CM Direct Activities ──
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

    # ── Agent Activities ──
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

    # ── Other Expenses ──
    st.subheader("📋 Other Expenses")
    if not oe.empty:
        oe_display = oe.copy()
        oe_display[f"Amount ({unit})"] = oe_display["Amount_FCFA"].apply(
            lambda v: fmt_currency(v*mul, unit))
        oe_display["Amount EUR"] = oe_display["Amount_EUR"].apply(
            lambda v: fmt_currency(v, "EUR"))
        st.dataframe(
            oe_display[["Country","Details",f"Amount ({unit})","Amount EUR","Comments","Category"]],
            width='stretch', hide_index=True)
    else:
        st.info("No other expense data.")
