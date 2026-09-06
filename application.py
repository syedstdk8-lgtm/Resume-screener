import streamlit as st
import sentence_transformers as s_t
from pypdf import PdfReader

st.set_page_config(page_title = "Resume Screener", layout = "wide")
st.title("Resume screening system")
st.caption("upload the resume to rank them according to the job description")

def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
        return text

def specificaions():
    st.subheader("educational qualifications")
    st.text_area("enter the educational qualifications here", height = 100)
    st.button("Submit")

    if st.button("submit"):
        st.success("submitted successfullly")

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