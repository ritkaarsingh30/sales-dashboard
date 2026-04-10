# 📊 IVC Pharma Executive Dashboard — User Guide

> **For internal use only. Please read before uploading any files.**

---

## 🖥️ Accessing the Dashboard

Open the dashboard URL in your browser. On the left sidebar you will find:
- A **Currency toggle** — switch between `FCFA` and `EUR` at any time.
- Two **Master File** uploaders (used across all months).
- A **Month selector tab** at the top of the main page (`January`, `February`, `March`).

Click a month tab and upload the 5 monthly files for that month. The dashboard renders **as soon as all files are uploaded**.

---

## 📁 File Reference

There are **2 master files** shared across all months, and **5 monthly files** per month.

---

### 🗂️ Master Files (upload once in the sidebar)

#### 1. Sales Data File
**Example name:** `IVC_Sales_Data_2026.xlsx`

Each month's data must be on a **separate sheet** named exactly:

| Month | Expected Sheet Name |
|-------|---------------------|
| January | `JAN-26` |
| February | `FEB-26` |
| March | `MAR-26` |

**Required columns (positional — no named header needed):**

| Col # | Content |
|-------|---------|
| A (0) | Category label (e.g. `TABLET`, `INJECTABLE`) — only on category rows |
| B (1) | Row serial number (1–17 for products) |
| C (2) | Product name |
| D (3) | Rate (price per unit in EUR) |
| E–G (4–6) | UBIPHARM/LABOREX: Sales, Closing Stock, Orders |
| H–J (7–9) | COPHARMED/LABOREX: Sales, Closing Stock, Orders |
| K–M (10–12) | TEDIS: Sales, Closing Stock, Orders |
| N–P (13–15) | DPCI: Sales, Closing Stock, Orders |
| Last col | Total Value (EUR) |

---

#### 2. Copy of Report File
**Example name:** `IVC_Copy_Of_Report_2026.xlsx`

Each month's report must be on a **separate sheet** named exactly:

| Month | Expected Sheet Name |
|-------|---------------------|
| January | `jan 2026` |
| February | `feb 2026` |
| March | `march 2026` |

This file has a **combined layout** — three sections side-by-side in the same sheet.

**Section 1 — Product Performance (Columns A–E):**

| Col # | Content |
|-------|---------|
| A (0) | Row serial number |
| B (1) | Product name |
| C (2) | Rate |
| D (3) | Target Units |
| E (4) | Achieved Units |

**Section 2 — Planned Doctor Activities (Columns F–J):**

| Col # | Content |
|-------|---------|
| F (5) | Doctor Name |
| G (6) | Hospital/Clinic |
| H (7) | Speciality |
| I (8) | Activity Type |
| J (9) | Amount (FCFA) |

**Section 3 — Actual Doctor Activities (Columns K–R):**

| Col # | Content |
|-------|---------|
| K (10) | Doctor Name |
| L (11) | Hospital/Clinic |
| M (12) | Speciality |
| N (13) | Activity Type |
| O (14) | Amount (FCFA) |
| P (15) | Remarks *(optional)* |
| Q (16) | Visited By (MR Name) *(optional)* |
| R (17) | No. of Visits *(optional)* |

> Columns P–R are optional. If your sheet does not have them, the dashboard will still work.

---

### 📅 Monthly Files (upload 5 files per month tab)

---

#### 1. Projection & Activity Plan
**Example name:** `IVC_Projection_Activity_Feb_2026.xlsx`

**Required sheets:**

| Sheet Name | Content |
|------------|---------|
| `PROJECTION` | Product sales targets |
| Any sheet with "ACTIVITY" in the name | Planned doctor visits |

**`PROJECTION` sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Row serial number |
| B (1) | Product name |
| C (2) | Rate (EUR) |
| D (3) | Target Units |
| E (4) | Target Value (EUR) |

**Activity Plan sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Serial number |
| B (1) | Doctor name |
| C (2) | Hospital/Clinic |
| D (3) | Speciality |
| E (4) | Delegate (MR name) |
| F (5) | Area/Territory |
| G (6) | Activity type |
| H (7) | Planned Amount (FCFA) |
| I (8) | Focus products (slash-separated, e.g. `OMECID/AVETEX`) |

---

#### 2. Expense & Activity Sheet
**Example name:** `IVC_EXPENSE_&_ACTIVITY_SHEET_Feb-2026.xlsx`

**Required sheets:**

| Sheet Name | Content |
|------------|---------|
| `MONEY RECEIVED` | Budget received and balance summary |
| `ACTIVITY EXP.` | Doctor-level activity spending |
| `OTHER EXP.` | Miscellaneous expenses |

**`MONEY RECEIVED` sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Date or label (e.g. `OPENING BALANCE`, `TOTAL RECEIVED FCFA`) |
| B (1) | Sub-label (e.g. `Opening Balance`, `Received Activity Money`) |
| C (2) | Amount (FCFA) |
| D (3) | Amount (EUR) |
| E (4) | Description |
| F (5) | Summary label (e.g. `TOTAL SPENT`, `BALANCE`) |
| G (6) | Summary value (FCFA) |

**`ACTIVITY EXP.` sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Serial number |
| B (1) | Doctor name |
| C (2) | Hospital/Clinic |
| D (3) | Speciality |
| E (4) | Activity type |
| F (5) | Products (slash-separated) |
| G (6) | Amount (FCFA) |
| H (7) | Contact reference |
| I (8) | Responsible MR (use `/` for joint activities, e.g. `JITENDRA/NELLY`) |

> **Joint Activities:** If two MRs worked together, write both names separated by `/` in column I. The dashboard automatically splits the cost equally between them.

**`OTHER EXP.` sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Serial number |
| B (1) | Country |
| C (2) | Details/Description |
| D (3) | Amount (FCFA) |
| E (4) | Amount (EUR) |
| F (5) | Comments |
| G (6) | Category |

---

#### 3. Monthly Reports
**Example name:** `IVC_MONTHLY_REPORTS_Feb-2026.xlsx`

**Required sheets:**

| Sheet Name | Content | Required? |
|------------|---------|-----------|
| `Delegates Reports` | MR performance metrics | Required |
| `Budget Analysis` | Doctor-level budget spend | Optional |

**`Delegates Reports` sheet columns:**

| Col # | Content |
|-------|---------|
| A (0) | Serial number |
| B (1) | Delegate (MR) name |
| C (2) | Territory |
| D (3) | Non-Prescriber calls |
| E (4) | Prescriber calls |
| F (5) | Doctors Converted |
| G (6) | Total Calls |
| H (7) | Pharmacy Calls |
| I (8) | Days Target |
| J (9) | Days Worked |
| K (10) | Avg Calls/Day |
| L (11) | Total Orders |
| M (12) | CTC |

> If `Budget Analysis` sheet is missing, all other MR data will still display. A warning will appear in the sidebar.

---

#### 4. Tour Plan vs Working Area
**Example name:** `IVC_TOUR_PLAN_VS_WORKING_AREA_Feb_2026.xlsx`

Single sheet (usually `Sheet1`). The dashboard auto-detects the header row.

**Expected column headers (must contain these keywords):**

| Keyword | Content |
|---------|---------|
| `DATE` | Date of planned visit |
| `NAME` or `MR` | MR name |
| `JOINT` | Joint working partner (optional) |
| `PLANNED AREA` | Territory planned |
| `ACTUAL AREA` | Territory actually visited |

---

#### 5. Visit Tracker
**Example name:** `IVC_Visit_Tracker_Feb_2026.xlsx`

Each **sheet** = one MR's visits. MR name is read from **cell C1** of each sheet. Rows 1–3 are metadata. **Row 4 must be the header row.**

**Header keywords the dashboard looks for (in row 4):**

| Keyword | Content |
|---------|---------|
| `NOM` | Doctor name |
| `SPEC` | Speciality |
| `CLINIC`, `HOSPITAL`, or `CSPS` | Clinic name |
| Any column with `VISIT` in header | Visit date(s) |

> Each visit-date column represents one visit. Multiple visit columns per row are supported.

---

## Common Warnings

| Warning | Meaning |
|---------|---------|
| `Missing sheets: Budget Analysis` | Monthly report uploaded but Budget Analysis tab not found. Other data still loads. |
| `Please upload all files` | One or more monthly files not yet uploaded for that month tab. |
| Date parsing warnings | Normal — visit tracker uses varied date formats. Data loads correctly. |

---

*Last updated: April 2026*
