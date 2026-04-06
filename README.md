# Citizen Helper - Legal AI Assistant

A comprehensive platform for legal assistance, featuring a modern AI-powered chat interface and a robust data pipeline for Vietnamese legal documents.

## 🚀 Project Overview

This project consists of two main parts:
1.  **Frontend**: A modern, responsive React application (Vite + Tailwind CSS).
2.  **AI Engine**: A data pipeline for crawling, cleaning, and processing legal information.

---

## 💻 Frontend Setup (Luật Sư AI)

The frontend is located in the `frontend` directory.

### Prerequisites
- Node.js (v18+)
- npm or yarn

### Steps to Run
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
4.  Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:5173`).

---

## 🤖 AI Engine & Crawlers

The AI and data processing logic is located in the `ai` directory.

### Structure
- **Crawlers**: Located in `ai/crawler/`. Scripts to fetch legal data from various sources (Cong Bao, MOJ, VBPL, etc.).
- **Data Processing**: Located in `ai/ai_engine/cleaning/`. Includes scripts for noise removal, article segmentation, and vector database indexing.

### How to Run Crawlers
You can run individual crawler scripts using Python. For example:
```bash
python ai/crawler/vbpl_crawler.py
```

---

## 📁 Data Management & Git

Large data files and processed datasets are excluded from Git to keep the repository lightweight.

**Ignored Paths:**
- `ai/ai_engine/raw/`: Original downloaded files.
- `ai/ai_engine/cleaning/*.jsonl`: Processed datasets.
- `ai/ai_engine/cleaning/*.joblib`: Pre-computed indices/models.
- `ai/ai_engine/cleaning/law_vector_db_pro/`: Vector database files.
- `ai/ai_engine/cleaning/law_data/`: Extracted data folders.

Please ensure you have the necessary data locally before running processing scripts.
