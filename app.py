import streamlit as st
import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, util
import pandas as pd

# Page setup
st.set_page_config(page_title="AI Resume Screener", layout="wide")
st.title("📄 AI Resume Screening & Ranking System")
st.caption("Upload multiple candidate resumes to rank them against a job description.")

def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s@.+-]", "", text)
    return text.strip().lower()

def extract_skills(text: str, skill_set: set) -> set:
    clean_resume = set(re.findall(r"\b[a-zA-Z0-9+#.-]+\b", text.lower()))
    return skill_set.intersection(clean_resume)

def score_resume(resume_text: str, jd_text: str, target_skills: set):
    clean_res = clean_text(resume_text)
    clean_jd = clean_text(jd_text)

    
    res_embedding = model.encode(clean_res, convert_to_tensor=True)
    jd_embedding = model.encode(clean_jd, convert_to_tensor=True)
    semantic_sim = float(util.cos_sim(res_embedding, jd_embedding)[0][0])

    # 2. Hard Skill Match
    matched_skills = extract_skills(clean_res, target_skills)
    skill_coverage = len(matched_skills) / len(target_skills) if target_skills else 0.0

    # 3. Composite Score (60% semantic, 40% hard skill presence)
    final_score = (0.6 * semantic_sim) + (0.4 * skill_coverage)
    final_score = max(0.0, min(final_score, 1.0)) * 100

    return {
        "final_score": round(final_score, 2),
        "semantic_similarity": round(semantic_sim * 100, 2),
        "matched_skills": ", ".join(matched_skills) if matched_skills else "None",
        "missing_skills": ", ".join(target_skills - matched_skills) if (target_skills - matched_skills) else "None"
    }

# UI Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Requirements")
    job_description = st.text_area(
        "Job Description",
        placeholder="Paste JD text here (responsibilities, requirements, qualifications)...",
        height=200
    )
    skills_input = st.text_input(
        "Mandatory Skills (comma-separated)",
        placeholder="python, fastapi, docker, aws, sql"
    )

with col2:
    st.subheader("2. Candidate Resumes")
    uploaded_files = st.file_uploader(
        "Upload PDF Resumes",
        type=["pdf"],
        accept_multiple_files=True
    )

st.divider()

# Processing
if st.button("Screen and Rank Resumes", type="primary"):
    if not job_description.strip():
        st.warning("Please provide a Job Description.")
    elif not uploaded_files:
        st.warning("Please upload at least one PDF resume.")
    else:
        target_skills = {s.strip().lower() for s in skills_input.split(",") if s.strip()}
        
        results = []
        with st.spinner("Analyzing candidate profiles..."):
            for file in uploaded_files:
                try:
                    pdf_text = extract_text_from_pdf(file)
                    metrics = score_resume(pdf_text, job_description, target_skills)
                    results.append({
                        "Candidate File": file.name,
                        "Overall Match (%)": metrics["final_score"],
                        "Semantic Score (%)": metrics["semantic_similarity"],
                        "Matched Skills": metrics["matched_skills"],
                        "Missing Skills": metrics["missing_skills"],
                    })
                except Exception as e:
                    st.error(f"Failed to parse {file.name}: {str(e)}")

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values(by="Overall Match (%)", ascending=False).reset_index(drop=True)
            df.index += 1  # 1-based rank indexing

            st.subheader("Candidate Rankings")
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Overall Match (%)": st.column_config.ProgressColumn(
                        "Overall Match",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                }
            )