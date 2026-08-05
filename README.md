# Logistics Cost & Macro Trade Analytics

A lightweight pipeline and dashboard repository for tracking high-frequency global shipping costs, energy prices, and macroeconomic trade indicators (including Israel Central Bureau of Statistics foreign trade data and live ticker performance).

## Overview

This project automates the collection and processing of logistics and financial data to serve as an early-warning system for supply chain cost inflation. It combines macroeconomic trade figures with high-frequency financial indicators (such as shipping equities, freight rates, and fuel prices) into a unified dataset.

## Repository Structure

- `app.py`: Interactive Streamlit web application providing multi-view dashboards for shipping tickers, monthly trade trends, and bilateral trade explorer.
- `cbs_processor.py`: Parses and cleans raw monthly trade Excel files from the Central Bureau of Statistics (CBS) into standardized formats.
- `data/`: Directory for storing local raw trade data files (`ta2`, `ta3`, `td1`, `te4`).
- `.github/workflows/`: Contains GitHub Actions configuration for automated data collection and updates.
- `requirements.txt`: Version-agnostic project dependencies.

## Installation & Setup

1. Clone the repository:
   git clone https://github.com/AshKatzEm/logistics-cost.git
   cd logistics-cost

2. Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

3. Install dependencies:
   pip install --upgrade pip
   pip install -r requirements.txt

## Usage

Place your CBS monthly trade Excel files inside the `data/` directory, then run the processing script:
python cbs_processor.py

## Streamlit Dashboard

To explore the datasets interactively through a web interface, launch the Streamlit app locally:

streamlit run app.py

The dashboard includes:
- **Overview & Summary:** High-level metrics card layout and recent shipping index trends.
- **Shipping Ticker Dashboard:** Multi-select chart tracking high-frequency shipping rates, energy benchmarks, carrier equities, and foreign exchange rates.
- **Monthly Trade Dashboard:** Visualizations for import/export volumes, Fisher volume indices, and country-specific bilateral trade trends.
- **Raw Dataset Inspector:** Full raw data exploration with native CSV download utilities.

## Automation

The project includes GitHub Actions workflows that automatically handle periodic data fetches and repository updates. Ensure your requirements and python versions align in your workflow configurations.