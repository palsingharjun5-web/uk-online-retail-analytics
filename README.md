# UK Online Retail Analytics Dashboard

An end-to-end data analytics project built using Python, Pandas, PostgreSQL, SQL, Streamlit, and Plotly to analyze UK online retail transaction data and transform it into an interactive business intelligence dashboard.

## Project Overview

This project analyzes over 1 million retail transaction records from a UK online retailer covering the period from December 2009 to December 2011.

The objective was to take raw transactional data, clean and structure it, build an analytical PostgreSQL database, perform business-focused analysis using SQL, and present the results through an interactive Streamlit dashboard.

The dashboard allows users to explore sales performance, customer behavior, product performance, geographic distribution, returns, cancellations, operational patterns, customer segmentation, and cohort retention.

## Tech Stack

- Python
- Pandas
- PostgreSQL
- SQL
- Streamlit
- Plotly
- Git
- GitHub

## Data & Database

The original dataset contained 1,067,371 transaction rows across two yearly worksheets.

After removing duplicate records, the final dataset contained 1,033,036 transactions.

The cleaned data was organized into a PostgreSQL analytical database containing tables and views for transactions, products, customers, product descriptions, sales, returns, customer RFM analysis, customer segmentation, customer cohorts, cohort retention, geographic analysis, product performance, transaction types, and data quality analysis.

## Dashboard

The dashboard is divided into several analytical sections:

### Overview
Provides a high-level summary of overall business performance using key KPIs and major trends.

### Sales
Analyzes revenue, orders, average order value, sales trends, and transaction performance.

### Customers
Explores customer revenue, purchasing behavior, repeat customers, and customer-level performance.

### Products
Examines product revenue, sales volume, and product-level performance.

### Geography
Analyzes sales and customer activity across different countries.

### Operations
Focuses on transaction types, returns, cancellations, and operational patterns.

### Findings
Presents the major analytical findings and business observations identified throughout the project.

## Key Metrics

- Total Transactions: 1,033,036
- Sale Transactions: 1,003,763
- Orders: 39,580
- Customers: 5,862
- Products: 4,910
- Units Sold: 11,188,703
- Revenue: £19,669,448.58
- Average Order Value: £496.95
- Revenue per Unit: £1.76
- Analysis Period: December 2009 – December 2011

## Analysis Areas

The project includes analysis of:

- Monthly and yearly revenue trends
- Country-level sales performance
- Product revenue and sales volume
- Customer revenue contribution
- Repeat customer behavior
- Customer RFM analysis
- Customer segmentation
- Customer cohort analysis
- Cohort retention
- Returns and return rates
- Transaction types
- Cancellations and adjustments
- Data quality

## Key Findings

The analysis identified several notable patterns in the dataset.

The top 10 customers account for approximately 14.06% of total revenue.

The top 10 products account for approximately 8% of total revenue.

The top 5 countries contribute approximately 95.04% of total revenue.

Approximately 72.26% of customers are repeat customers based on the project's repeat-customer definition.

Return transactions represent approximately 0.34% of sale transactions.

These findings, along with additional observations and data-quality considerations, are presented in the Findings section of the dashboard.

## Data Quality

Data quality was treated as an important part of the analysis rather than assuming the original dataset was perfectly clean.

The project includes checks for duplicate transactions, missing customer IDs, missing product descriptions, zero-price transactions, cancellations, returns, adjustments, special transactions, and other non-standard transaction types.

Relevant data-quality limitations and analytical caveats are also documented within the dashboard.

## Project Structure


UK Retail Dashboard/
│
├── Assets/
├── Components/
├── Pages_Views/
├── SQL/
├── Style/
├── app.py
├── db_connection.py
├── requirements.txt
└── STYLE_NOTE.txt

Running the Project Locally

Clone the repository and navigate into the project directory:

git clone https://github.com/palsingharjun5-web/uk-online-retail-analytics.git
cd uk-online-retail-analytics

Install the required dependencies:

pip install -r requirements.txt

The dashboard requires a PostgreSQL database containing the project's analytical tables and views.

Database credentials should be stored locally using Streamlit secrets and should not be committed to GitHub.

After configuring the database connection, run the dashboard with:

python -m streamlit run app.py
Security

Database credentials and other sensitive configuration files are intentionally excluded from the repository.

The project's .gitignore prevents local secrets, datasets, virtual environments, and backup files from being committed.

Project Status

The analytical workflow and interactive dashboard are complete.

The project is currently being prepared for deployment and portfolio presentation.

Author

Arjun Pal Singh

B.Com (Computer Applications)
Osmania University

This project was developed as part of my data analytics learning and portfolio journey.
