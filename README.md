# 🚀 NoteGenius

NoteGenius is an AI-powered tool that extracts key insights, concise summaries, and interactive quizzes from your uploaded documents — making learning smarter and faster.

---

## 🌟 Features

- Upload `.txt`, `.pdf`, or `.docx` files  
- AI-generated **paragraph summaries**
- Extract **key insights** beyond just restating facts
- Generate **interactive quizzes** to test your knowledge
- Clean, simple UI built with Streamlit

---

## Tech stack

- **Backend**: FastAPI, Ollama (Mistral model)  
- **Frontend**: Streamlit  
- **Libraries**: PyPDF2, python-docx, requests  

### Installation 

1️⃣ **Clone the repo** 

```bash
git clone https://github.com/DazNeh/NoteGenius.git
cd NoteGenius
```

Download Ollama then run
```bash
Ollama pull mistral
```

2️⃣ **Setup the Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then start the backend server:

```bash
uvicorn app:app --reload --port 8000
```

3️⃣ **Setup the Frontend**

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then start the frontend app:

```bash
streamlit run app.py
```
