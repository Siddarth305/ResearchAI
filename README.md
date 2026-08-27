# ResearchAI

ResearchAI is an AI-powered research discovery app for finding relevant academic papers, exploring topic clusters, and saving useful papers for later.

## Live Demo

[Open ResearchAI](https://researchai-ham2.onrender.com/)

## Features

- Search research topics with semantic relevance ranking
- Retrieve paper metadata from arXiv and OpenAlex
- Group results into research topic clusters
- Filter results by category and sort by relevance or publication date
- Open paper landing pages and available PDF links
- Save papers to a personal browser-based library
- Responsive dark and light themes

## Tech Stack

- Python and Flask
- scikit-learn and NumPy for ranking and clustering
- arXiv and OpenAlex APIs for research data
- HTML, CSS, and JavaScript for the frontend
- Gunicorn for production deployment

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Siddarth305/ResearchAI.git
cd ResearchAI
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the development server

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Production Start

```bash
gunicorn app:app
```

## Project Structure

```text
ResearchAI/
├── app.py                 Flask application and API routes
├── ml/model.py            Paper ranking and topic clustering
├── requirements.txt       Python dependencies
├── static/
│   ├── script.js          Frontend behavior
│   └── style.css          Application styling
├── templates/index.html   Main application page
└── data/                  Application data directory
```

## API

- `GET /api/search?query=<topic>` searches for relevant research papers.

## Notes

Saved papers are stored in the browser's `localStorage`, so the library is specific to the browser and device where papers are saved.
