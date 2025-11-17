import io
import pdfplumber
from docx import Document
DOMAIN_KEYWORDS = {
    'web_development': ['django', 'flask', 'react', 'javascript', 'html', 'css', 'rest', 'api', 'template'],
    'mobile_development': ['android', 'ios', 'flutter', 'react native', 'kotlin', 'swift'],
    'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'],
    'devops': ['aws', 'docker', 'kubernetes', 'ci/cd', 'jenkins', 'ansible'],
    'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite']
}
def extract_text_from_pdf(file_obj):
    text = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ''
            text.append(page_text)
    return '\n'.join(text)
def extract_text_from_docx(file_obj):
    doc = Document(file_obj)# file_obj is an UploadedFile-like object
    paragraphs = [p.text for p in doc.paragraphs]
    return '\n'.join(paragraphs)
def extract_text_from_txt(file_obj):
    return file_obj.read().decode(errors='ignore')
def extract_resume_text(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):# pdfplumber expects a file-like object; Django's InMemoryUploadedFile works
        return extract_text_from_pdf(uploaded_file)
    elif name.endswith('.docx'):
        return extract_text_from_docx(uploaded_file)
    else:
        return extract_text_from_txt(uploaded_file)
def detect_domain_from_text(text):
    """
    Simple keyword counting classifier.
    Returns the best-matching domain (string) or 'general' if none matched.
    """
    text_lower = text.lower()
    scores = {domain: 0 for domain in DOMAIN_KEYWORDS.keys()}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += text_lower.count(kw)
    best = max(scores.items(), key=lambda kv: kv[1]) # pick highest score
    if best[1] == 0:
        return 'general'
    return best[0]
