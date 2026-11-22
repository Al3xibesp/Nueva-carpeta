from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "sellers.xlsx"

st.set_page_config(page_title="Sellers Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["SELLER"] = df["NAME"].str.strip() + " " + df["LASTNAME"].str.strip()
    # ID is not unique (9091 appears twice), so build a unique label for selection.
    df["LABEL"] = df["SELLER"] + " (ID " + df["ID"].astype(str) + ", " + df["REGION"] + ")"
    return df


df = load_data(DATA_PATH)

st.title("📊 Sellers Dashboard")

# ---------- Sidebar filter ----------
regions = sorted(df["REGION"].unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
if not selected_regions:
    st.warning("Select at least one region in the sidebar.")
    st.stop()

fdf = df[df["REGION"].isin(selected_regions)]

tab_overview, tab_charts, tab_vendor = st.tabs(["Table", "Charts", "Vendor"])

# ---------- Table ----------
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sellers", f"{len(fdf):,}")
    c2.metric("Units sold", f"{fdf['SOLD UNITS'].sum():,}")
    c3.metric("Total sales", f"${fdf['TOTAL SALES'].sum():,}")
    c4.metric("Avg sales per seller", f"${fdf['TOTAL SALES'].mean():,.0f}")

    st.dataframe(
        fdf.drop(columns=["SELLER", "LABEL"]),
        width="stretch",
        hide_index=True,
        column_config={
            "INCOME": st.column_config.NumberColumn(format="$%d"),
            "TOTAL SALES": st.column_config.NumberColumn(format="$%d"),
            "SALES AVERAGE": st.column_config.NumberColumn(format="percent"),
        },
    )

# ---------- Charts ----------
with tab_charts:
    by_region = (
        fdf.groupby("REGION")
        .agg(units=("SOLD UNITS", "sum"), sales=("TOTAL SALES", "sum"), avg=("TOTAL SALES", "mean"))
        .reset_index()
    )

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

    st.subheader("By seller")
    metric = st.radio(
        "Metric",
        ["SOLD UNITS", "TOTAL SALES", "SALES AVERAGE"],
        horizontal=True,
    )
    sdf = fdf.sort_values(metric, ascending=False)
    fig = px.bar(sdf, x="SELLER", y=metric, color="REGION", title=f"{metric.title()} by seller")
    if metric == "SALES AVERAGE":
        fig.update_yaxes(tickformat=".0%")
        st.caption("SALES AVERAGE is each seller's share of their region's total sales.")
    st.plotly_chart(fig, width="stretch")

# ---------- Vendor ----------
with tab_vendor:
    label = st.selectbox("Choose a vendor", fdf.sort_values("SELLER")["LABEL"])
    v = fdf[fdf["LABEL"] == label].iloc[0]
    region_df = df[df["REGION"] == v["REGION"]]

    st.subheader(v["SELLER"])
    st.caption(f"ID {v['ID']} · Region {v['REGION']}")

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

    rank = int(region_df["TOTAL SALES"].rank(ascending=False)[v.name])
    st.write(f"Ranks **#{rank} of {len(region_df)}** in {v['REGION']} by total sales.")

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
    fig = px.bar(compare, x="Metric", y="Value", color="Who", barmode="group",
                 title="Vendor vs region average")
    st.plotly_chart(fig, width="stretch")
