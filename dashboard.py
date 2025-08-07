
import streamlit as st
import pandas as pd
import altair as alt

# Load CSV
df = pd.read_csv("data_scientist_jobs_israel.csv")

# Normalize Tel Aviv names
df["location"] = df["location"].apply(
    lambda x: "Tel Aviv" if isinstance(x, str) and "tel" in x.lower() and "aviv" in x.lower() else x
)

# Convert scraped_at to datetime (fix: read as day-first)
df["scraped_at"] = pd.to_datetime(df["scraped_at"], dayfirst=False, errors="coerce")
df = df.dropna(subset=["scraped_at"])

# Page config
st.set_page_config(page_title="Data Scientist Jobs in Israel", layout="wide")
st.title("🇮🇱 Data Scientist Jobs in Israel")
st.caption(f"Last updated: {df['scraped_at'].max().strftime('%d/%m/%Y %H:%M')}")

# Sidebar filters
st.sidebar.header("🔍 Filters")

min_date = df["scraped_at"].min().date()
max_date = df["scraped_at"].max().date()
date_range = st.sidebar.date_input("Scraped At Range", [min_date, max_date], min_value=min_date, max_value=max_date)

sources = st.sidebar.multiselect("Filter by Source", options=sorted(df["source"].dropna().unique()))
companies = st.sidebar.multiselect("Filter by Company", options=sorted(df["company"].dropna().unique()))
locations = st.sidebar.multiselect("Filter by Location", options=sorted(df["location"].dropna().unique()))

# Filtering
filtered_df = df.copy()
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["scraped_at"].dt.date >= start_date) &
        (filtered_df["scraped_at"].dt.date <= end_date)
    ]

if sources:
    filtered_df = filtered_df[filtered_df["source"].isin(sources)]
if companies:
    filtered_df = filtered_df[filtered_df["company"].isin(companies)]
if locations:
    filtered_df = filtered_df[filtered_df["location"].isin(locations)]

st.write(f"🔍 {len(filtered_df)} jobs after filtering")

# 📈 Chart of scrape counts over time (by scraping event)
st.markdown("## 📈 Jobs Per Scraping Event")

# Group by exact scraping timestamp and count jobs excluding "None"
def count_jobs_per_scrape(group):
    # Count only rows where title is a non-empty string and not "None"
    return group["title"].apply(lambda x: isinstance(x, str) and x.strip() != "" and x.strip().lower() != "none").sum()


scrape_counts = (
    filtered_df.groupby("scraped_at")
    .apply(count_jobs_per_scrape)
    .reset_index(name="Job Count")
    .sort_values("scraped_at")
)

# Add a formatted label for display
scrape_counts["Scraped At Label"] = scrape_counts["scraped_at"].dt.strftime("%d/%m/%Y %H:%M")

# Create Altair line chart with points and labels
chart = alt.Chart(scrape_counts).mark_line(point=True).encode(
    x=alt.X("Scraped At Label:N", title="Scraping Timestamp", axis=alt.Axis(labelAngle=0)),  # horizontal
    y=alt.Y("Job Count:Q", title="Jobs Scraped"),
    tooltip=["Scraped At Label", "Job Count"]
).properties(width=900, height=400)

# Add job count text labels above points
text = alt.Chart(scrape_counts).mark_text(
    align='center',
    baseline='bottom',
    dy=-5
).encode(
    x=alt.X("Scraped At Label:N", sort=None),
    y="Job Count:Q",
    text="Job Count:Q"
)

st.altair_chart(chart + text, use_container_width=True)

# 📋 Job Listings Table

# Filter out invalid job titles (like "None", empty, or NaN)
def is_valid_title(title):
    return isinstance(title, str) and title.strip() != "" and title.strip().lower() != "none"

table_df = filtered_df[filtered_df["title"].apply(is_valid_title)].copy()

table_df["title"] = table_df.apply(
    lambda row: f'<a href="{row["link"]}" target="_blank">{row["title"]}</a>', axis=1
)
table_df = table_df.drop(columns=["link"])
table_df.rename(columns={"scraped_at": "Scraped At", "title": "Job Title"}, inplace=True)

st.markdown("## 📋 Job Listings")
if not table_df.empty:
    st.write("Click on job titles to open listings:")
    st.markdown(table_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("No jobs to show based on current filters.")
