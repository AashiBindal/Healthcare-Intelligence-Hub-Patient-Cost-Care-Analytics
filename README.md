# Healthcare Intelligence Hub: Patient, Cost & Care Analytics

An end-to-end analytics project on **Snowflake**. It turns raw hospital patient-visit data into a clean, snowflake-schema warehouse and an interactive **Streamlit** dashboard for operations, finance and care-quality teams.

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
| **Rohan Verma** | Finance & Billing Manager | Cost by facility and visit type (consultation, medication, lab, room), total cost vs insurance coverage vs patient payment, cost growth vs visit growth |
| **Meera Iyer** | Care Quality Manager | Satisfaction by doctor and facility, length of stay by diagnosis vs readmission, to spot early or late discharges |

## 3. Tech Stack

- **Snowflake** (warehouse, stages, SQL, views)
- **SQL** (transformation and modelling)
- **Snowflake Schema** (normalized dimensional model)
- **Streamlit in Snowflake** (dashboard)

## 4. Dataset

Six CSV files: one fact table and five dimension sources.

| File | Rows | Description |
|---|---|---|
| `patients.csv` | 3,000 | Demographics, city, insurance provider, registration date |
| `doctors.csv` | 60 | Doctor name, specialty, years of experience, department |
| `facilities.csv` | 10 | Facility name, city, facility type |
| `diagnoses.csv` | 15 | Diagnosis name and category |
| `date_1.csv` | 974 | Calendar attributes (year, quarter, month, week, day of week, weekend flag) |
| `patient_visits.csv` | 10,000 | One row per visit: visit type, admission and treatment status, length of stay, cost breakdown, insurance coverage, patient payment, satisfaction, 30-day readmission |

**Source data checks:** no nulls, no duplicate keys, no orphan foreign keys, `total_cost` equals the sum of its four components, and `insurance_coverage + patient_payment = total_cost` on every row.

## 5. Architecture

```
CSV files
   |  (PUT / upload to internal stage)
   v
RAW        raw_* tables, all STRING, loaded as-is
   |  (clean, cast, derive)
   v
STAGING    stg_* tables, typed and standardized
   |  (model)
   v
CURATED    dim_* and fact_visits (snowflake schema) + KPI views
   |
   v
Streamlit dashboard (Operations | Finance | Quality)
```

**Snowflake objects**

| Object | Name |
|---|---|
| Warehouse | `HEALTHCARE_WH` (XSMALL, auto-suspend 60s) |
| Database | `HEALTHCARE_DB` |
| Schemas | `RAW`, `STAGING`, `CURATED` |
| File format | `CSV_FORMAT` |
| Stage | `HEALTHCARE_STAGE` |

## 6. Data Model (Snowflake Schema)

Dimensions are normalized into sub-dimensions.

```
dim_department <-- dim_doctor ----\
dim_city <------- dim_facility ----\
dim_city <------- dim_patient ------>  fact_visits
dim_diagnosis_category <-- dim_diagnosis --/
dim_insurance ---------------------/
dim_date -------------------------/
```

**`fact_visits`** (grain: one row per visit): visit, patient, doctor, facility, diagnosis, insurance and date keys; visit type, admission status, treatment status; length of stay; consultation, medication, lab, room and total cost; insurance coverage; patient payment; satisfaction score; 30-day readmission flag.

## 7. Project Structure

```
.
├── data/                          # source CSV files
├── sql/
│   ├── 01_setup_and_ingestion.sql # warehouse, database, schemas, stage, RAW tables, COPY INTO, validation
│   ├── 02_staging.sql             # cleaning and typing
│   ├── 03_curated_model.sql       # dimensions and fact table
│   └── 04_kpi_views.sql           # analytics views
├── streamlit/
│   └── streamlit_app.py           # dashboard
├── screenshots/
└── README.md
```

## 8. How to Run

1. **Set up Snowflake:** create a Snowflake account (trial is fine) and open a SQL file in Snowsight with the `ACCOUNTADMIN` role.
2. **Architecture and ingestion:** run `sql/01_setup_and_ingestion.sql`. Upload the 6 CSVs to `HEALTHCARE_STAGE` when the script reaches the manual step (Data > Databases > HEALTHCARE_DB > RAW > Stages > HEALTHCARE_STAGE > + Files), then run the `COPY INTO` and validation sections.
3. **Validate:** row counts should be 10 / 15 / 60 / 974 / 3,000 / 10,000, and the duplicate and orphan checks should all return 0.
4. **Staging, model and views:** run `02_staging.sql`, `03_curated_model.sql` and `04_kpi_views.sql` in order.
5. **Dashboard:** create a Streamlit app in Snowsight (Projects > Streamlit), choose `HEALTHCARE_WH` and `HEALTHCARE_DB.CURATED`, and paste `streamlit_app.py`.

## 9. Transformations (RAW to STAGING)

- Cast text columns to proper types (dates, integers, decimals).
- Standardize text (trim, consistent casing).
- Convert `readmission_within_30_days` from Yes/No to a 1/0 flag.
- Derive new fields such as patient age, visit year-month and insurance coverage percentage.
- Deduplicate on the visit ID and enforce key integrity.

## 10. KPIs and Dashboard

**Operations (Priya)**
- Monthly visit trend
- Visits and average length of stay by facility
- Distribution by visit type and admission status

**Finance (Rohan)**
- Cost by facility and visit type, split into consultation, medication, lab and room
- Total cost vs insurance coverage vs patient payment, with insurance coverage %
- Month-over-month cost growth vs visit growth per facility

**Quality (Meera)**
- Average satisfaction by doctor, department and facility
- 30-day readmission rate
- Average length of stay by diagnosis vs readmission rate

All views are filterable by facility, visit type and date range.

## 11. Performance Testing

| Test | Method |
|---|---|
| Amount of data loaded | Row counts for RAW, STAGING and each CURATED table |
| Filter efficiency | Compare elapsed time and partitions scanned with and without filters (Query Profile) |
| New fields created | List of derived columns added in STAGING and CURATED |
| Query history | `INFORMATION_SCHEMA.QUERY_HISTORY` (elapsed time, bytes scanned, rows produced) |

Results and screenshots: _to be added in `screenshots/`_.

## 12. Project Status

| Epic | Status |
|---|---|
| 1. Problem definition and data collection | Done |
| 2. Data architecture setup | In progress |
| 3. Data ingestion (RAW) | In progress |
| 4. Staging | Pending |
| 5. Curated model | Pending |
| 6. Business analytics (KPI views) | Pending |
| 7. Streamlit app | Pending |
| 8. Performance testing, demo and documentation | Pending |

## 13. Demo and Documentation

- Demo video: _link to be added_
- Step-by-step development documentation: _link to be added_

## 14. Author

**Aashi Bindal**