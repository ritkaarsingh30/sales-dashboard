"""
Tab 1 — Performance Overview
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from constants import (
    FCFA_TO_EUR, TEMPLATE, DISTRIBUTORS, DIST_COLORS,
    CLR_GREEN, CLR_RED, CLR_BLUE, CLR_ORANGE, CLR_TEAL,
)
from utils import fmt_currency, kpi_row


def render_tab1(sales_data, proj_data, copy_data, currency, current_month: str):
    current = sales_data["current"]
    prev = sales_data.get("prev", pd.DataFrame())
    proj = proj_data["projection"]
    prod_perf = copy_data["product_perf"]

    # ── KPI cards ──
    total_curr_eur = current["TOTAL_VALUE_EUR"].sum() if not current.empty else 0
    total_target_eur = proj["Target_Value_EUR"].sum() if not proj.empty else 0
    ach_pct = (total_curr_eur / total_target_eur * 100) if total_target_eur else 0
    color_ach = CLR_GREEN if ach_pct >= 100 else CLR_RED
    unit = currency

    kpi_row([
        {"label": f"Total {current_month} Sales",
         "value": fmt_currency(total_curr_eur * (1 if currency == "EUR" else FCFA_TO_EUR), unit),
         "color": CLR_BLUE},
        {"label": f"{current_month} Target",
         "value": fmt_currency(total_target_eur * (1 if currency == "EUR" else FCFA_TO_EUR), unit),
         "color": CLR_ORANGE},
        {"label": "Achievement %",
         "value": f"{ach_pct:.1f}%",
         "delta": f"+{ach_pct-100:.1f}%" if ach_pct >= 100 else f"{ach_pct-100:.1f}%",
         "color": color_ach},
    ])
    st.markdown("---")

    # ── Target vs Achieved ──
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
        st.plotly_chart(fig_ta, width='stretch', key=f"fig_ta_{current_month}")
    else:
        st.info("Upload 'Copy of Report' file to see this chart.")

    st.markdown("---")

    # ── Sales Trend ──
    st.subheader("📈 Sales Trend (Units per Product)")
    if not current.empty:
        if not prev.empty:
            # Two months available — show line trend
            prev_s = prev[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Prev"})
            curr_s = current[["Product", "TOTAL_SALES"]].rename(columns={"TOTAL_SALES": "Current"})
            trend = prev_s.merge(curr_s, on="Product", how="outer").fillna(0)
            trend_long = trend.melt(id_vars="Product", var_name="Month", value_name="Units")
            fig_trend = px.line(trend_long, x="Month", y="Units", color="Product",
                                markers=True, template=TEMPLATE, height=400)
            fig_trend.update_traces(line_width=2.5)
            fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(t=20, b=20))
            st.plotly_chart(fig_trend, width='stretch', key=f"fig_trend_{current_month}")

            st.subheader("📊 Prev vs Current Sales Comparison (Units)")
            fig_cmp = go.Figure()
            fig_cmp.add_trace(go.Scatter(name="Prev", x=trend["Product"], y=trend["Prev"],
                                         mode='lines+markers', line=dict(color=CLR_BLUE, width=2)))
            fig_cmp.add_trace(go.Scatter(name="Current", x=trend["Product"], y=trend["Current"],
                                         mode='lines+markers', line=dict(color=CLR_TEAL, width=2)))
            fig_cmp.update_layout(template=TEMPLATE, height=360,
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(t=20, b=60), xaxis_tickangle=-25,
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_cmp, width='stretch', key=f"fig_cmp_{current_month}")
        else:
            # First month — no previous data, show current as bar chart
            st.caption(f"ℹ️ No previous month data available — showing {current_month} units only.")
            curr_s = current[["Product", "TOTAL_SALES"]].sort_values("TOTAL_SALES", ascending=False)
            fig_trend = go.Figure(go.Bar(
                x=curr_s["Product"], y=curr_s["TOTAL_SALES"],
                marker_color=CLR_BLUE,
                text=curr_s["TOTAL_SALES"].astype(int), textposition="outside",
            ))
            fig_trend.update_layout(template=TEMPLATE, height=400,
                                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(t=20, b=60), xaxis_tickangle=-25,
                                    yaxis_title="Units Sold")
            st.plotly_chart(fig_trend, width='stretch', key=f"fig_trend_{current_month}")

    st.markdown("---")

    # ── Distributor 2×2 ──
    st.subheader("🏭 Sales by Distributor (Units) with MoM Growth")
    if not current.empty:
        fig_dist = make_subplots(rows=2, cols=2, subplot_titles=DISTRIBUTORS,
                                 vertical_spacing=0.25, horizontal_spacing=0.10)
        for (r, c), dist in zip([(1,1),(1,2),(2,1),(2,2)], DISTRIBUTORS):
            col_key = f"{dist}_SALES"
            if col_key not in current.columns:
                continue
            d_curr = current[["Product", col_key]].rename(columns={col_key: "Curr_Sales"})
            if not prev.empty and col_key in prev.columns:
                d_prev = prev[["Product", col_key]].rename(columns={col_key: "Prev_Sales"})
                sub = pd.merge(d_curr, d_prev, on="Product", how="left").fillna(0)
                sub["MoM_Text"] = sub.apply(
                    lambda row: f"+{((row['Curr_Sales']-row['Prev_Sales'])/row['Prev_Sales']*100):.0f}%"
                    if row['Prev_Sales'] > 0 and row['Curr_Sales'] > row['Prev_Sales']
                    else (f"{((row['Curr_Sales']-row['Prev_Sales'])/row['Prev_Sales']*100):.0f}%"
                          if row['Prev_Sales'] > 0 else "New"),
                    axis=1
                )
                sub["Display_Text"] = sub["Curr_Sales"].astype(int).astype(str) + " (" + sub["MoM_Text"] + ")"
            else:
                sub = d_curr.copy().fillna(0)
                sub["Prev_Sales"] = 0
                sub["Display_Text"] = sub["Curr_Sales"].astype(int).astype(str)
            sub = sub[sub["Curr_Sales"] > 0].sort_values("Curr_Sales", ascending=True)
            fig_dist.add_trace(go.Bar(
                name=dist, x=sub["Curr_Sales"], y=sub["Product"], orientation="h",
                marker_color=DIST_COLORS[dist],
                text=sub["Display_Text"], textposition="outside",
                showlegend=False,
            ), row=r, col=c)
        fig_dist.update_layout(template=TEMPLATE, height=700,
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=50, b=20))
        st.plotly_chart(fig_dist, width='stretch', key=f"fig_dist_{current_month}")


