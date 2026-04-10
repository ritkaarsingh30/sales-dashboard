"""
Month Trends Tab — Cross-Month Comparative Analytics (Jan / Feb / Mar)
Sections:
  1. MR Performance Trend   — Calls, Drs Converted, Days Worked
  2. Field Visit Activity   — Verified visits per MR and team total
  3. Budget & Spend Trend   — Received vs Spent vs Balance, per-MR spend
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from constants import (
    FCFA_TO_EUR, TEMPLATE,
    CLR_BLUE, CLR_TEAL, CLR_GREEN, CLR_ORANGE, CLR_PURPLE, CLR_RED,
)
from utils import fmt_currency, kpi_row
from name_map import mr_display_name, normalize_mr

# ── Colour palette for months ──────────────────────────────────────────────────
MONTH_COLORS = {
    "January":  "#4C9FFF",
    "February": "#00D4AA",
    "March":    "#F4A523",
}
MONTHS = ["January", "February", "March"]


def _safe_delegates(monthly_data) -> pd.DataFrame | None:
    """Return delegates DataFrame or None."""
    if monthly_data and monthly_data.get("delegates") is not None:
        df = monthly_data["delegates"]
        return df if not df.empty else None
    return None


def _safe_expense(expense_data) -> dict | None:
    return expense_data if expense_data else None


def render_tab_trends(all_months: dict, visit_data_all: pd.DataFrame, currency: str):
    """
    all_months: {
        "January":  {"monthly": ..., "expense": ..., "proj": ...},
        "February": { ... },
        "March":    { ... },
    }
    visit_data_all: unified visit tracker DataFrame with Month column
    currency: "FCFA" or "EUR"
    """
    mul = 1 / FCFA_TO_EUR if currency == "EUR" else 1
    unit = "EUR" if currency == "EUR" else "FCFA"

    st.markdown("""
        <div style="padding:16px 0 8px 0;border-bottom:1px solid #1e3050;margin-bottom:24px;">
            <h2 style="margin:0;color:#e8f0ff;font-size:22px;font-weight:700;">
                📈 Month Trends — Jan → Feb → Mar 2026
            </h2>
            <p style="margin:4px 0 0 0;color:#8899aa;font-size:13px;">
                Cross-month comparative analytics across MR performance, field visits and budget.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Check data availability ───────────────────────────────────────────────
    available = [m for m in MONTHS if m in all_months]
    missing   = [m for m in MONTHS if m not in all_months]
    if missing:
        st.warning(
            f"⚠️ Please upload data for **{', '.join(missing)}** to unlock Month Trends. "
            "All three months are required."
        )
        return

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — MR PERFORMANCE TREND
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("## 👥 MR Performance Trend")

    # Build combined delegates DataFrame
    del_frames = []
    for month in MONTHS:
        df = _safe_delegates(all_months[month].get("monthly"))
        if df is not None:
            df = df.copy()
            df["Month"] = month
            del_frames.append(df)

    if del_frames:
        delegates_all = pd.concat(del_frames, ignore_index=True)
        # Exclude non-MR entries
        from constants import _NON_MR_IDS
        delegates_all = delegates_all[~delegates_all["MR_ID"].isin(_NON_MR_IDS)]
        delegates_all = delegates_all[delegates_all["MR_ID"] != "UNKNOWN"]
        delegates_all["DisplayName"] = delegates_all["MR_ID"].apply(
            lambda x: mr_display_name(x) if x else x
        )

        col_a, col_b = st.columns(2)

        # ── Chart: Total Calls per MR ──────────────────────────────────────
        with col_a:
            st.subheader("📞 Total Calls per MR")
            fig_calls = go.Figure()
            for month in MONTHS:
                sub = delegates_all[delegates_all["Month"] == month]
                fig_calls.add_trace(go.Bar(
                    name=month,
                    x=sub["DisplayName"],
                    y=sub["TotalCalls"].fillna(0).astype(int),
                    marker_color=MONTH_COLORS[month],
                    text=sub["TotalCalls"].fillna(0).astype(int),
                    textposition="outside",
                ))
            fig_calls.update_layout(
                barmode="group", template=TEMPLATE, height=380,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=60, l=20, r=20),
                legend=dict(orientation="h", y=1.08),
                xaxis_tickangle=-15,
                yaxis_title="Total Calls",
            )
            st.plotly_chart(fig_calls, width="stretch", key="trend_calls")

        # ── Chart: Drs Converted per MR ────────────────────────────────────
        with col_b:
            st.subheader("🩺 Doctors Converted per MR")
            fig_conv = go.Figure()
            for month in MONTHS:
                sub = delegates_all[delegates_all["Month"] == month]
                fig_conv.add_trace(go.Bar(
                    name=month,
                    x=sub["DisplayName"],
                    y=sub["DrsConverted"].fillna(0).astype(int),
                    marker_color=MONTH_COLORS[month],
                    text=sub["DrsConverted"].fillna(0).astype(int),
                    textposition="outside",
                ))
            fig_conv.update_layout(
                barmode="group", template=TEMPLATE, height=380,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=60, l=20, r=20),
                legend=dict(orientation="h", y=1.08),
                xaxis_tickangle=-15,
                yaxis_title="Drs Converted",
            )
            st.plotly_chart(fig_conv, width="stretch", key="trend_drs_conv")

        # ── Chart: Days Worked vs Target ────────────────────────────────────
        st.subheader("⏰ Days Worked vs Target (per MR per Month)")
        fig_days = go.Figure()
        for month in MONTHS:
            sub = delegates_all[delegates_all["Month"] == month]
            fig_days.add_trace(go.Bar(
                name=f"{month} — Worked",
                x=sub["DisplayName"],
                y=sub["DaysWorked"].fillna(0).astype(int),
                marker_color=MONTH_COLORS[month],
                opacity=0.9,
                legendgroup=month,
            ))
            fig_days.add_trace(go.Scatter(
                name=f"{month} — Target",
                x=sub["DisplayName"],
                y=sub["DaysTarget"].fillna(0).astype(int),
                mode="markers",
                marker=dict(color=MONTH_COLORS[month], size=10, symbol="line-ew-open", line=dict(width=3)),
                legendgroup=month,
            ))
        fig_days.update_layout(
            barmode="group", template=TEMPLATE, height=380,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=60, l=20, r=20),
            legend=dict(orientation="h", y=1.08, traceorder="grouped"),
            xaxis_tickangle=-15,
            yaxis_title="Days",
        )
        st.plotly_chart(fig_days, width="stretch", key="trend_days")

    else:
        st.info("No delegate report data available across months.")

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — FIELD VISIT ACTIVITY
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("## 🏃 Field Visit Activity Trend")

    if not visit_data_all.empty and "Month" in visit_data_all.columns:
        # Map short month label (Jan/Feb/Mar) → full name
        month_label_map = {"Jan": "January", "Feb": "February", "Mar": "March"}
        visit_data_all = visit_data_all.copy()
        visit_data_all["MonthFull"] = visit_data_all["Month"].map(month_label_map).fillna(visit_data_all["Month"])

        col_c, col_d = st.columns(2)

        # ── Chart: Team Total per Month (line) ─────────────────────────────
        with col_c:
            st.subheader("📊 Total Team Visits per Month")
            totals = (
                visit_data_all.groupby("MonthFull")
                .size().reindex(MONTHS, fill_value=0)
                .reset_index(name="Visits")
            )
            totals.columns = ["Month", "Visits"]
            fig_total = go.Figure(go.Scatter(
                x=totals["Month"], y=totals["Visits"],
                mode="lines+markers+text",
                text=totals["Visits"],
                textposition="top center",
                line=dict(color=CLR_BLUE, width=3),
                marker=dict(size=10, color=CLR_BLUE),
                fill="tozeroy",
                fillcolor="rgba(76,159,255,0.08)",
            ))
            fig_total.update_layout(
                template=TEMPLATE, height=340,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=40, l=20, r=20),
                yaxis_title="Total Visits",
            )
            st.plotly_chart(fig_total, width="stretch", key="trend_total_visits")

        # ── Chart: Visits per MR per Month ─────────────────────────────────
        with col_d:
            st.subheader("👤 Visits per MR per Month")
            mr_month = (
                visit_data_all.groupby(["MR", "MonthFull"])
                .size().reset_index(name="Visits")
            )
            fig_mr_visits = go.Figure()
            for month in MONTHS:
                sub = mr_month[mr_month["MonthFull"] == month]
                fig_mr_visits.add_trace(go.Bar(
                    name=month,
                    x=sub["MR"],
                    y=sub["Visits"],
                    marker_color=MONTH_COLORS[month],
                    text=sub["Visits"],
                    textposition="outside",
                ))
            fig_mr_visits.update_layout(
                barmode="group", template=TEMPLATE, height=340,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=60, l=20, r=20),
                legend=dict(orientation="h", y=1.08),
                xaxis_tickangle=-20,
                yaxis_title="Visits",
            )
            st.plotly_chart(fig_mr_visits, width="stretch", key="trend_mr_visits")

    else:
        st.info("No visit tracker data available. Please upload visit trackers for all three months.")

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — BUDGET & SPEND TREND
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("## 💰 Budget & Spend Trend")

    budget_rows = []
    mr_spend_rows = []

    for month in MONTHS:
        expense = _safe_expense(all_months[month].get("expense"))
        if not expense:
            continue
        summary = expense.get("summary", {})
        received = summary.get("total_received", 0) or 0
        spent    = summary.get("total_spent", 0) or 0
        balance  = summary.get("balance", 0) or 0
        budget_rows.append({
            "Month": month,
            "Received": received * mul,
            "Spent":    spent * mul,
            "Balance":  balance * mul,
        })

        # Per-MR spend from activity_expenses
        act_exp = expense.get("activity_expenses")
        if act_exp is not None and not act_exp.empty:
            # Split joint activities
            for _, row in act_exp.iterrows():
                raw_mr = str(row.get("MR", "")).strip()
                amt = row.get("Amount_FCFA", 0) or 0
                mr_ids = [normalize_mr(x.strip()) for x in raw_mr.split("/") if x.strip()]
                if not mr_ids:
                    continue
                share = amt / len(mr_ids)
                for mr_id in mr_ids:
                    mr_spend_rows.append({
                        "Month":  month,
                        "MR_ID":  mr_id,
                        "MR":     mr_display_name(mr_id),
                        "Amount": share * mul,
                    })

    # ── Chart: Budget Received vs Spent vs Balance ──────────────────────────
    if budget_rows:
        bdf = pd.DataFrame(budget_rows)
        col_e, col_f = st.columns(2)

        with col_e:
            st.subheader(f"📥 Budget Received vs Spent ({unit})")
            fig_budget = go.Figure()
            fig_budget.add_trace(go.Bar(
                name="Received", x=bdf["Month"], y=bdf["Received"],
                marker_color=CLR_GREEN, opacity=0.85,
                text=[fmt_currency(v, unit) for v in bdf["Received"]],
                textposition="outside",
            ))
            fig_budget.add_trace(go.Bar(
                name="Spent", x=bdf["Month"], y=bdf["Spent"],
                marker_color=CLR_RED, opacity=0.85,
                text=[fmt_currency(v, unit) for v in bdf["Spent"]],
                textposition="outside",
            ))
            fig_budget.add_trace(go.Bar(
                name="Balance", x=bdf["Month"], y=bdf["Balance"],
                marker_color=CLR_TEAL, opacity=0.85,
                text=[fmt_currency(v, unit) for v in bdf["Balance"]],
                textposition="outside",
            ))
            fig_budget.update_layout(
                barmode="group", template=TEMPLATE, height=360,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=40, l=20, r=20),
                legend=dict(orientation="h", y=1.08),
                yaxis_title=unit,
            )
            st.plotly_chart(fig_budget, width="stretch", key="trend_budget")

        # ── Chart: Spend efficiency line ─────────────────────────────────
        with col_f:
            st.subheader("📉 Spend Rate (% of Budget Used)")
            bdf["SpendRate"] = (bdf["Spent"] / bdf["Received"].replace(0, float("nan")) * 100).round(1)
            fig_rate = go.Figure(go.Scatter(
                x=bdf["Month"], y=bdf["SpendRate"],
                mode="lines+markers+text",
                text=[f"{v}%" for v in bdf["SpendRate"]],
                textposition="top center",
                line=dict(color=CLR_ORANGE, width=3),
                marker=dict(size=10, color=CLR_ORANGE),
                fill="tozeroy",
                fillcolor="rgba(244,165,35,0.08)",
            ))
            fig_rate.add_hline(
                y=80, line_dash="dash", line_color="#ff4444",
                annotation_text="80% threshold", annotation_position="bottom right",
            )
            fig_rate.update_layout(
                template=TEMPLATE, height=360,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=40, l=20, r=20),
                yaxis_title="% Budget Used", yaxis_range=[0, 120],
            )
            st.plotly_chart(fig_rate, width="stretch", key="trend_spend_rate")

    # ── Chart: Per-MR Spend per Month ──────────────────────────────────────
    if mr_spend_rows:
        mdf = pd.DataFrame(mr_spend_rows)
        mdf_grouped = mdf.groupby(["Month", "MR"])["Amount"].sum().reset_index()
        # Filter non-MRs
        from constants import _NON_MR_IDS
        mdf_grouped = mdf_grouped[~mdf_grouped["MR"].apply(normalize_mr).isin(_NON_MR_IDS)]

        st.subheader(f"💼 Activity Spend per MR per Month ({unit})")
        fig_mr_spend = go.Figure()
        for month in MONTHS:
            sub = mdf_grouped[mdf_grouped["Month"] == month]
            fig_mr_spend.add_trace(go.Bar(
                name=month,
                x=sub["MR"],
                y=sub["Amount"].round(0),
                marker_color=MONTH_COLORS[month],
                text=[fmt_currency(v, unit) for v in sub["Amount"]],
                textposition="outside",
            ))
        fig_mr_spend.update_layout(
            barmode="group", template=TEMPLATE, height=380,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=60, l=20, r=20),
            legend=dict(orientation="h", y=1.08),
            xaxis_tickangle=-20,
            yaxis_title=unit,
        )
        st.plotly_chart(fig_mr_spend, width="stretch", key="trend_mr_spend")
    else:
        st.info("No expense data available across months.")
