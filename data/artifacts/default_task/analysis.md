# Quantitative Data Analysis: demo_sales.csv

**Total Records:** 72 • **Dimensions:** Date, Region, Product, Revenue, Units, Customers, Customer Retention, Average Order Value

## Computed Descriptive Statistics

| Metric | Total | Mean | Median | Std Dev | Min / Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Revenue** | 18,955,000.0 | 263,263.89 | 237,500.0 | 114604.27 | 95000.0 / 555000.0 |
| **Units** | 6,900.0 | 95.83 | 91.0 | 39.22 | 30.0 / 190.0 |
| **Customers** | 6,150.0 | 85.42 | 80.0 | 34.93 | 25.0 / 168.0 |
| **Customer Retention** | 5,991.4 | 83.21 | 85.2 | 8.68 | 58.2 / 95.1 |
| **Average Order Value** | 234,000.0 | 3,250.0 | 3,250.0 | 1750.0 | 1500.0 / 5000.0 |

## Detected Anomalies (Outliers |Z| > 2.0)
- **Row 7**: `Revenue` = 510000.0 (z-score: 2.15)
- **Row 13**: `Revenue` = 540000.0 (z-score: 2.41)
- **Row 19**: `Revenue` = 555000.0 (z-score: 2.55)
- **Row 25**: `Revenue` = 530000.0 (z-score: 2.33)
- **Row 31**: `Revenue` = 495000.0 (z-score: 2.02)