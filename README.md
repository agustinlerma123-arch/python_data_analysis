# 🚚 Operations, Delivery & Returns Analytics Dashboard

An end-to-end data cleaning, operational logistics, and returns analytics capstone project built with Python and Streamlit. 
This repository contains automated data hygiene scripts, master transactional datasets, performance charts, and an interactive web application designed to evaluate supply chain efficiency and product return patterns.

---

## 📋 Executive Summary
* This project delivers an end-to-end data cleaning, operational logistics, and returns analytics pipeline built using Python and Streamlit.
* Integrates four operational datasets (`orders`, `products`, `shipments`, and `returns`), totaling 15,000+ transaction records.
* Automated data hygiene protocols handled missing values, standardized product categories, reconciled mixed date formats, and stripped currency strings.
* Implemented foreign key integrity validation to identify and quarantine orphan records across transactional relationships.
* Evaluated core delivery KPIs, discovering an overall average lead time of 4.0 days with a 77.9% successful delivery rate.
* Tracked operational bottlenecks, showing 18.0% of shipments in transit and 1.1% lost in transit across partner couriers.
* Analyzed an overall return rate of 8.00%, identifying customer sentiment ("Changed Mind") and product defects as primary return drivers.
* Visualized key operational metrics via 5 interactive Plotly charts, enabling real-time filtering by courier and product category.

---

## 📂 Repository File Structure

├── README.md
├── app.py
├── Executive_Summary.txt
├── Cleaned_orders.csv
├── Cleaned_products.csv
├── Cleaned_shipments.csv
├── Cleaned_returns.csv
└── charts/
    ├── lead-time-distribution-days.png
    ├── shipment-status-share.png
    ├── average-lead-time-by-courier-days.png
    ├── return-volume-by-reason.png
    └── return-rate-percentage-by-category.png