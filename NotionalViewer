import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Client Notional Dashboard", layout="wide")

st.title("Client Notional per Country")

st.markdown(
    """
This app takes a trade file with the following columns:

- `country`
- `client`
- `product_type`
- `notional`

and returns, for each country, the list of clients with the **sum of notional traded**.
"""
)

# --------- File upload ---------
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

    # --------- Optional filters ---------
    with st.sidebar:
        st.header("Filters")

        # Filter on product type
        if "product_type" in df.columns:
            all_products = sorted(df["product_type"].dropna().unique())
            selected_products = st.multiselect(
                "Product types", 
                options=all_products, 
                default=all_products
            )
            df = df[df["product_type"].isin(selected_products)]

        # You can add more filters here if needed (date, desk, etc.)

    # --------- Aggregation logic ---------
    required_cols = {"country", "client", "notional"}
    if not required_cols.issubset(df.columns):
        st.error(f"Input file must contain at least: {required_cols}")
    else:
        grouped = (
            df
            .groupby(["country", "client"], as_index=False)["notional"]
            .sum()
            .sort_values(["country", "notional"], ascending=[True, False])
        )

        st.subheader("Aggregated Notional per Country and Client")
        st.dataframe(grouped, use_container_width=True)

        # --------- Download button ---------
        csv_buffer = io.StringIO()
        grouped.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download aggregated data as CSV",
            data=csv_buffer.getvalue(),
            file_name="notional_per_country_client.csv",
            mime="text/csv",
        )
else:
    st.info("Please upload a CSV or Excel file to get started.")
