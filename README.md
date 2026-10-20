# Healthcare Intelligence Hub: Patient, Cost & Care Analytics

An end-to-end analytics project on **Snowflake**. It turns raw hospital patient-visit data into a layered warehouse (`RAW → STAGING → CURATED → MART`) and an interactive **Streamlit in Snowflake** dashboard for operations, finance and care-quality teams.

---

## 1. Business Problem

Hospital data is spread across patient registration, doctors, facilities, diagnoses, treatments, billing, insurance and feedback. Without a common analytical structure, management cannot quickly answer basic questions:

- Which facilities, departments and diagnoses generate the most visits, and how is volume changing over time?
- Where are healthcare costs rising, and how much is covered by insurance versus paid by the patient?
- How satisfied are patients, how long do they stay, and how many are readmitted within 30 days?

**Goal:** consolidate the source CSVs into one well-modelled warehouse, track visit volume, cost and length of stay across time, facility, doctor and diagnosis, monitor satisfaction and 30-day readmissions as quality indicators, and deliver the insights through a filterable Streamlit app.

## 2. Users and Use Cases

| Persona | Role | What they need |
|---|---|---|
| **Priya Sharma** | Operations Administrator | Monthly visit trend, facility load, visit type and admission status split, length of stay, to plan staff and beds |
| **Rohan Verma** | Finance & Billing Manager | Cost by facility and visit type (consultation, medication, lab, room), total cost vs insurance coverage vs patient payment |
| **Meera Iyer** | Care Quality Manager | Satisfaction by doctor and facility, readmission rate by diagnosis, length of stay |

## 3. Tech Stack

- **Snowflake** (database, schemas, file format, internal stage, views)
- **SQL** (cleaning, modelling and KPI views)
- **Streamlit in Snowflake** (dashboard, using Snowpark, pandas and Altair)
- **Snowflake CLI** project definition (`snowflake.yml`) for the Streamlit app

## 4. Project Structure

```
.
├── patients.csv               # source data (6 CSV files)
├── doctors.csv
├── facilities.csv
├── diagnoses.csv
├── date.csv
├── patient_visits.csv
├── query.sql                  # full SQL pipeline: setup, RAW, STAGING, CURATED, MART views
├── Health/                    # Streamlit in Snowflake app
│   ├── streamlit_app.py       # dashboard
│   ├── snowflake.yml          # Snowflake CLI app definition (HEALTH_DB.RAW, COMPUTE_WH)
│   ├── pyproject.toml         # Python 3.11, streamlit[snowflake]
│   └── .streamlit/config.toml # Streamlit theme config
└── README.md
```

## 5. Dataset

Six CSV files: one fact source and five dimension sources.

| File | Rows | Description |
|---|---|---|
| `patients.csv` | 3,000 | Name, gender, date of birth, city, insurance provider, registration date |
| `doctors.csv` | 60 | Doctor name, specialty, years of experience, department |
| `facilities.csv` | 10 | Facility name, city, facility type |
| `diagnoses.csv` | 15 | Diagnosis name and category |
| `date.csv` | 974 | Calendar attributes (year, quarter, month, month name, week, day of week, weekend flag) |
| `patient_visits.csv` | 10,000 | One row per visit: visit type, admission and treatment status, length of stay, cost breakdown, insurance coverage, patient payment, satisfaction, 30-day readmission |

## 6. Architecture

```
CSV files
   |  (upload to HEALTHCARE_STAGE / load into tables)
   v
RAW        *_RAW tables, typed columns, loaded as-is
   |  (trim, standardize casing, drop null keys)
   v
STAGING    PATIENTS, DOCTORS, FACILITIES, DIAGNOSES, DATE, PATIENT_VISITS
   |  (model)
   v
CURATED    DIM_* tables + FACT_PATIENT_VISITS (denormalized fact)
   |
   +--> MART      VW_* KPI views
   |
   +--> Streamlit dashboard (reads CURATED.FACT_PATIENT_VISITS)
```

**Snowflake objects**

| Object | Name |
|---|---|
| Warehouse | `COMPUTE_WH` |
| Database | `HEALTH_DB` |
| Schemas | `RAW`, `STAGING`, `CURATED`, `MART` |
| File format | `HEALTH_DB.RAW.CSV_FORMAT` (CSV, header skipped, `YYYY-MM-DD` dates) |
| Stage | `HEALTH_DB.RAW.HEALTHCARE_STAGE` |
| Streamlit app | `HEALTH` (in `HEALTH_DB.RAW`) |

## 7. Data Model

**Dimensions (`CURATED`)**

| Table | Key | Attributes |
|---|---|---|
| `DIM_PATIENT` | `PATIENT_ID` | first/last name, gender, date of birth, city, insurance provider, registration date |
| `DIM_DOCTOR` | `DOCTOR_ID` | doctor name, specialty, experience years, department |
| `DIM_FACILITY` | `FACILITY_ID` | facility name, city, facility type |
| `DIM_DIAGNOSIS` | `DIAGNOSIS_ID` | diagnosis name, diagnosis category |
| `DIM_DATE` | `DATE` | year, quarter, month, month name, week, day of week, weekend flag |

**`FACT_PATIENT_VISITS`** (grain: one row per visit): visit, patient, doctor, facility and diagnosis IDs; visit date; visit type, admission status, treatment status; length of stay; consultation, medication, lab, room and total cost; insurance coverage; patient payment; satisfaction score; 30-day readmission (Yes/No). It is denormalized with patient, doctor, facility and diagnosis attributes (e.g. `PATIENT_CITY`, `SPECIALTY`, `FACILITY_NAME`, `DIAGNOSIS_CATEGORY`) so that views and the dashboard can query it without joins.

## 8. Transformations

**RAW → STAGING**
- Trim whitespace on all ID and text columns.
- Standardize casing with `INITCAP` (gender, city, specialty, department, facility type, diagnosis category, visit type, admission/treatment status, readmission flag).
- Drop rows with a null primary key.

**STAGING → CURATED**
- Build `DIM_*` tables with `SELECT DISTINCT`.
- Build `FACT_PATIENT_VISITS` by left-joining visits to patients, doctors, facilities and diagnoses.

**Validation queries (in `query.sql`)**
- Row counts for RAW, STAGING and CURATED tables.
- Null-key and duplicate-key checks in STAGING.
- Orphan checks on the fact table (unmatched patient, doctor, facility, diagnosis).

## 9. KPI Views (`HEALTH_DB.MART`)

| View | What it shows |
|---|---|
| `VW_EXECUTIVE_KPI` | Total visits, patients, doctors, facilities, cost, insurance coverage, patient payment, avg satisfaction, avg length of stay, readmissions |
| `VW_MONTHLY_VISITS` | Visits, cost and avg satisfaction per month |
| `VW_DIAGNOSIS_ANALYTICS` | Visits, avg cost, avg length of stay and satisfaction per diagnosis |
| `VW_FACILITY_ANALYTICS` | Visits, total and avg cost, satisfaction and length of stay per facility |
| `VW_VISIT_TYPE_DISTRIBUTION` | Visits, avg cost, satisfaction and length of stay per visit type |
| `VW_TREATMENT_ANALYTICS` | Visits, avg cost and satisfaction per treatment status |
| `VW_ADMISSION_STATUS_ANALYTICS` | Visits and avg cost per admission status |
| `VW_PATIENT_VISIT_TYPE_ANALYSIS` | Visit type metrics ordered by avg visit cost |
| `VW_DOCTOR_ANALYTICS` | Visits, avg cost, satisfaction and readmissions per doctor |
| `VW_READMISSION_ANALYTICS` | Readmissions and readmission rate (%) per diagnosis |

## 10. Streamlit Dashboard

`Health/streamlit_app.py` reads `HEALTH_DB.CURATED.FACT_PATIENT_VISITS` through the active Snowpark session (cached for 10 minutes).

**Sidebar filters:** date range, facility, doctor specialty, visit type, diagnosis category.

**Sections**
- KPI cards: total visits, unique patients, total cost, avg satisfaction, readmission rate, avg length of stay
- Monthly visit trend and visit type split
- Top 10 diagnoses by volume and admission status
- Facility performance (chart and table)
- Treatment status and readmission rate by diagnosis
- Average cost breakdown (consultation, medication, lab, room) by visit type
- Doctor performance leaderboard

## 11. How to Run

1. **Set up Snowflake:** open a SQL worksheet in Snowsight with a role that can create databases (e.g. `ACCOUNTADMIN`) and use `COMPUTE_WH`.
2. **Create objects:** run the first part of `query.sql` to create `HEALTH_DB`, the four schemas, the `*_RAW` tables, `CSV_FORMAT` and `HEALTHCARE_STAGE`.
3. **Load data:** upload the 6 CSVs to `HEALTHCARE_STAGE` (or use Snowsight *Load Data*) and load each into its `*_RAW` table using `CSV_FORMAT`.
4. **Validate RAW:** row counts should be 3,000 / 60 / 10 / 15 / 974 / 10,000 (patients, doctors, facilities, diagnoses, date, visits).
5. **Build the pipeline:** run the rest of `query.sql` in order: STAGING tables and checks, CURATED dimensions and fact, then MART views. Null, duplicate and orphan checks should all return 0.
6. **Deploy the dashboard:** either create a Streamlit app in Snowsight (Projects > Streamlit) on `COMPUTE_WH` and paste `Health/streamlit_app.py`, or deploy with the Snowflake CLI from the `Health/` folder:
   ```bash
   cd Health
   snow streamlit deploy --replace
   ```

## 12. Project Status

| Epic | Status |
|---|---|
| 1. Problem definition and data collection | Done |
| 2. Data architecture setup | Done |
| 3. Data ingestion (RAW) | Done |
| 4. Staging | Done |
| 5. Curated model | Done |
| 6. Business analytics (KPI views) | Done |
| 7. Streamlit app | Done |
| 8. Performance testing, demo and documentation | Pending |

## 13. Demo and Documentation

- Demo video: _link to be added_
- Step-by-step development documentation: _link to be added_

## 14. Author

**Aashi Bindal**
