    
import pandas as pd
import numpy as np
import streamlit as st

# ---------- Settings ----------
BASE = "/Projects/memory_care_meals"
st.set_page_config(page_title="Memory Care Meals — Dashboard", layout="wide")

@st.cache_data
def load_data():
    residents = pd.read_csv(f"{BASE}/residents.csv")
    daily = None
    checks = None
    try:
        daily = pd.read_csv(f"{BASE}/daily_summary_with_plate_counts.csv")
    except Exception:
        pass
    try:
        checks = pd.read_csv(f"{BASE}/daily_checks_with_plate_counts.csv")
    except Exception:
        pass
    return residents, daily, checks

residents, daily, checks = load_data()

st.title("Memory Care Meals — Cost, Nutrition & Waste")

# ---------- Guards ----------
if daily is None:
    st.info("Run your plate-count analysis first to generate `daily_summary_with_plate_counts.csv` (e.g., `analyze_plate_counts_fixed.py`).")
    st.stop()

# Ensure proper types
if "day" in daily.columns:
    try:
        daily["day"] = pd.to_datetime(daily["day"])
    except Exception:
        pass

# ---------- Sidebar Filters ----------
with st.sidebar:
    st.header("Filters")
    min_day = pd.to_datetime(daily["day"]).min()
    max_day = pd.to_datetime(daily["day"]).max()
    date_range = st.date_input(
        "Date range",
        value=(min_day.date(), max_day.date()),
        min_value=min_day.date(),
        max_value=max_day.date(),
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        mask = (pd.to_datetime(daily["day"]) >= start) & (pd.to_datetime(daily["day"]) <= end)
        daily_view = daily.loc[mask].copy()
    else:
        daily_view = daily.copy()

# ---------- Top KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Residents", len(residents))
if "approx_cost_per_resident_day_usd" in daily_view.columns:
    c2.metric("Avg Cost / Resident-Day (USD)", f"{daily_view['approx_cost_per_resident_day_usd'].mean():.2f}")
if "waste_pct" in daily_view.columns:
    c3.metric("Avg Waste %", f"{(daily_view['waste_pct'].mean()*100):.1f}%")
c4.metric("Days in View", len(daily_view))

tabs = st.tabs(["Cost", "Nutrition", "Compliance", "Waste", "Data"])

# ---------- Cost Tab ----------
with tabs[0]:
    st.subheader("Approx Cost per Resident-Day (USD)")
    if "approx_cost_per_resident_day_usd" in daily_view.columns:
        st.line_chart(daily_view.set_index("day")[["approx_cost_per_resident_day_usd"]])
    else:
        st.warning("Column 'approx_cost_per_resident_day_usd' not found in daily summary.")

# ---------- Nutrition Tab ----------
with tabs[1]:
    st.subheader("Daily Nutrition Totals")
    cols = [c for c in ["calories_kcal","protein_g","carbs_g","fat_g","sodium_mg","fiber_g"] if c in daily_view.columns]
    if cols:
        st.line_chart(daily_view.set_index("day")[cols])
    else:
        st.info("Nutrition columns not found in daily summary.")
    if cols:
        with st.expander("Summary Stats"):
            st.dataframe(daily_view[cols].describe().round(2))

# ---------- Compliance Tab ----------
with tabs[2]:
    st.subheader("Daily Compliance")
    if checks is None:
        st.info("`daily_checks_with_plate_counts.csv` not found. Run the robust analysis/notebook to generate it.")
    else:
        # Align date type
        try:
            checks["day"] = pd.to_datetime(checks["day"])
        except Exception:
            pass
        # Filter checks to date range if possible
        if checks["day"].dtype.kind in "M":
            cmask = (checks["day"] >= pd.to_datetime(daily_view["day"].min())) & (checks["day"] <= pd.to_datetime(daily_view["day"].max()))
            cview = checks.loc[cmask].copy()
        else:
            cview = checks.copy()
        st.dataframe(cview)
        # Simple pass rate
        bool_cols = [c for c in cview.columns if c.endswith("_ok")]
        if bool_cols:
            pass_rate = cview[bool_cols].mean().mean() * 100
            st.metric("Overall pass rate", f"{pass_rate:.1f}%")

# ---------- Waste Tab ----------
with tabs[3]:
    st.subheader("Waste (%)")
    if "waste_pct" in daily_view.columns:
        st.line_chart(daily_view.set_index("day")[["waste_pct"]])
        with st.expander("Waste table"):
            tmp = daily_view[["day","prepared","served","leftover","waste_pct"]].copy()
            tmp["waste_pct"] = (tmp["waste_pct"] * 100).round(1)
            st.dataframe(tmp)
    else:
        st.info("No waste data found.")

# ---------- Data Tab ----------
with tabs[4]:
    st.subheader("Download data")
    st.download_button("Download daily summary (CSV)", data=daily.to_csv(index=False), file_name="daily_summary_with_plate_counts.csv")
    if checks is not None:
        st.download_button("Download compliance checks (CSV)", data=checks.to_csv(index=False), file_name="daily_checks_with_plate_counts.csv")
    with st.expander("Preview daily data"):
        st.dataframe(daily_view)

st.caption("Tip: Re-run the analysis script/notebook whenever you update the CSVs in '/Projects/memory_care_meals'.")
