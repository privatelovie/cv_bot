# CV Job Vacancy Bot

Upload your CV and get currently available job vacancies ranked by relevance.

## What this app does
- Accepts CV upload in `PDF`, `DOCX`, or `TXT`
- Extracts text and detects skills
- Pulls **live vacancies** from public job APIs:
  - Remotive
  - Arbeitnow
- Cleans HTML-heavy job descriptions for better readability and ranking
- Ranks vacancies against your CV using TF-IDF + cosine similarity
- Shows top matched jobs with direct links

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

## Run tests
```bash
python -m unittest -v
```

## Notes
- If live APIs are temporarily unavailable, the app falls back to sample vacancies so the app still works.
- You can add a manual search keyword in the sidebar to steer matching (for example: `backend engineer`, `data analyst`).
