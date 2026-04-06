"""
Tab 3 — MR Performance
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from constants import (
    FCFA_TO_EUR, TEMPLATE, _NON_MR_IDS,
    CLR_BLUE, CLR_TEAL, CLR_GREEN, CLR_ORANGE, CLR_PURPLE, CLR_RED
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
            split_amount = row.get("Amount_FCFA_Share", row["Amount_FCFA"] / len(mr_ids))
            for mr_id in mr_ids:
                mr_spend_map[mr_id] = mr_spend_map.get(mr_id, 0) + split_amount

    # ── Build visit count map (Verified visits) ──
    visit_count_map = {}
    if not visits.empty and "MR_ID" in visits.columns:
        # If there is a Month column, prioritize Feb, but we aggregate all if not specified.
        feb_visits = visits[visits["Month"] == "Feb"] if "Month" in visits.columns else visits
        visit_count_map = feb_visits.groupby("MR_ID").size().to_dict()

    st.header("👥 Individual MR Reports")

    for _, row in field_delegates.iterrows():
        mr_id = row["MR_ID"]
        display_name = mr_display_name(mr_id) if mr_id in MR_CANONICAL else row["Delegate"]
        spend = mr_spend_map.get(mr_id, 0)
        territory = territory_display_name(normalize_territory(row["Territory"]))

        # Check for unmapped MRs and assign them gracefully
        if mr_id == "UNKNOWN":
            continue

        with st.container():
            st.markdown(f"""
            <div style="background-color:rgba(76,159,255,0.05); padding: 12px 16px; border-left: 4px solid #4C9FFF; border-radius: 4px; margin-bottom: 12px;">
                <h3 style="margin:0; color: #4C9FFF;">{display_name} <span style="font-size: 16px; color:#8899aa; font-weight: normal;">— {territory}</span></h3>
            </div>
            """, unsafe_allow_html=True)
            
            # --- 1. KPI Row ---
            kpi_row([
                {"label": "Total Calls",      "value": f"{int(row['TotalCalls'])}",   "color": CLR_BLUE},
                {"label": "Prescriber Calls", "value": f"{int(row['Prescriber'])}",   "color": CLR_TEAL},
                {"label": "Drs Converted",    "value": f"{int(row['DrsConverted'])}", "color": CLR_GREEN},
                {"label": "Days Worked",      "value": f"{int(row['DaysWorked'])} / {int(row['DaysTarget'])}", "color": CLR_ORANGE},
                {"label": f"Spend ({unit})",  "value": fmt_currency(spend*mul, unit), "color": CLR_PURPLE},
            ])

            # --- 2. Tour Plan Coverage & Verified Visits ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📍 Reported vs Verified Visits")
                rep = int(row["TotalCalls"])
                ver = visit_count_map.get(mr_id, 0)
                
                # Simple progress comparison
                pct_verified = (ver / rep * 100) if rep > 0 else 0
                st.write(f"**Reported (Self):** {rep}")
                st.write(f"**Verified (Tracker):** {ver} *({pct_verified:.1f}% tracking rate)*")

            with col2:
                st.markdown("##### 🗺️ Tour Programme Coverage")
                if tour_plan_data is not None and not tour_plan_data.empty:
                    mr_tp = tour_plan_data[tour_plan_data["MR"] == mr_id]
                    if not mr_tp.empty:
                        planned = len(mr_tp)
                        covered = mr_tp["Covered"].sum()
                        pct = (covered / planned * 100) if planned > 0 else 0
                        st.write(f"**Total Days Planned:** {planned}")
                        st.write(f"**Days Actual Area == Planned Area:** {covered} ")
                        st.write(f"**Compliance Rate:** {pct:.1f}%")
                    else:
                        st.info("No Tour Plan data mapped for this MR.")
                else:
                    st.info("Tour Plan file not uploaded.")

            # --- 3. Tour Plan Details ---
            st.markdown("---")
            st.markdown("##### 📍 Detailed Tour Plan Status")
            if tour_plan_data is not None and not tour_plan_data.empty:
                mr_tp = tour_plan_data[tour_plan_data["MR"] == mr_id]
                if not mr_tp.empty:
                    col_tp1, col_tp2 = st.columns([1, 1.5])
                    tp_detail = mr_tp.sort_values("Date").copy()
                    tp_detail["Status"] = tp_detail["Covered"].apply(lambda c: "Covered" if c else "Missed Area")
                    
                    with col_tp1:
                        # Graph: Donut chart for summary compliance
                        status_counts = tp_detail["Status"].value_counts().reset_index()
                        status_counts.columns = ["Status", "Days"]
                        fig_tp = px.pie(
                            status_counts, names="Status", values="Days", hole=0.5,
                            color="Status", color_discrete_map={"Covered": CLR_GREEN, "Missed Area": CLR_RED}
                        )
                        fig_tp.update_layout(
                            template=TEMPLATE, height=220,
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            margin=dict(t=10, b=10, l=10, r=10),
                            showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_tp, use_container_width=True)
                    
                    with col_tp2:
                        # Table: Detailed History
                        tp_detail['Date'] = pd.to_datetime(tp_detail['Date']).dt.strftime('%d %b')
                        st.dataframe(
                            tp_detail[['Date', 'Joint_Working', 'Planned_Area', 'Actual_Area', 'Covered']].rename(
                                columns={'Planned_Area': 'Planned Area', 'Actual_Area': 'Actual Area', 'Joint_Working': 'Joint Working'}
                            ),
                            use_container_width=True, hide_index=True, height=200
                        )
                else:
                    st.caption("No Detailed Plan Available.")
            else:
                st.caption("Provide Tour Plan file to render details.")
            
            # --- 4. Doctor Repeat Visits ---
            st.markdown("---")
            st.markdown("##### 🔄 Doctors Visited > 1 Time (Repeats)")
            if not visits.empty:
                mr_visits = visits[visits["MR_ID"] == mr_id]
                if not mr_visits.empty:
                    repeat_visits = (
                        mr_visits.groupby(["Doctor", "Clinic", "Speciality"])
                        .size().reset_index(name="Visits")
                    )
                    repeat_visits = repeat_visits[repeat_visits["Visits"] > 1].sort_values("Visits", ascending=True)
                    if not repeat_visits.empty:
                        repeat_visits["DocLabel"] = repeat_visits.apply(
                            lambda r: f"{r['Doctor']} ({str(r['Clinic'])[:10]}...)" if r['Clinic'] and len(str(r['Clinic'])) > 10 else f"{r['Doctor']}", axis=1
                        )
                        # Render as a Treemap to fit all doctors dynamically (Full Width, Larger Height)
                        fig_rv = px.treemap(
                            repeat_visits,
                            path=[px.Constant("Doctors"), "DocLabel"],
                            values="Visits",
                            color="Visits",
                            color_continuous_scale="Teal",
                            hover_data={"Doctor": True, "Clinic": True, "Speciality": True, "Visits": True, "DocLabel": False},
                        )
                        fig_rv.update_layout(
                            template=TEMPLATE, height=400,
                            margin=dict(t=20, b=10, l=10, r=10)
                        )
                        fig_rv.update_traces(marker=dict(line=dict(width=1, color="#1a2535")))
                        st.plotly_chart(fig_rv, use_container_width=True)
                        
                        # Table beneath chart (show all descending)
                        st.dataframe(
                            repeat_visits.sort_values("Visits", ascending=False).rename(columns={"Visits": "Total Visits"}).drop(columns=["DocLabel"]),
                            use_container_width=True, hide_index=True, height=200
                        )
                    else:
                        st.info("No repeated visits (>1) recorded for this MR.")
                else:
                    st.caption("No Visit Tracker entries matched to this MR.")
            else:
                st.caption("Provide Visit Tracker file to render repeat data.")

        st.markdown("---")

    # ── Comparative Analytics (Aggregate) ──
    st.header("📈 MR Comparative Analytics")

    col_cmp1, col_cmp2 = st.columns(2)
    with col_cmp1:
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
            
    with col_cmp2:
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
    st.subheader("📋 Overall MR Summary Table")
    summary = field_delegates.copy()
    summary = summary[summary["MR_ID"] != "UNKNOWN"]
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
