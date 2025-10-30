import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

def load_data():
    """
    Function to load data from the SQLite database.
    We use @st.cache_data to speed up the app by only loading
    the data once.
    """
    # Define the path to the database
    db_path = Path.cwd() / "outputs" / "ld_database.db"
    
    # Check if the database file exists
    if not db_path.exists():
        st.error(f"Error: Database file not found at {db_path}")
        st.error("Please run `process_report.py` first to create the database.")
        return pd.DataFrame() # Return an empty DataFrame

    try:
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Read the entire kpi_history table
        df = pd.read_sql('SELECT * FROM kpi_history', con=engine)
        
        # Convert % column back to a numeric float for charting
        df['YTD_Achievement_Percent'] = pd.to_numeric(df['YTD_Achievement_Percent'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    # --- 1. Page Configuration ---
    # This should be the first streamlit command
    st.set_page_config(
        page_title="L&D KPI Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # --- 2. Load Data ---
    df = load_data()

    if df.empty:
        st.stop() # Stop the script if data loading failed

    # --- 3. Page Title ---
    st.title("L&D Key Performance Indicator (KPI) Dashboard")
    st.markdown("This dashboard tracks YTD & MTD training hours against department goals.")

    # --- 4. Sidebar Filters ---
    st.sidebar.header("Filters")
    
    # Get the most recent month from our data
    latest_month = df['Report_Month'].max()
    
    # Create a dropdown to select the report month
    selected_month = st.sidebar.selectbox(
        "Select Report Month",
        df['Report_Month'].unique(),
        index=df['Report_Month'].unique().tolist().index(latest_month) # Default to latest
    )
    
    # Filter the main dataframe by the selected month
    df_filtered = df[df['Report_Month'] == selected_month].copy()

    # --- 5. Main Page Metrics (KPIs) ---
    st.subheader(f"Summary for: {selected_month}")
    
    # Calculate overall metrics
    total_ytd_hours = df_filtered['YTD_Hours'].sum()
    total_mtd_hours = df_filtered['MTD_Hours'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Total YTD Training Hours", f"{total_ytd_hours:,.0f} hrs")
    col2.metric("Total MTD Training Hours", f"{total_mtd_hours:,.0f} hrs")

    st.markdown("---") # Horizontal line

    # --- 6. Charts ---
    st.subheader("YTD Achievement vs. Goal")
    
    # Format the % column for the chart tooltip
    df_filtered['YTD_Achievement_Formatted'] = df_filtered['YTD_Achievement_Percent'].map('{:.1%}'.format)

    # A bar chart showing % achievement by department
    st.bar_chart(
        df_filtered,
        x='Department',
        y='YTD_Achievement_Percent'
    )
    st.caption("This chart shows the total YTD hours as a percentage of the annual target.")

    # --- 7. Data Table ---
    st.subheader("Detailed Report Data")
    
    # Format the % column for display in the table
    df_filtered_display = df_filtered.copy()
    df_filtered_display['YTD_Achievement_Percent'] = df_filtered_display['YTD_Achievement_Percent'].map('{:.1%}'.format)
    
    # Display the final table
    st.dataframe(df_filtered_display.drop(columns=['YTD_Achievement_Formatted']))


if __name__ == "__main__":
    main()