# Sellers Dashboard

Streamlit dashboard for `data/sellers.xlsx`.

## Run in VS Code

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Data

`data/sellers.xlsx` (columns: REGION, ID, NAME, LASTNAME, INCOME, SOLD UNITS, TOTAL SALES, SALES AVERAGE).
`SALES AVERAGE` is each seller's share of their region's total sales (sums to 100% per region).
