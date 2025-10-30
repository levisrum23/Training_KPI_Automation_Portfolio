import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
from sqlalchemy import create_engine

def main():
    """
    Main function to run the L&D report ETL process.
    """
    print("Starting ETL Process...")
    
    # --- 1. DEFINE "TODAY" ---
    TODAY = pd.to_datetime('2025-10-28')
    REPORT_MONTH_STR = TODAY.strftime('%Y-%m') # e.g., "2025-10"
    
    try:
        # --- 1. EXTRACT ---
        print("[EXTRACT] Loading files...")
        base_dir = Path.cwd()
        input_dir = base_dir / "inputs"
        output_dir = base_dir / "outputs" # <-- NEW
        
        # Create the 'outputs' folder if it doesn't exist
        output_dir.mkdir(exist_ok=True) # <-- NEW
        
        roster_file = input_dir / "Employee_Roster.xlsx"
        log_file = input_dir / "Training_Log_2025.xlsx"
        goals_file = input_dir / "Department_Goals.xlsx"
        
        df_roster = pd.read_excel(roster_file)
        df_log = pd.read_excel(log_file)
        df_goals = pd.read_excel(goals_file)

        print("[EXTRACT] Data loaded. Verifying...")
        print(f"Roster shape: {df_roster.shape}")
        print(f"Log shape: {df_log.shape}")
        print(f"Goals shape: {df_goals.shape}")
        
        # --- 4. TRANSFORM: CLEAN & PREP DATA ---
        print("\n[TRANSFORM] Starting data transformation...")
        df_log['Course_Date'] = pd.to_datetime(df_log['Course_Date'])

        # --- 5. TRANSFORM: JOIN & ENRICH (The "VLOOKUP") ---
        df_merged = pd.merge(
            df_log,
            df_roster[['Employee_ID', 'Department']],
            on='Employee_ID',
            how='left'
        )
        print("[TRANSFORM] Merged Roster and Log data.")

        # --- 6. TRANSFORM: FILTER & AGGREGATE (The "Pivot Table") ---
        is_this_year = (df_merged['Course_Date'].dt.year == TODAY.year)
        is_this_month = (df_merged['Course_Date'].dt.month == TODAY.month)

        df_ytd_data = df_merged[is_this_year]
        df_mtd_data = df_merged[is_this_year & is_this_month]

        ytd_hours = df_ytd_data.groupby('Department')['Duration_Hours'].sum().rename('YTD_Hours')
        mtd_hours = df_mtd_data.groupby('Department')['Duration_Hours'].sum().rename('MTD_Hours')

        print("[TRANSFORM] Calculated MTD and YTD hours.")

        # --- 7. TRANSFORM: BUILD FINAL REPORT ---
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
        
        # Add a 'Report_Month' column for our database
        df_kpi_report['Report_Month'] = REPORT_MONTH_STR # <-- NEW
        
        print("\n--- [TRANSFORM] Phase Complete ---")
        
        # --- 8. LOAD ---
        print("\n[LOAD] Starting data load phase...")
        
        # --- 8a: Load to Excel ---
        excel_file_name = f"Monthly_KPI_Summary_{REPORT_MONTH_STR}.xlsx"
        excel_path = output_dir / excel_file_name
        
        # Create a clean copy for Excel
        df_excel = df_kpi_report.copy()
        # Format the % column nicely for managers
        df_excel['YTD_Achievement_Percent'] = df_excel['YTD_Achievement_Percent'].map('{:.1%}'.format)
        
        df_excel.to_excel(excel_path, index=False)
        print(f"[LOAD] Success: Data saved to {excel_path}")

        # --- 8b: Load to Database ---
        db_path = output_dir / "ld_database.db"
        # Create the database "connection string"
        # This tells SQLAlchemy "I'm using sqlite, and here is the file"
        engine = create_engine(f"sqlite:///{db_path}")

        # Save the *unformatted* data to the database
        # 'if_exists="append"' adds the new rows, it doesn't overwrite
        # 'index=False' means don't save the pandas index (0, 1, 2, 3)
        df_kpi_report.to_sql(
            'kpi_history',    # The name of the table
            con=engine,
            if_exists='append',
            index=False
        )
        print(f"[LOAD] Success: Data appended to database at {db_path}")
        
        print("\n--- [ETL Process Complete] ---")


    except FileNotFoundError as e:
        print(f"\n--- [ERROR] ---")
        print(f"Error: {e}")
        print(f"File not found. Did you create the 'inputs' folder?")
        print(f"Are your filenames spelled *exactly* correct?")
        sys.exit(1)
    except Exception as e:
        print(f"\n--- [ERROR] ---")
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()