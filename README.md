# 💊 ZEE Pharma — Sales Dashboard Analytics

An interactive executive dashboard for **ZEE Pharmaceuticals**, built to monitor and analyse monthly field sales performance across Ivory Coast (IVC). All data is processed **locally in-browser** — no database, no server, no data leaves your machine.

---

## 📊 Dashboard Tabs

| Tab | What it shows |
|-----|---------------|
| **Performance Overview** | Feb sales vs targets, Jan→Feb trend, per-distributor breakdown |
| **Doctor Spend** | Planned vs actual activity spend per doctor, spend by activity type |
| **MR Performance** | Per-MR KPIs, reported vs verified visits, spend and conversion stats |
| **CM Spend** | Country Manager budget flow, utilisation %, activity and other expense breakdown |
| **Visit Timeline** | Calendar heatmap + daily line chart of MR field visits for Feb 2026 |
| **Injectable Commission** | Coming soon |

---

## 📁 Required Files

Upload these Excel files via the sidebar when using the dashboard:

| File | Purpose |
|------|---------|
| `IVC_SALES_FEB-2026.xlsx` | Monthly sales by product and distributor (Jan + Feb) |
| `IVC_PROJECTION_&_ACTIVITY_PLAN_FOR_THE_MONTH_OF_FEB-2026.xlsx` | Sales targets and planned doctor activities |
| `IVC_EXPENSE_&_ACTIVITY_SHEET_FEB-2026.xlsx` | Actual doctor spend, other expenses, money received |
| `IVC_MONTHLY_REPORTS_FEB-2026.xlsx` | MR call reports and budget analysis |
| `Ivory_coast_visit_tracker_feb-2026.xlsx` | MR-wise doctor visit log (5 sheets, one per MR) |
| `Copy_of_report_feb_IVC.xlsx` | Combined product performance and activity summary |

> ⚠️ **Data files are never committed to Git** (covered by `.gitignore`). Users upload them fresh each session.

---

## 🚀 Running Locally

**1. Clone the repo**
```bash
git clone <your-repo-url>
cd sales-dashboard
```

**2. Create a virtual environment and install dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Launch the dashboard**
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## ☁️ Streamlit Cloud Deployment

This app is deployed on [Streamlit Cloud](https://streamlit.io/cloud). Any push to the `main` branch automatically redeploys the app within ~60 seconds.

The dark theme is enforced via `.streamlit/config.toml` and will display consistently on all devices regardless of the viewer's OS preference.

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io/)** — web app framework
- **[Plotly Express](https://plotly.com/python/plotly-express/)** — interactive charts
- **[Pandas](https://pandas.pydata.org/)** — data wrangling
- **[openpyxl](https://openpyxl.readthedocs.io/)** — Excel file parsing

---

## 💱 Currency

All monetary values can be toggled between **FCFA** and **EUR** using the sidebar control.  
Conversion rate used: **1 EUR = 655.97 FCFA**

---

## 📌 Notes

- The dashboard is a **single-file app** (`app.py`) with helper functions per module — no external files or databases required.
- All file parsing uses the exact column structure of ZEE's February 2026 Excel templates.
- The **Injectable Commission** tab is reserved for future use.
