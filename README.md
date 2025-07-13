# Ethiopian Medical Business Data Platform

## Project Overview

This project aims to build a robust, end-to-end data platform to extract, process, and analyze data related to Ethiopian medical businesses, primarily sourced from public Telegram channels. The platform utilizes a modern ELT (Extract, Load, Transform) framework, leveraging Docker for containerization, PostgreSQL as a data warehouse, dbt for data transformations, YOLOv8 for image-based data enrichment, and FastAPI to expose analytical insights via an API. Pipeline orchestration is managed by Dagster.

The goal is to answer key business questions such as:
* What are the top 10 most frequently mentioned medical products or drugs across all channels?
* How does the price or availability of a specific product vary across different channels?
* Which channels have the most visual content (e.g., images of pills vs. creams)?
* What are the daily and weekly trends in posting volume for health-related topics?

## Architecture

The platform follows a layered approach:
1.  **Data Scraping:** Python scripts utilizing Telegram API (`Telethon`) to extract raw messages and images.
2.  **Data Lake:** Raw, unaltered data is stored as JSON files in a partitioned directory structure (`data/raw/`).
3.  **Data Warehouse (PostgreSQL):** Raw data is loaded into a PostgreSQL database, serving as the data warehouse.
4.  **Data Transformation (dbt):** Data is cleaned, restructured, and modeled into a dimensional star schema (Fact and Dimension tables) using dbt, ensuring data reliability and analytical optimization.
5.  **Data Enrichment (YOLOv8):** Images collected from Telegram are processed using a pre-trained YOLOv8 model for object detection. Detected objects (e.g., "pill," "cream") and their confidence scores are integrated into the data warehouse.
6.  **Analytical API (FastAPI):** A FastAPI application provides analytical endpoints to query the transformed data and deliver insights.
7.  **Orchestration (Dagster):** The entire ELT pipeline is orchestrated using Dagster, providing a robust, observable, and schedulable workflow.
8.  **Containerization (Docker):** The entire application stack (Python environment, PostgreSQL, dbt, FastAPI) is containerized using Docker and Docker Compose for reproducible and portable deployment.
