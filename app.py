import io
import re
from dataclasses import dataclass
from html import unescape
from typing import Iterable, List

import pdfplumber
import requests
import streamlit as st
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str


SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "node", "sql", "postgresql", "mysql",
    "aws", "azure", "gcp", "docker", "kubernetes", "machine learning", "data analysis", "fastapi",
    "django", "flask", "git", "linux", "excel", "power bi", "tableau", "nlp", "pandas",
    "numpy", "spark", "hadoop", "communication", "project management", "c++", "c#", "golang",
]


def clean_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text or "")
    normalized = re.sub(r"\s+", " ", unescape(without_tags)).strip()
    return normalized


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_cv_text(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    suffix = uploaded_file.name.lower().split(".")[-1]

    if suffix == "pdf":
        return extract_text_from_pdf(file_bytes)
    if suffix == "docx":
        return extract_text_from_docx(file_bytes)
    if suffix == "txt":
        return file_bytes.decode("utf-8", errors="ignore")

    raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT.")


def extract_skills(cv_text: str) -> List[str]:
    lowered = cv_text.lower()
    found = [skill for skill in SKILL_KEYWORDS if re.search(rf"\b{re.escape(skill)}\b", lowered)]
    return sorted(set(found))


def fetch_jobs_remotive(query: str, limit: int = 40) -> List[Job]:
    url = "https://remotive.com/api/remote-jobs"
    try:
        response = requests.get(url, params={"search": query}, timeout=25)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return []

    jobs = []
    for item in payload.get("jobs", [])[:limit]:
        jobs.append(
            Job(
                title=item.get("title", "Unknown Title"),
                company=item.get("company_name", "Unknown Company"),
                location=item.get("candidate_required_location", "Remote/Unknown"),
                description=clean_text(item.get("description", "")),
                url=item.get("url", ""),
                source="Remotive",
            )
        )
    return jobs


def fetch_jobs_arbeitnow(limit: int = 40) -> List[Job]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return []

    jobs = []
    for item in payload.get("data", [])[:limit]:
        jobs.append(
            Job(
                title=item.get("title", "Unknown Title"),
                company=item.get("company_name", "Unknown Company"),
                location=item.get("location", "Unknown Location"),
                description=clean_text(item.get("description", "")),
                url=item.get("url", ""),
                source="Arbeitnow",
            )
        )
    return jobs


def deduplicate_jobs(jobs: Iterable[Job]) -> List[Job]:
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job.title.strip().lower(), job.company.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)
    return unique_jobs


def rank_jobs(cv_text: str, jobs: List[Job]) -> List[tuple[Job, float]]:
    if not jobs:
        return []

    corpus = [cv_text] + [f"{job.title}. {job.description}" for job in jobs]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return sorted(zip(jobs, similarities), key=lambda x: x[1], reverse=True)


def fallback_jobs() -> List[Job]:
    return [
        Job("Backend Python Engineer", "ExampleTech", "Remote", "Build microservices with Python, FastAPI, PostgreSQL, and Docker.", "https://example.com/jobs/backend", "Sample"),
        Job("Data Analyst", "ExampleData", "USA", "Analyze business KPIs using SQL, Python, Tableau, and Excel.", "https://example.com/jobs/analyst", "Sample"),
        Job("ML Engineer", "ExampleAI", "Remote", "Train and deploy machine learning pipelines and NLP models.", "https://example.com/jobs/ml", "Sample"),
    ]


def main() -> None:
    st.set_page_config(page_title="CV Job Vacancy Bot", page_icon="🤖")
    st.title("🤖 CV Job Vacancy Bot")
    st.write("Upload your CV and get currently available job vacancies matched to your profile.")

    with st.sidebar:
        st.header("Options")
        top_k = st.slider("Number of matches", min_value=5, max_value=50, value=15)
        search_override = st.text_input("Optional job search keyword", placeholder="e.g. data engineer")

    uploaded_file = st.file_uploader("Upload CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file:
        try:
            cv_text = extract_cv_text(uploaded_file)
            if len(cv_text.strip()) < 100:
                st.warning("CV text looks too short. Please upload a detailed CV.")
                return
        except Exception as e:
            st.error(f"Could not read CV: {e}")
            return

        skills = extract_skills(cv_text)
        st.subheader("Detected skills from your CV")
        st.write(", ".join(skills) if skills else "No common skills detected; using full CV text for matching.")

        query = search_override.strip() or " ".join(skills[:10]) or "software engineer"

        with st.spinner("Fetching live vacancies from public job APIs..."):
            remotive_jobs = fetch_jobs_remotive(query=query, limit=80)
            arbeitnow_jobs = fetch_jobs_arbeitnow(limit=80)
            jobs = deduplicate_jobs(remotive_jobs + arbeitnow_jobs)

        source_note = "Remotive + Arbeitnow"
        if not jobs:
            jobs = fallback_jobs()
            source_note = "Built-in sample jobs (live APIs unavailable right now)"

        ranked = rank_jobs(cv_text, jobs)[:top_k]

        st.subheader(f"Top {len(ranked)} matching vacancies")
        st.caption(f"Job source: {source_note}")

        for i, (job, score) in enumerate(ranked, start=1):
            st.markdown(f"### {i}. {job.title}")
            st.write(f"**Company:** {job.company}")
            st.write(f"**Location:** {job.location}")
            st.write(f"**Source:** {job.source}")
            st.write(f"**Match score:** {score * 100:.1f}%")
            st.write(job.description[:600] + ("..." if len(job.description) > 600 else ""))
            if job.url:
                st.markdown(f"[Open Vacancy]({job.url})")
            st.divider()


if __name__ == "__main__":
    main()
