import pandas as pd
import streamlit as st
from io import BytesIO

# ------------------ Page config ------------------
st.set_page_config(page_title="NotionalView", layout="wide")

st.title("NotionalView — Client Notional per Country")

st.markdown(
    """
This app takes a trade file with the following columns:

- `country`
- `client`
- `product_type`
- `notional`

and returns, for each country, an **Excel-like pivot table** with clients in columns
and the **sum of notional traded** in each cell.
"""
)

# ------------------ File upload ------------------
uploaded_file = st.file_uploader(
    "Upload your trade file (CSV or Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    # Read file depending on extension
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)

    # ------------------ Sidebar filters ------------------
    with st.sidebar:
        st.header("Filters")

        # Optional filter on product_type
        if "product_type" in df.columns:
            all_products = sorted(df["product_type"].dropna().unique())
            selected_products = st.multiselect(
                "Product types",
                options=all_products,
                default=all_products
            )
            df = df[df["product_type"].isin(selected_products)]

    # ------------------ Validation ------------------
    required_cols = {"country", "client", "notional"}
    if not required_cols.issubset(df.columns):
        st.error(f"Input file must contain at least the following columns: {required_cols}")
    else:
        # ------------------ Aggregation ------------------
        summary_long = (
            df
            .groupby(["country", "client"], as_index=False)["notional"]
            .sum()
        )

        # ------------------ Pivot (final output) ------------------
        pivot_df = summary_long.pivot_table(
            index="country",
            columns="client",
            values="notional",
            aggfunc="sum",
            fill_value=0
        )

        st.subheader("Pivot Table — Notional per Country and Client")
        st.dataframe(pivot_df, use_container_width=True)

        # ------------------ Excel export: pivot only ------------------
        st.markdown("---")
        st.subheader("Download Excel Pivot")

        excel_pivot = BytesIO()
        with pd.ExcelWriter(excel_pivot, engine="xlsxwriter") as writer:
            pivot_df.to_excel(writer, sheet_name="Pivot_Table")

        st.download_button(
            label="📥 Download pivot table (Excel)",
            data=excel_pivot.getvalue(),
            file_name="notional_country_client_pivot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("Please upload a CSV or Excel file to get started.")
