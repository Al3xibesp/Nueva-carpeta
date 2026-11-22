# Import the standard library and third-party packages used by the dashboard.
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Build the path to the Excel data file relative to this script.
# This ensures the app can find the file even when launched from another folder.
DATA_PATH = Path(__file__).parent / "data" / "sellers.xlsx"

# Configure the browser page title, icon, and full-width layout.
st.set_page_config(page_title="Sellers Dashboard", page_icon="📊", layout="wide")


# Cache the data-loading function so Streamlit only reloads it when the path changes.
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    # Read seller records from the Excel worksheet into a pandas DataFrame.
    df = pd.read_excel(path)

    # Combine the first and last name columns to create a single seller name.
    df["SELLER"] = df["NAME"].str.strip() + " " + df["LASTNAME"].str.strip()

    # IDs are not always unique, so include the seller name and region in the label.
    df["LABEL"] = df["SELLER"] + " (ID " + df["ID"].astype(str) + ", " + df["REGION"] + ")"
    return df


# Load the seller data once and reuse the resulting DataFrame below.
df = load_data(DATA_PATH)

# Display the main heading at the top of the dashboard.
st.title("📊 Sellers Dashboard")

# ---------- Sidebar filter ----------
# Find and sort all available regions for the sidebar options.
regions = sorted(df["REGION"].unique())

# Let the user choose one or more regions; all regions are selected initially.
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

# Stop the dashboard if no region is selected and show instructions to the user.
if not selected_regions:
    st.warning("Select at least one region in the sidebar.")
    st.stop()

# Keep only the rows that belong to the regions selected in the sidebar.
fdf = df[df["REGION"].isin(selected_regions)]

# Create three top-level tabs: a summary table, charts, and an individual vendor view.
tab_overview, tab_charts, tab_vendor = st.tabs(["Table", "Charts", "Vendor"])

# ---------- Table ----------
# The overview tab shows key totals and the filtered seller records.
with tab_overview:
    # Create four metric columns to summarize the filtered data.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sellers", f"{len(fdf):,}")
    c2.metric("Units sold", f"{fdf['SOLD UNITS'].sum():,}")
    c3.metric("Total sales", f"${fdf['TOTAL SALES'].sum():,}")
    c4.metric("Avg sales per seller", f"${fdf['TOTAL SALES'].mean():,.0f}")

    # Display the filtered table and remove helper columns used for dashboard labels.
    st.dataframe(
        fdf.drop(columns=["SELLER", "LABEL"]),
        width="stretch",
        hide_index=True,
        # Format currency and percentage columns for easier reading.
        column_config={
            "INCOME": st.column_config.NumberColumn(format="$%d"),
            "TOTAL SALES": st.column_config.NumberColumn(format="$%d"),
            "SALES AVERAGE": st.column_config.NumberColumn(format="percent"),
        },
    )

# ---------- Charts ----------
# The charts tab compares seller performance across regions and metrics.
with tab_charts:
    # Aggregate sales and units by region for the regional summary charts.
    by_region = (
        fdf.groupby("REGION")
        .agg(units=("SOLD UNITS", "sum"), sales=("TOTAL SALES", "sum"), avg=("TOTAL SALES", "mean"))
        .reset_index()
    )

    # Create three side-by-side charts for units, sales, and average sales.
    col1, col2, col3 = st.columns(3)
    col1.plotly_chart(
        px.bar(by_region, x="REGION", y="units", color="REGION", title="Units Sold by Region",
               labels={"units": "Units sold"}),
        width="stretch",
    )
    col2.plotly_chart(
        px.bar(by_region, x="REGION", y="sales", color="REGION", title="Total Sales by Region",
               labels={"sales": "Total sales"}),
        width="stretch",
    )
    col3.plotly_chart(
        px.bar(by_region, x="REGION", y="avg", color="REGION", title="Average Sales per Seller by Region",
               labels={"avg": "Average sales"}),
        width="stretch",
    )

    # Add a seller-level chart with a selectable performance metric.
    st.subheader("By seller")
    metric = st.radio(
        "Metric",
        ["SOLD UNITS", "TOTAL SALES", "SALES AVERAGE"],
        horizontal=True,
    )

    # Sort sellers from highest to lowest for the selected metric.
    sdf = fdf.sort_values(metric, ascending=False)

    # Build a bar chart and color each bar by its seller region.
    fig = px.bar(sdf, x="SELLER", y=metric, color="REGION", title=f"{metric.title()} by seller")

    # Format sales-average values as percentages and explain their meaning.
    if metric == "SALES AVERAGE":
        fig.update_yaxes(tickformat=".0%")
        st.caption("SALES AVERAGE is each seller's share of their region's total sales.")
    st.plotly_chart(fig, width="stretch")

# ---------- Vendor ----------
# The vendor tab provides a detailed view for one selected seller.
with tab_vendor:
    # Let the user select a seller by the descriptive unique label.
    label = st.selectbox("Choose a vendor", fdf.sort_values("SELLER")["LABEL"])

    # Retrieve the complete row for the selected seller.
    v = fdf[fdf["LABEL"] == label].iloc[0]

    # Get all sellers in the selected vendor's region for comparisons.
    region_df = df[df["REGION"] == v["REGION"]]

    # Show the selected seller's name and identifying information.
    st.subheader(v["SELLER"])
    st.caption(f"ID {v['ID']} · Region {v['REGION']}")

    # Compare four key metrics: income, units, sales, and regional sales share.
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Income", f"${v['INCOME']:,}")
    m2.metric(
        "Units sold", f"{v['SOLD UNITS']:,}",
        f"{v['SOLD UNITS'] - region_df['SOLD UNITS'].mean():+,.0f} vs region avg",
    )
    m3.metric(
        "Total sales", f"${v['TOTAL SALES']:,}",
        f"{v['TOTAL SALES'] - region_df['TOTAL SALES'].mean():+,.0f} vs region avg",
    )
    m4.metric("Share of region sales", f"{v['SALES AVERAGE']:.1%}")

    # Calculate and display the seller's rank within their region by total sales.
    rank = int(region_df["TOTAL SALES"].rank(ascending=False)[v.name])
    st.write(f"Ranks **#{rank} of {len(region_df)}** in {v['REGION']} by total sales.")

    # Create a comparison table containing vendor values and regional averages.
    compare = pd.DataFrame(
        {
            "Metric": ["Units sold", "Units sold", "Total sales", "Total sales"],
            "Who": ["Vendor", "Region average", "Vendor", "Region average"],
            "Value": [
                v["SOLD UNITS"], region_df["SOLD UNITS"].mean(),
                v["TOTAL SALES"], region_df["TOTAL SALES"].mean(),
            ],
        }
    )

    # Use a grouped bar chart to compare the vendor with the regional average.
    fig = px.bar(compare, x="Metric", y="Value", color="Who", barmode="group",
                 title="Vendor vs region average")
    st.plotly_chart(fig, width="stretch")
