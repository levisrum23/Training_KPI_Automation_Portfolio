# L&D KPI Automation & BI Dashboard

**Author:** Anderson Rumuy
**Portfolio Project (WIP)** - *Actively in development*

---

### 1. The Business Problem

In my role as a Learning & Development officer, I was responsible for a monthly manual reporting process to track training KPIs. This process was:
* **Time-Consuming:** Required 8-10 hours per month.
* **Error-Prone:** Involved manually merging and pivoting 3+ different Excel spreadsheets.
* **Static:** The final report was a "dead" PowerPoint slide, offering no historical tracking or interactive analysis.

### 2. The Solution

I built a complete, automated ETL (Extract, Transfom, Load) pipeline and a dynamic Business Intelligence dashboard. This system:
1.  **Extracts** data from standardized Excel inputs (employee roster, training logs, department goals).
2.  **Transforms** the raw data using Python (`pandas`) to automatically join, clean, and aggregate it—calculating MTD/YTD hours and %-to-goal.
3.  **Loads** the final, clean report into two destinations:
    * A new, clean Excel file for managers.
    * A permanent `SQLite` database to build a historical record.
4.  **Visualizes** the data through an interactive web dashboard built with `Streamlit`, allowing any stakeholder to self-serve and view historical KPI trends.

### 3. Live Demo

[Link to your live Streamlit app - *We will add this in the next step!*]

---

### 4. Technical Stack

* **Language:** Python
* **ETL & Data Manipulation:** `pandas`
* **Database:** `SQLite` (via `sqlalchemy`)
* **BI Dashboard:** `Streamlit`
* **Libraries:** `openpyxl`