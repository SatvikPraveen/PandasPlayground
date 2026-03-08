# 📖 Data Dictionary

This document describes all datasets used in the PandasPlayground project, including column names, data types, descriptions, and sample values.

---

## 🏪 Superstore Sales Dataset

**File:** `data/superstore_sales.csv`  
**Format:** CSV  
**Rows:** ~10,000  
**Purpose:** Retail sales analysis, time series, aggregations

### Columns

| Column | Data Type | Description | Sample Values |
|--------|-----------|-------------|---------------|
| `Order_ID` | string | Unique identifier for each order | "ORD-2024-001" |
| `Order_Date` | datetime | Date when order was placed | "2024-01-15" |
| `Ship_Date` | datetime | Date when order was shipped | "2024-01-18" |
| `Ship_Mode` | category | Shipping method used | "Standard Class", "Second Class", "First Class", "Same Day" |
| `Customer_ID` | string | Unique customer identifier | "CUS-12345" |
| `Customer_Name` | string | Full name of customer | "John Smith" |
| `Segment` | category | Customer segment | "Consumer", "Corporate", "Home Office" |
| `Country` | string | Country of sale | "United States" |
| `City` | string | City of sale | "New York", "Los Angeles" |
| `State` | string | State/Province | "CA", "NY", "TX" |
| `Postal_Code` | string | Zip/Postal code | "90210" |
| `Region` | category | Geographic region | "East", "West", "Central", "South" |
| `Product_ID` | string | Unique product identifier | "PROD-001" |
| `Category` | category | Product category | "Furniture", "Office Supplies", "Technology" |
| `Sub_Category` | category | Product subcategory | "Chairs", "Tables", "Phones" |
| `Product_Name` | string | Full product name | "Staples Desk Chair" |
| `Sales` | float | Total sale amount in USD | 100.50 |
| `Quantity` | integer | Number of items sold | 1-10 |
| `Discount` | float | Discount percentage (0-1) | 0.0, 0.15, 0.20 |
| `Profit` | float | Profit from sale (can be negative) | -50.00 to 500.00 |

**Use Cases:**
- Time series analysis (sales over time)
- Geographic analysis (sales by region/state)
- Product performance analysis
- Customer segmentation
- Profit margin analysis

---

## 🌦️ Weather Data

**File:** `data/weather_data.json`  
**Format:** JSON  
**Rows:** ~10,000  
**Purpose:** JSON parsing, date handling, categorical analysis

### Schema

```json
{
  "date": "YYYY-MM-DD",
  "temperature_c": -10 to 40,
  "humidity": 30 to 100,
  "condition": "Sunny|Rain|Cloudy|Storm|Snow"
}
```

### Fields

| Field | Data Type | Description | Range/Values |
|-------|-----------|-------------|--------------|
| `date` | string (ISO date) | Observation date | "2022-01-01" to "2024-12-31" |
| `temperature_c` | integer | Temperature in Celsius | -10°C to 40°C |
| `humidity` | integer | Humidity percentage | 30% to 100% |
| `condition` | string | Weather condition | "Sunny", "Rain", "Cloudy", "Storm", "Snow" |

**Use Cases:**
- JSON to DataFrame conversion
- Date parsing and manipulation
- Aggregations by weather condition
- Time series resampling
- Merging with other temporal datasets

---

## 🏦 Bank Loans Dataset

**File:** `data/bank_loans.xlsx`  
**Format:** Excel (.xlsx)  
**Rows:** ~10,000  
**Purpose:** Excel handling, categorical analysis, approval predictions

### Columns

| Column | Data Type | Description | Sample Values |
|--------|-----------|-------------|---------------|
| `Customer_ID` | integer | Unique customer ID | 1001-11000 |
| `Customer_Name` | string | Full customer name | "Jane Doe" |
| `Age` | integer | Customer age in years | 21-65 |
| `Income` | integer | Annual income in USD | 25,000 - 150,000 |
| `Loan_Amount` | integer | Requested loan amount | 3,000 - 80,000 |
| `Loan_Purpose` | category | Purpose of loan | "Car", "Home", "Education", "Business", "Medical", "Vacation" |
| `Approved` | category | Approval status | "Yes", "No" |
| `Region` | category | Customer region (in multisheet) | "North", "South", "East", "West" |

**Derived Metrics:**
- `Loan_to_Income_Ratio` = Loan_Amount / Income
- `Approval_Rate` = (Approved == "Yes").mean()
- `Average_Loan_by_Purpose` = groupby('Loan_Purpose')['Loan_Amount'].mean()

**Use Cases:**
- Excel file handling (single and multi-sheet)
- Categorical data analysis
- Approval rate calculations
- Income segmentation
- Purpose-based loan analysis

---

## 🦠 COVID-19 Data

**File:** `data/covid_data.parquet`  
**Format:** Parquet  
**Rows:** ~5,000  
**Purpose:** Parquet handling, time series, merging

### Columns

| Column | Data Type | Description | Sample Values |
|--------|-----------|-------------|---------------|
| `date` | datetime | Report date | "2020-03-01" onwards |
| `country` | string | Country name | "United States", "India", "Brazil" |
| `new_cases` | integer | Daily new cases | 0 - 1,000,000 |
| `total_cases` | integer | Cumulative cases | 0 - 100,000,000 |
| `new_deaths` | integer | Daily new deaths | 0 - 10,000 |
| `total_deaths` | integer | Cumulative deaths | 0 - 1,000,000 |
| `hospitalized` | integer | Currently hospitalized | 0 - 100,000 |
| `icu` | integer | In ICU | 0 - 10,000 |
| `population` | integer | Country population | varies |

**Calculated Fields:**
- `case_rate` = (new_cases / population) * 100,000
- `death_rate` = (total_deaths / total_cases) * 100
- `7_day_avg` = new_cases.rolling(7).mean()

**Use Cases:**
- Parquet file operations
- Time series analysis with resampling
- Cross-country comparisons
- Rolling averages and trends
- Merging with weather/sales data

---

## 📁 Processed/Export Files

### `exports/final_merged_pipeline.csv`

**Generated by:** `08_final_pipeline.ipynb`

Combined dataset merging superstore sales, weather, and covid data by date/region.

| Column | Description |
|--------|-------------|
| `month` | Aggregated month (first day of month) |
| `sales` | Total monthly sales |
| `profit` | Total monthly profit |
| `new_cases` | Total monthly COVID cases |
| `hospitalized` | Average hospitalized count |
| `avg_temperature` | Average monthly temperature |
| `region` | Geographic region |

---

## 🔍 Data Quality Notes

### Missing Values
- **Superstore Sales**: No missing values (synthetically generated)
- **Weather Data**: ~0.1% missing temperature readings
- **Bank Loans**: ~2% missing income values
- **COVID Data**: Some countries have gaps in hospitalization data

### Data Generation
All datasets in this project are **synthetically generated** using:
- `scripts/generate_mock_data.py`
- Faker library for realistic names/addresses
- NumPy for numerical distributions
- Pandas for structure

### Data Privacy
No real personal information is used. All names, addresses, and identifiers are randomly generated.

---

## 🔄 Data Lineage

```
Raw Data (data/)
    ↓
01-02: Load & Clean (assets/*_cleaned.csv)
    ↓
03-04: Aggregate & Merge (assets/*_agg_*.csv)
    ↓
05-07: Time Series & Visualizations
    ↓
08: Final Pipeline (exports/final_merged_pipeline.csv)
    ↓
09: Reports (exports/report_final.*)
    ↓
10: Optimized (exports/*_optimized.csv)
```

---

## 📝 Adding Your Own Data

To use your own datasets:

1. **Place files in `data/` directory**
2. **Update column mappings** in relevant notebooks
3. **Document your schema** (add to this file)
4. **Update `scripts/utils_io.py`** if needed

### Example: Adding a New Dataset

```python
# In your notebook:
import pandas as pd
from scripts.utils_io import load_csv

# Load your data
df = load_csv('data/my_custom_data.csv')

# Document in this file:
# - Column names and types
# - Sample values
# - Data sources
# - Known quality issues
```

---

## 📚 References

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Data Types in Pandas](https://pandas.pydata.org/docs/user_guide/basics.html#dtypes)
- [Working with Missing Data](https://pandas.pydata.org/docs/user_guide/missing_data.html)

---

**Last Updated:** March 8, 2026  
**Maintained by:** PandasPlayground Contributors
