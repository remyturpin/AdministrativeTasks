import io
import pandas as pd
import streamlit as st

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
You can switch between a *long format* and an *Excel-like pivot table*.
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

        # Product type filter (optional)
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
            ["Long format (Country / Client / Notional)",
             "Pivot table (Countries as rows, Clients as columns)"]
        )

        st.subheader("Aggregated Notional")

        if view_mode == "Long format (Country / Client / Notional)":
            st.dataframe(summary_long, use_container_width=True)

            # Download button (long format)
            csv_buffer = io.StringIO()
            summary_long.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download long-format table as CSV",
                data=csv_buffer.getvalue(),
                file_name="notional_country_client_long.csv",
                mime="text/csv",
            )

        else:
            st.dataframe(summary_wide, use_container_width=True)

            csv_buffer = io.StringIO()
            summary_wide.to_csv(csv_buffer)
            st.download_button(
                label="📥 Download pivot table as CSV",
                data=csv_buffer.getvalue(),
                file_name="notional_country_client_pivot.csv",
                mime="text/csv",
            )

else:
    st.info("Please upload a CSV or Excel file to get started.")
