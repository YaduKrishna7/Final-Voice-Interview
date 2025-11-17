from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from .resume_parser import extract_text_from_resume

# Load once
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_resume_score(job_description, resume_file):
    try:
        resume_text = extract_text_from_resume(resume_file.path)
        if not resume_text:
            return 0.0
        job_emb = model.encode(job_description, convert_to_tensor=True)
        resume_emb = model.encode(resume_text, convert_to_tensor=True)
        score = cos_sim(job_emb, resume_emb).item()
        return round(score * 100, 2)  # percentage
    except Exception:
        return 0.0
