import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="Logistics & Trade Cost Explorer",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading with Caching ---
@st.cache_data
def load_data():
    # Use relative paths or flexible fallback paths
    shipping_path = Path("shipping_ticker_data.csv")
    monthly_path = Path("monthly_trade_data.csv")
    
    # Fallback to absolute paths if running locally in specific structures
    if not shipping_path.exists():
        shipping_path = Path("/Users/asherkatz/Desktop/logistics-cost/shipping_ticker_data.csv")
    if not monthly_path.exists():
        monthly_path = Path("/Users/asherkatz/Desktop/logistics-cost/monthly_trade_data.csv")

    shipping_df = pd.read_csv(shipping_path)
    monthly_df = pd.read_csv(monthly_path)

    # Parse Dates safely
    if "Date" in shipping_df.columns:
        shipping_df["Parsed_Date"] = pd.to_datetime(shipping_df["Date"], errors="coerce")
        shipping_df["Date_Only"] = shipping_df["Parsed_Date"].dt.date

    return shipping_df, monthly_df

# Load datasets
try:
    shipping_df, monthly_df = load_data()
except Exception as e:
    st.error(f"Error loading datasets. Please verify CSV file paths. Details: {e}")
    st.stop()

# --- Sidebar Configuration ---
st.sidebar.title("🧭 Navigation & Filters")
app_mode = st.sidebar.radio("Choose View", ["Overview & Summary", "Shipping Ticker Dashboard", "Monthly Trade Dashboard", "Raw Data Explorer"])

st.sidebar.markdown("---")

# --- Main App Layout ---
def main():
    if app_mode == "Overview & Summary":
        st.title("🚢 Logistics Cost & Trade Intelligence Hub")
        st.markdown("Welcome to your interactive dashboard. Use the sidebar to switch between high-resolution data visualizations for shipping markets and macroeconomic trade metrics.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Shipping Ticker Records", value=f"{len(shipping_df):,}")
        with col2:
            st.metric(label="Trade Data Months", value=f"{len(monthly_df):,}")
        with col3:
            latest_basket = shipping_df["Shipping_Basket_Index"].iloc[0] if "Shipping_Basket_Index" in shipping_df.columns else "N/A"
            st.metric(label="Latest Shipping Basket Index", value=f"{latest_basket}")

        st.markdown("---")
        st.subheader("Quick Trend Preview")
        
        if "Parsed_Date" in shipping_df.columns and "Shipping_Basket_Index" in shipping_df.columns:
            fig_quick = px.line(
                shipping_df.sort_values("Parsed_Date"),
                x="Parsed_Date",
                y="Shipping_Basket_Index",
                title="Recent Shipping Basket Index Trend",
                labels={"Parsed_Date": "Date", "Shipping_Basket_Index": "Basket Index"}
            )
            st.plotly_chart(fig_quick, use_container_width=True)

    elif app_mode == "Shipping Ticker Dashboard":
        st.title("📈 Shipping Ticker & Commodity Dashboard")
        st.markdown("Explore high-frequency shipping rates, fuel benchmarks, and currency metrics over time.")

        # Metric Selector
        available_metrics = [col for col in ["Shipping_Basket_Index", "Brent_Crude", "BDI_Proxy_BDRY", "ZIM", "MATX", "SBLK", "FRO", "STNG", "USD_ILS", "EUR_ILS"] if col in shipping_df.columns]
        
        selected_metrics = st.multiselect("Select Metrics to Plot", available_metrics, default=["Shipping_Basket_Index", "Brent_Crude"])

        if selected_metrics:
            fig_shipping = px.line(
                shipping_df.sort_values("Parsed_Date"),
                x="Parsed_Date",
                y=selected_metrics,
                title="Shipping & Macroeconomic Indicators Over Time",
                labels={"Parsed_Date": "Timestamp", "value": "Metric Value", "variable": "Indicator"}
            )
            st.plotly_chart(fig_shipping, use_container_width=True)
        else:
            st.warning("Please select at least one metric from the dropdown above.")

        # Summary statistics table
        st.subheader("Statistical Summary (Shipping Tickers)")
        st.dataframe(shipping_df[available_metrics].describe(), use_container_width=True)

    elif app_mode == "Monthly Trade Dashboard":
        st.title("📊 Monthly Macro Trade Dashboard")
        st.markdown("Analyze import/export volumes, Fisher volume indices, and country-specific trade stats.")

        # Year selection filter
        if "Year" in monthly_df.columns:
            years = sorted(monthly_df["Year"].dropna().unique())
            selected_year = st.selectbox("Filter by Year", ["All"] + list(years))
            
            filtered_trade = monthly_df if selected_year == "All" else monthly_df[monthly_df["Year"] == selected_year]
        else:
            filtered_trade = monthly_df

        # Plot Fisher Trade Volumes if available
        if "fisher_import_volume" in filtered_trade.columns and "fisher_export_volume" in filtered_trade.columns:
            fig_trade = px.bar(
                filtered_trade,
                x="Month",
                y=["fisher_import_volume", "fisher_export_volume"],
                barmode="group",
                title="Fisher Import vs Export Volumes by Month",
                labels={"value": "Volume Index", "variable": "Trade Type"}
            )
            st.plotly_chart(fig_trade, use_container_width=True)

        # Country specific analysis
        st.subheader("Bilateral Trade Explorer (Imports/Exports by Country)")
        country_cols = [c.replace("_Import", "") for c in filtered_trade.columns if c.endswith("_Import")]
        country_cols = sorted(list(set(country_cols)))

        if country_cols:
            selected_country = st.selectbox("Select Country Partner", country_cols)
            imp_col = f"{selected_country}_Import"
            exp_col = f"{selected_country}_Export"

            if imp_col in filtered_trade.columns and exp_col in filtered_trade.columns:
                fig_country = px.line(
                    filtered_trade,
                    x="Month",
                    y=[imp_col, exp_col],
                    title=f"Trade with {selected_country} (Imports vs Exports)",
                    labels={"value": "Value (Millions)", "variable": "Flow"}
                )
                st.plotly_chart(fig_country, use_container_width=True)

    elif app_mode == "Raw Data Explorer":
        st.title("🔍 Raw Dataset Inspector")
        
        dataset_choice = st.radio("Choose Dataset to Inspect", ["Shipping Ticker Data", "Monthly Trade Data"])
        
        if dataset_choice == "Shipping Ticker Data":
            st.subheader("Shipping Ticker Dataset Preview")
            st.dataframe(shipping_df, use_container_width=True)
            
            # Download button
            csv = shipping_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Shipping Data as CSV", csv, "shipping_ticker_data_filtered.csv", "text/csv")
            
        else:
            st.subheader("Monthly Trade Dataset Preview")
            st.dataframe(monthly_df, use_container_width=True)
            
            # Download button
            csv = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Monthly Trade Data as CSV", csv, "monthly_trade_data_filtered.csv", "text/csv")

if __name__ == "__main__":
    main()