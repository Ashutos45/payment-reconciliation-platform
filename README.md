# 🏦 Payment Reconciliation Platform

A production-grade, full-stack Fintech application built to automate and streamline the process of reconciling internal ledger transactions against external bank statements. It features a robust Python backend powered by **FastAPI** and **pandas**, and an interactive, data-rich frontend built with **Streamlit**.

## 🌟 Key Features

- **Automated Ingestion**: Seamlessly upload and parse `.csv` and `.xlsx` transaction files.
- **Advanced Matching Engine**:
  - **Exact Matching**: Matches transactions on ID, timestamp (±5 mins tolerance), and amount (±$0.01 tolerance).
  - **Fuzzy Matching**: Uses `rapidfuzz` to catch mangled transaction IDs when times and amounts still align perfectly.
- **Exception Detection**: Automatically identifies edge-cases and discrepancies:
  - 🚨 Missing Transactions (Unmatched records)
  - 🚨 Duplicate Transactions
  - 🚨 Amount Mismatches
  - 🚨 Delayed Settlements
  - 🚨 Refund Status Mismatches
- **Interactive Analytics Dashboard**: Beautiful, real-time KPI metrics and Plotly charts (Donut, Bar) displaying match rates and exception breakdowns.
- **Exporting & Reporting**: Automatically generate and download comprehensive multi-sheet Excel reports detailing exact matches, fuzzy matches, unmatched records, and exceptions.
- **Robust Architecture**: Built with SQLAlchemy ORM, Pydantic validation, centralized Loguru logging, and Clean Architecture principles.

---

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Data Processing**: Pandas, NumPy, RapidFuzz
- **Database**: SQLAlchemy, SQLite (Default for local dev), PostgreSQL (Production ready)
- **Frontend**: Streamlit, Plotly
- **Testing**: Pytest

---

## 📂 Project Structure

```text
payment-reconciliation-tool/
│
├── app/
│   ├── api/            # FastAPI Route Endpoints (Upload, Reconcile, Metrics, etc.)
│   ├── core/           # Environment Config & Logger Setup
│   ├── db/             # SQLAlchemy Database Setup & Models
│   ├── schemas/        # Pydantic Validation Models
│   ├── services/       # Core Business Logic (Ingestion, Matching, Exceptions, Reports)
│   └── dashboard/      # Streamlit Frontend UI Application
│
├── data/               # Sample CSV Data for testing
├── tests/              # Pytest automated testing suite
├── uploads/            # Temporary directory for file ingestion
├── requirements.txt    # Project Dependencies
├── .env                # Environment Variables Configuration
├── main.py             # FastAPI Application Entrypoint
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Installation
Clone the repository and install the dependencies:
```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
The project runs out-of-the-box using a local SQLite database configured in the `.env` file. If you wish to switch to PostgreSQL, simply edit the `.env` file:
```env
# Switch from SQLite to PostgreSQL by updating DATABASE_URL
DATABASE_URL=postgresql://user:password@localhost/payment_reconciliation
```

---

## 🏃‍♂️ Running the Application

This platform requires both the Backend API and Frontend Dashboard to be running simultaneously.

### Start the FastAPI Backend
Open a terminal and run the server:
```bash
uvicorn main:app --reload
```
*The API will be available at `http://127.0.0.1:8000`*
*API Documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`*

### Start the Streamlit Frontend
Open a **new** terminal window and run:
```bash
streamlit run app/dashboard/app.py
```
*The Dashboard will open automatically in your browser at `http://localhost:8501`*

---

## 🧪 Running Tests

To ensure the core business logic and APIs are functioning correctly, run the automated test suite:
```bash
pytest tests/
```

---

## 📖 How to Use the Platform

1. **Upload Data**: Navigate to the **Upload** page on the sidebar. Upload the sample files located in the `data/` folder (`internal_transactions.csv` and `bank_transactions.csv`).
2. **Reconcile**: Go to the **Dashboard** page and click **"Run Matching Engine"**. The system will crunch the numbers and instantly display your match rates and metrics.
3. **Review Exceptions**: Head to the **Exceptions** page to drill down into specific discrepancies like amount mismatches or missing records.
4. **Export**: Finally, go to the **Export** page to download a clean, multi-sheet `.xlsx` report of the entire reconciliation run.
