from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from docx import Document
import ollama
import tempfile
import os
import io
import json

app = FastAPI()

# For development we accept any origin; lock this down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def extract_text(file: UploadFile) -> str:
    """
    Load .txt, .pdf, or .docx into a single text blob.
    Raises 415 if the format isn’t supported.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    data = await file.read()

    if ext == ".txt":
        return data.decode("utf-8")

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        # python-docx needs a filesystem path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(data)
            path = tmp.name
        try:
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        finally:
            os.unlink(path)

    raise HTTPException(status_code=415, detail="Unsupported file type")

def clean_bullets(text: str) -> list[str]:
    """
    Turn model output into a list of tidy bullet points.
    Strips any leading numbers or punctuation.
    """
    points = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("•-–").lstrip("0123456789. ").strip()
        if stripped:
            points.append(stripped)
    return points

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    action: str = Form("all")  # "all", "summary", "insights", or "quiz"
):
    """
    1. Extract the document text
    2. Always produce a paragraph summary (3–5 sentences)
    3. Optionally generate insights and/or a quiz from that summary
    """
    # 1) Pull text out of the file
    text = await extract_text(file)
    results: dict = {}

    # 2) Always run paragraph summary so we have it for insights/quiz
    prompt_summary = (
        "Write a concise paragraph (3–5 sentences) capturing the essence "
        "of these notes—no bullets or numbering:\n\n" + text
    )
    resp_summary = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt_summary}]
    )
    summary_text = resp_summary.message.content.strip()
    results["summary"] = summary_text

    # 3) Insights (if requested)
    if action in ("insights", "all"):
        prompt_insights = (
            f"Here’s the paragraph summary:\n\n{summary_text}\n\n"
            "Now give me 5 insights that go beyond restating facts—"
            "real-world uses, surprising implications, or why it matters. "
            "Return clean bullet points."
        )
        resp_ins = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt_insights}]
        )
        results["insights"] = clean_bullets(resp_ins.message.content)

    # 4) Quiz (if requested)
    if action in ("quiz", "all"):
        # force only JSON array back, then regex-extract
        prompt_quiz = (
            f"Based on the summary above, generate exactly 5 multiple-choice questions. "
            "Output *only* a JSON array where each element has: question, options (list), answer_index.\n\n"
            + summary_text
        )
        resp_quiz = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt_quiz}]
        )
        raw = resp_quiz.message.content.strip()

        # pull out the first [...] block in case of extra text
        import re
        m = re.search(r"(\[\s*\{.*\}\s*\])", raw, flags=re.DOTALL)
        json_text = m.group(1) if m else raw

        try:
            results["quiz"] = json.loads(json_text)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Quiz JSON parse error. Model output:\n{raw}"
            )

    return results