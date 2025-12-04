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

and returns, for each country, the list of clients with the **sum of notional traded**.  
You can switch between a *long format* and an *Excel-like pivot table*, and export the results in Excel.
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
        # ------------------ Aggregation (long format) ------------------
        summary_long = (
            df
            .groupby(["country", "client"], as_index=False)["notional"]
            .sum()
            .sort_values(["country", "notional"], ascending=[True, False])
        )

        # ------------------ Pivot (wide format) ------------------
        summary_wide = summary_long.pivot_table(
            index="country",
            columns="client",
            values="notional",
            aggfunc="sum",
            fill_value=0
        )

        # ------------------ View selector ------------------
        view_mode = st.radio(
            "Select display mode:",
            [
                "Long format (Country / Client / Notional)",
                "Pivot table (Countries as rows, Clients as columns)"
            ]
        )

        st.subheader("Aggregated Notional")

        if view_mode == "Long format (Country / Client / Notional)":
            st.dataframe(summary_long, use_container_width=True)
        else:
            st.dataframe(summary_wide, use_container_width=True)

        st.markdown("---")
        st.subheader("Download Excel report")

        # ------------------ Excel export: long format ------------------
        excel_long = BytesIO()
        with pd.ExcelWriter(excel_long, engine="xlsxwriter") as writer:
            summary_long.to_excel(writer, sheet_name="Long_Format", index=False)

        st.download_button(
            label="📥 Download long-format table (Excel)",
            data=excel_long.getvalue(),
            file_name="notional_country_client_long.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ------------------ Excel export: pivot format ------------------
        excel_pivot = BytesIO()
        with pd.ExcelWriter(excel_pivot, engine="xlsxwriter") as writer:
            summary_wide.to_excel(writer, sheet_name="Pivot_Table")

        st.download_button(
            label="📥 Download pivot table (Excel)",
            data=excel_pivot.getvalue(),
            file_name="notional_country_client_pivot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ------------------ Excel export: full report (2 sheets) ------------------
        excel_full = BytesIO()
        with pd.ExcelWriter(excel_full, engine="xlsxwriter") as writer:
            summary_long.to_excel(writer, sheet_name="Long_Format", index=False)
            summary_wide.to_excel(writer, sheet_name="Pivot_Table")

        st.download_button(
            label="📥 Download full Excel report (2 sheets)",
            data=excel_full.getvalue(),
            file_name="notional_country_client_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("Please upload a CSV or Excel file to get started.")
