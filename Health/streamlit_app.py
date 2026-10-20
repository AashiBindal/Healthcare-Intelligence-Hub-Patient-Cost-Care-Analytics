import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="Healthcare Intelligence Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Connection (Snowflake native session) ─────────────────────
@st.cache_data(ttl=600)
def load_fact():
    session = get_active_session()
    df = session.table("HEALTH_DB.CURATED.FACT_PATIENT_VISITS").to_pandas()
    df.columns = df.columns.str.upper()
    df["VISIT_DATE"] = pd.to_datetime(df["VISIT_DATE"])
    return df

df_raw = load_fact()

# ── Sidebar Filters ───────────────────────────────────────────
st.sidebar.title("Filters")

date_min = df_raw["VISIT_DATE"].min().date()
date_max = df_raw["VISIT_DATE"].max().date()
date_range = st.sidebar.date_input(
    "Date Range", [date_min, date_max],
    min_value=date_min, max_value=date_max
)

facilities  = ["All"] + sorted(df_raw["FACILITY_NAME"].dropna().unique().tolist())
specialties = ["All"] + sorted(df_raw["SPECIALTY"].dropna().unique().tolist())
visit_types = ["All"] + sorted(df_raw["VISIT_TYPE"].dropna().unique().tolist())
diag_cats   = ["All"] + sorted(df_raw["DIAGNOSIS_CATEGORY"].dropna().unique().tolist())

sel_facility  = st.sidebar.selectbox("Facility",           facilities)
sel_specialty = st.sidebar.selectbox("Doctor Specialty",   specialties)
sel_visit     = st.sidebar.selectbox("Visit Type",         visit_types)
sel_diag_cat  = st.sidebar.selectbox("Diagnosis Category", diag_cats)

# ── Apply Filters ─────────────────────────────────────────────
df = df_raw.copy()
if len(date_range) == 2:
    df = df[
        (df["VISIT_DATE"].dt.date >= date_range[0]) &
        (df["VISIT_DATE"].dt.date <= date_range[1])
    ]
if sel_facility  != "All": df = df[df["FACILITY_NAME"]      == sel_facility]
if sel_specialty != "All": df = df[df["SPECIALTY"]          == sel_specialty]
if sel_visit     != "All": df = df[df["VISIT_TYPE"]         == sel_visit]
if sel_diag_cat  != "All": df = df[df["DIAGNOSIS_CATEGORY"] == sel_diag_cat]

# ── Header ────────────────────────────────────────────────────
st.title("Healthcare Intelligence Hub")
st.caption("Patient, Cost & Care Analytics")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────
total_visits   = len(df)
total_patients = df["PATIENT_ID"].nunique()
total_cost     = df["TOTAL_COST"].sum()
avg_sat        = df["PATIENT_SATISFACTION"].mean() if total_visits > 0 else 0
readmit_rate   = (
    100 * (df["READMISSION_WITHIN_30_DAYS"] == "Yes").sum() / total_visits
    if total_visits > 0 else 0
)
avg_los = df["LENGTH_OF_STAY_DAYS"].mean() if total_visits > 0 else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Visits",       f"{total_visits:,}")
c2.metric("Unique Patients",    f"{total_patients:,}")
c3.metric("Total Cost",         f"${total_cost:,.0f}")
c4.metric("Avg Satisfaction",   f"{avg_sat:.2f} / 5")
c5.metric("Readmission Rate",   f"{readmit_rate:.1f}%")
c6.metric("Avg Length of Stay", f"{avg_los:.2f} days")

st.divider()

# ── Row 1: Monthly Trend + Visit Type Split ───────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Monthly Visit Trend")
    monthly = (
        df.groupby(df["VISIT_DATE"].dt.to_period("M"))
        .agg(TOTAL_VISITS=("VISIT_ID", "count"))
        .reset_index()
    )
    monthly["VISIT_DATE"] = monthly["VISIT_DATE"].dt.to_timestamp()
    chart = alt.Chart(monthly).mark_line(point=True).encode(
        x=alt.X("VISIT_DATE:T", title="Month"),
        y=alt.Y("TOTAL_VISITS:Q", title="Total Visits")
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("Visit Type Split")
    vt = df.groupby("VISIT_TYPE")["VISIT_ID"].count().reset_index()
    vt.columns = ["VISIT_TYPE", "COUNT"]
    chart = alt.Chart(vt).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("COUNT:Q"),
        color=alt.Color("VISIT_TYPE:N", title="Visit Type"),
        tooltip=["VISIT_TYPE", "COUNT"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

# ── Row 2: Top Diagnoses + Admission Status ───────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Top 10 Diagnoses by Volume")
    diag = (
        df.groupby("DIAGNOSIS_NAME")["VISIT_ID"].count()
        .reset_index()
        .rename(columns={"VISIT_ID": "VISITS"})
        .sort_values("VISITS", ascending=False)
        .head(10)
    )
    chart = alt.Chart(diag).mark_bar().encode(
        x=alt.X("VISITS:Q", title="Total Visits"),
        y=alt.Y("DIAGNOSIS_NAME:N", sort="-x", title=""),
        tooltip=["DIAGNOSIS_NAME", "VISITS"]
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("Admission Status")
    adm = df.groupby("ADMISSION_STATUS")["VISIT_ID"].count().reset_index()
    adm.columns = ["STATUS", "COUNT"]
    chart = alt.Chart(adm).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("COUNT:Q"),
        color=alt.Color("STATUS:N", title="Status"),
        tooltip=["STATUS", "COUNT"]
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

# ── Row 3: Facility Performance ───────────────────────────────
st.subheader("Facility Performance")
facility_df = (
    df.groupby(["FACILITY_NAME", "FACILITY_CITY", "FACILITY_TYPE"])
    .agg(
        TOTAL_VISITS    =("VISIT_ID",            "count"),
        TOTAL_COST      =("TOTAL_COST",          "sum"),
        AVG_COST        =("TOTAL_COST",          "mean"),
        AVG_SATISFACTION=("PATIENT_SATISFACTION","mean"),
        AVG_LOS         =("LENGTH_OF_STAY_DAYS", "mean"),
    )
    .reset_index()
    .sort_values("TOTAL_VISITS", ascending=False)
    .round(2)
)

col1, col2 = st.columns([1, 1])
with col1:
    chart = alt.Chart(facility_df).mark_bar().encode(
        x=alt.X("FACILITY_NAME:N", sort="-y", title="", axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("TOTAL_VISITS:Q", title="Total Visits"),
        color=alt.Color("FACILITY_TYPE:N", title="Type"),
        tooltip=["FACILITY_NAME", "FACILITY_TYPE", "TOTAL_VISITS", "AVG_COST"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
with col2:
    st.dataframe(
        facility_df[["FACILITY_NAME", "FACILITY_CITY", "FACILITY_TYPE",
                     "TOTAL_VISITS", "AVG_COST", "AVG_SATISFACTION"]],
        use_container_width=True, hide_index=True
    )

# ── Row 4: Treatment Status + Readmission Rate ────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Treatment Status")
    treat = df.groupby("TREATMENT_STATUS")["VISIT_ID"].count().reset_index()
    treat.columns = ["STATUS", "COUNT"]
    chart = alt.Chart(treat).mark_bar().encode(
        x=alt.X("STATUS:N", title="Treatment Status"),
        y=alt.Y("COUNT:Q", title="Total Visits"),
        tooltip=["STATUS", "COUNT"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("Readmission Rate by Diagnosis")
    readm = df.groupby("DIAGNOSIS_NAME").agg(
        TOTAL       =("VISIT_ID", "count"),
        READMISSIONS=("READMISSION_WITHIN_30_DAYS", lambda x: (x == "Yes").sum())
    ).reset_index()
    readm["READMISSION_RATE_PCT"] = (100 * readm["READMISSIONS"] / readm["TOTAL"]).round(2)
    readm = readm.sort_values("READMISSION_RATE_PCT", ascending=False).head(10)
    chart = alt.Chart(readm).mark_bar().encode(
        x=alt.X("READMISSION_RATE_PCT:Q", title="Readmission Rate (%)"),
        y=alt.Y("DIAGNOSIS_NAME:N", sort="-x", title=""),
        tooltip=["DIAGNOSIS_NAME", "READMISSION_RATE_PCT", "READMISSIONS"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

# ── Row 5: Cost Breakdown by Visit Type ──────────────────────
st.subheader("Average Cost Breakdown by Visit Type")
cost_cols = ["CONSULTATION_COST", "MEDICATION_COST", "LAB_COST", "ROOM_COST"]
cost_df = df.groupby("VISIT_TYPE")[cost_cols].mean().round(2).reset_index()
cost_melted = cost_df.melt(id_vars="VISIT_TYPE", var_name="COST_TYPE", value_name="AVG_COST")
chart = alt.Chart(cost_melted).mark_bar().encode(
    x=alt.X("VISIT_TYPE:N", title="Visit Type"),
    y=alt.Y("AVG_COST:Q", title="Avg Cost ($)"),
    color=alt.Color("COST_TYPE:N", title="Cost Type"),
    tooltip=["VISIT_TYPE", "COST_TYPE", "AVG_COST"]
).properties(height=300)
st.altair_chart(chart, use_container_width=True)

# ── Row 6: Doctor Leaderboard ─────────────────────────────────
st.subheader("Doctor Performance Leaderboard")
doctor_df = (
    df.groupby(["DOCTOR_NAME", "SPECIALTY", "DEPARTMENT"])
    .agg(
        TOTAL_VISITS    =("VISIT_ID",                   "count"),
        AVG_COST        =("TOTAL_COST",                 "mean"),
        AVG_SATISFACTION=("PATIENT_SATISFACTION",       "mean"),
        READMISSIONS    =("READMISSION_WITHIN_30_DAYS", lambda x: (x == "Yes").sum())
    )
    .reset_index()
    .sort_values("TOTAL_VISITS", ascending=False)
    .round(2)
)
st.dataframe(doctor_df, use_container_width=True, hide_index=True)

st.divider()
st.caption(f"Data filtered to {total_visits:,} visits | HEALTH_DB.CURATED.FACT_PATIENT_VISITS")
