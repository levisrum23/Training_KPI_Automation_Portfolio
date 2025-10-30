import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- NEW DATA LOADING FUNCTION ---
@st.cache_data  # This "caches" the data, so we only run this slow ETL once.
def run_etl_pipeline():
    """
    This function runs the entire ETL process in-memory
    by reading the raw Excel files from the 'inputs' folder.
    """
    print("RUNNING IN-MEMORY ETL...") # You'll see this in the Streamlit logs
    
    # --- 1. DEFINE "TODAY" ---
    TODAY = pd.to_datetime('2025-10-28')
    REPORT_MONTH_STR = TODAY.strftime('%Y-%m')
    
    # --- 2. EXTRACT ---
    input_dir = Path.cwd() / "inputs"
    df_roster = pd.read_excel(input_dir / "Employee_Roster.xlsx")
    df_log = pd.read_excel(input_dir / "Training_Log_2025.xlsx")
    df_goals = pd.read_excel(input_dir / "Department_Goals.xlsx")
    
    # --- 3. TRANSFORM: CLEAN & PREP ---
    df_log['Course_Date'] = pd.to_datetime(df_log['Course_Date'])

    # --- 4. TRANSFORM: JOIN & ENRICH ---
    df_merged = pd.merge(
        df_log,
        df_roster[['Employee_ID', 'Department']],
        on='Employee_ID',
        how='left'
    )
    
    # --- 5. TRANSFORM: FILTER & AGGREGATE ---
    is_this_year = (df_merged['Course_Date'].dt.year == TODAY.year)
    is_this_month = (df_merged['Course_Date'].dt.month == TODAY.month)

    df_ytd_data = df_merged[is_this_year]
    df_mtd_data = df_merged[is_this_year & is_this_month]

    ytd_hours = df_ytd_data.groupby('Department')['Duration_Hours'].sum().rename('YTD_Hours')
    mtd_hours = df_mtd_data.groupby('Department')['Duration_Hours'].sum().rename('MTD_Hours')

    # --- 6. TRANSFORM: BUILD FINAL REPORT ---
    df_kpi_summary = pd.merge(
        ytd_hours,
        mtd_hours,
        on='Department',
        how='outer'
    ).fillna(0)
    
    df_kpi_report = pd.merge(
        df_goals,
        df_kpi_summary,
        on='Department',
        how='left'
    ).fillna(0)

    # Calculate the final KPI
    df_kpi_report['YTD_Achievement_Percent'] = (
        df_kpi_report['YTD_Hours'] / df_kpi_report['Target_Man_Hours_YTD']
    )
    
    # Add a 'Report_Month' column
    df_kpi_report['Report_Month'] = REPORT_MONTH_STR
    
    return df_kpi_report

def main():
    # --- 1. Page Configuration ---
    st.set_page_config(
        page_title="L&D KPI Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # --- 2. Load Data ---
    # Now, we just call our new ETL function
    df = run_etl_pipeline()

    if df.empty:
        st.error("Data loading failed. Check 'inputs' folder.")
        st.stop() 

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
        # 'tooltip' argument removed for compatibility
    )
    st.caption("This chart shows the total YTD hours as a percentage of the annual target.")

    # --- 7. Data Table ---
    st.subheader("Detailed Report Data")
    
    # Format the % column for display in the table
    df_filtered_display = df_filtered.copy()
    df_filtered_display['YTD_Achievement_Percent'] = df_filtered_display['YTD_Achievement_Percent'].map('{:.1%}'.format)
    
    # Display the final table
    st.dataframe(df_filtered_display.drop(columns=['YTD_Achievement_Formatted'], errors='ignore'))


if __name__ == "__main__":
    main()