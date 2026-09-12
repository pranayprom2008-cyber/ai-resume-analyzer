"""
AI Resume Analyzer & ATS Optimizer - FastAPI Application
Provides REST endpoints for resume parsing, keyword matching, semantic similarity,
ATS scoring, and preset job profile loading.
"""

import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from parser import ResumeParser
from skill_extractor import SkillExtractor
from ats_scorer import ATSScorer

app = FastAPI(
    title="AI Resume Analyzer & ATS Optimization Engine",
    description="Engineered for 2nd-year AI/ML students to audit resumes against ATS algorithms, analyze skill gaps, and maximize placement evaluations.",
    version="1.0.0"
)

# Enable CORS for local testing or cross-origin client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard preset job descriptions for instant demonstrations
SAMPLE_JOB_PRESETS = {
    "aiml_intern": {
        "title": "AI/ML Engineering Intern",
        "category": "AI / Machine Learning",
        "description": """Job Title: AI/ML Engineering Intern
Department: Machine Learning & Applied AI
Location: Bengaluru / Remote

About the Role:
We are seeking an enthusiastic AI/ML Engineering Intern to help design, train, and deploy machine learning models. You will collaborate with senior engineers to build intelligent pipelines, optimize models for inference, and integrate algorithms into production APIs.

Requirements:
- Strong programming proficiency in Python and solid understanding of Object-Oriented Programming (OOP).
- Hands-on experience with Machine Learning and Deep Learning frameworks: PyTorch, TensorFlow, or Scikit-Learn.
- Knowledge of Computer Vision (OpenCV) or Natural Language Processing (NLP).
- Familiarity with data analysis libraries: Pandas, NumPy, and Matplotlib.
- Experience with building or consuming REST APIs using FastAPI or Flask.
- Foundational grasp of Data Structures, Algorithms, and System Design concepts.
- Understanding of Git/GitHub version control, Docker containerization, and Linux environments.
- Exposure to Large Language Models (LLMs) and Vector Databases (e.g. ChromaDB) is a plus.
"""
    },
    "fullstack_developer": {
        "title": "Junior Full-Stack Web Developer",
        "category": "Software Engineering",
        "description": """Job Title: Junior Full-Stack Developer
Department: Engineering

Responsibilities:
- Build responsive, modern web user interfaces using React, TypeScript, and Tailwind CSS.
- Develop robust, scalable REST APIs using Python (FastAPI/Django) or Node.js (Express).
- Design and optimize relational database schemas using PostgreSQL or MySQL with ORM tools (Prisma / SQLAlchemy).
- Integrate user authentication, OAuth, and role-based access control.
- Write unit tests and maintain CI/CD pipelines via GitHub Actions.
- Collaborate using Agile and Scrum methodologies.

Qualifications:
- Proficiency in JavaScript, TypeScript, HTML5, and CSS3.
- Hands-on project experience with React and state management (Redux / Zustand).
- Working knowledge of SQL, PostgreSQL, Docker, and Git.
- Strong problem-solving and algorithmic thinking.
"""
    },
    "data_scientist": {
        "title": "Data Science & Analytics Trainee",
        "category": "Data Science",
        "description": """Job Title: Data Science Trainee
Department: Analytics & Business Intelligence

Key Skills Required:
- Proficiency in Python, SQL, and exploratory data analysis (EDA).
- In-depth knowledge of statistics, probability, regression, and classification algorithms.
- Experience with Scikit-Learn, Pandas, NumPy, Seaborn, and Matplotlib.
- Experience creating dashboards in Tableau or Power BI.
- Ability to engineer features, handle missing data, and evaluate models using Precision, Recall, F1-Score, and ROC-AUC.
- Strong communication skills to present data insights to technical and non-technical stakeholders.
"""
    }
}

SAMPLE_RESUME_TEXT = """M PRANAY
pranayprom2008@gmail.com | +91 98765 43210 | Bengaluru, India
GitHub: https://github.com/pranayprom2008-cyber | LinkedIn: https://linkedin.com/in/pranay-ai

EDUCATION
Bachelor of Technology in Artificial Intelligence and Machine Learning (2023 - 2027)
GPA: 8.8 / 10.0
Relevant Coursework: Data Structures & Algorithms, Operating Systems, Machine Learning, Deep Learning, DBMS, Computer Networks

TECHNICAL SKILLS
- Programming Languages: Python, C, C++, Java, JavaScript, TypeScript, SQL
- Machine Learning & AI: PyTorch, Scikit-Learn, OpenCV, Pandas, NumPy, SciPy, Matplotlib
- Web & Frameworks: FastAPI, React, Next.js, HTML5, CSS3, Tailwind CSS, Node.js
- Databases & Cloud: PostgreSQL, SQLite, Supabase, Prisma, Docker, Git, GitHub

PROJECTS
1. Chicken Farm Pro - Enterprise Poultry Management Platform
- Architected a full-stack Next.js and Prisma system with Supabase backend and Google OAuth 2.0 authentication.
- Built ChickAI assistant using Google Gemini API to analyze flock mortality patterns, reducing diagnostic delay by 45%.
- Implemented real-time financial tracking and automated PDF report generation for 500+ daily operational records.

2. Real-Time Vision & Object Detection Pipeline
- Engineered a high-throughput video processing pipeline using OpenCV and deep learning models.
- Achieved consistent 50+ FPS webcam inference with low-latency bounding box tracking and confidence scoring.
- Benchmarked frame throughput and optimized memory buffers, reducing processing latency by 30%.

3. Hand Gesture Air-Keyboard & Virtual Controller
- Developed a contactless computer vision interface utilizing MediaPipe hand tracking and PyAutoGUI.
- Built dual-hand spatial gesture recognition for virtual typing and mouse cursor navigation without physical hardware.

ACHIEVEMENTS & CERTIFICATIONS
- Active open-source contributor with 10+ software projects across GitHub.
- Finalist in College Technical Hackathon for autonomous computer vision prototypes.
"""

@app.get("/api/health")
def health_check():
    """Returns system status and supported feature modules."""
    return {
        "status": "healthy",
        "service": "AI Resume Analyzer & ATS Engine",
        "version": "1.0.0",
        "features": {
            "pdf_parsing": True,
            "skill_taxonomy_count": len(SkillExtractor.TAXONOMY),
            "semantic_tfidf": True,
            "ats_scoring": True,
            "heuristics": True
        }
    }

@app.get("/api/presets")
def get_presets():
    """Returns curated job description presets for immediate testing."""
    return SAMPLE_JOB_PRESETS

@app.get("/api/sample-resume")
def get_sample_resume():
    """Returns a realistic student resume for one-click testing."""
    return {
        "text": SAMPLE_RESUME_TEXT,
        "filename": "sample_pranay_resume.txt"
    }

@app.post("/api/analyze")
async def analyze_resume(
    job_description: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None)
):
    """
    Core analysis endpoint.
    Accepts an uploaded PDF resume or direct text, compares it against the job description,
    and returns comprehensive ATS metrics, skill gaps, and improvement suggestions.
    """
    if not job_description or len(job_description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Please provide a valid job description (at least 30 characters).")

    raw_text = ""
    is_pdf = False

    # Process file upload if provided
    if resume_file and resume_file.filename:
        filename = resume_file.filename.lower()
        if not (filename.endswith(".pdf") or filename.endswith(".txt")):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are currently supported.")

        file_bytes = await resume_file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        if filename.endswith(".pdf"):
            is_pdf = True
            try:
                parsed_data = ResumeParser.parse(file_bytes, is_pdf=True)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"PDF extraction error: {str(e)}")
        else:
            text_decoded = file_bytes.decode("utf-8", errors="ignore")
            parsed_data = ResumeParser.parse(text_decoded, is_pdf=False)
    elif resume_text and len(resume_text.strip()) > 30:
        parsed_data = ResumeParser.parse(resume_text, is_pdf=False)
    else:
        raise HTTPException(status_code=400, detail="Please upload a PDF resume or paste resume text.")

    # Calculate ATS score and detailed analytics
    results = ATSScorer.score_resume(
        resume_text=parsed_data["cleaned_text"],
        job_description=job_description,
        parsed_resume=parsed_data
    )

    # Attach parsing metadata
    results["candidate_preview"] = {
        "detected_sections": parsed_data["detected_sections"],
        "word_count": parsed_data["word_count"],
        "snippet": parsed_data["cleaned_text"][:350] + "..." if len(parsed_data["cleaned_text"]) > 350 else parsed_data["cleaned_text"]
    }

    return JSONResponse(content=results)

# Mount frontend static files if directory exists
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
