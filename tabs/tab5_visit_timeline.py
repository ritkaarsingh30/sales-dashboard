"""
Tab 5 — Visit Timeline
"""

import streamlit as st
import plotly.express as px

from constants import TEMPLATE
from utils import placeholder_tab


def render_tab5(visit_data, current_month: str):
    if visit_data.empty:
        placeholder_tab("Visit Timeline", f"Upload at least one Visit Tracker file for {current_month} to see this tab.")
        return

    visits = visit_data.copy()
    visits["Day"] = visits["Visit_Date"].dt.day

    # ── Controls ──
    ctrl1, ctrl2 = st.columns([1, 2])
    with ctrl1:
        available_months = sorted(visits["Month"].unique()) if "Month" in visits.columns else [current_month[:3]]
        selected_month = st.selectbox("📅 Month", available_months, index=0, key=f"sel_month_{current_month}")
    with ctrl2:
        mr_list = sorted(visits["MR"].unique().tolist())
        selected_mr = st.selectbox("👤 MR", ["All"] + mr_list, key=f"sel_mr_{current_month}")

    month_visits = visits[visits["Month"] == selected_month].copy() if "Month" in visits.columns else visits
    filtered = month_visits if selected_mr == "All" else month_visits[month_visits["MR"] == selected_mr]
    st.markdown("---")

    # ── Daily Visit Line Chart ──
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
        st.plotly_chart(fig_line, width='stretch', key=f"fig_line_{current_month}")

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
        st.plotly_chart(fig_hm, width='stretch', key=f"fig_hm_{current_month}")
    st.markdown("---")

    # ── Detail Table ──
    st.subheader("📋 Visit Details")
    if not filtered.empty:
        show = filtered[["MR","Doctor","Speciality","Clinic","Visit_Date"]].copy()
        show["Visit_Date"] = show["Visit_Date"].dt.strftime("%d-%b-%Y")
        show = show.sort_values(["MR","Visit_Date"])
        st.dataframe(show.rename(columns={"Visit_Date": "Visit Date"}),
                     width='stretch', hide_index=True, key=f"df_visit_detail_{current_month}")
    else:
        st.info(f"No visits found for the selected filter in {selected_month} 2026.")
