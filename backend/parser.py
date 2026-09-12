"""
Resume Parser Module
Extracts text from PDF documents, detects contact information,
normalizes formatting, and segments the resume into standard ATS sections.
"""

import re
import io
from typing import Dict, Any, Optional
from pypdf import PdfReader


class ResumeParser:
    """Robust parser for resumes in PDF and plain text formats."""

    SECTION_PATTERNS = {
        "contact_info": [r"\bcontact\b", r"\bpersonal details\b"],
        "summary": [r"\bsummary\b", r"\bprofessional summary\b", r"\bprofile\b", r"\bobjective\b", r"\babout me\b"],
        "education": [r"\beducation\b", r"\bacademics?\b", r"\bacademic background\b", r"\bqualifications?\b"],
        "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcore competencies\b", r"\btechnologies\b", r"\btools\b"],
        "experience": [r"\bexperience\b", r"\bwork experience\b", r"\bemployment\b", r"\binternships?\b", r"\bprofessional experience\b"],
        "projects": [r"\bprojects\b", r"\bacademic projects\b", r"\bkey projects\b", r"\bpersonal projects\b"],
        "certifications": [r"\bcertifications?\b", r"\blicenses?\b", r"\bcourses?\b", r"\btrainings?\b"],
        "achievements": [r"\bachievements?\b", r"\bawards?\b", r"\bhono[u]?rs\b", r"\bextracurricular\b"]
    }

    @staticmethod
    def extract_text_from_pdf(file_source: Any) -> str:
        """
        Extract raw text from a PDF file path or bytes buffer.
        Handles multi-page documents and page breaks.
        """
        extracted_pages = []
        try:
            if isinstance(file_source, bytes):
                reader = PdfReader(io.BytesIO(file_source))
            elif isinstance(file_source, str):
                reader = PdfReader(file_source)
            else:
                reader = PdfReader(file_source)

            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)

            full_text = "\n\n".join(extracted_pages).strip()
            return full_text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans unicode noise, normalizes bullet points and whitespace.
        Preserves punctuation necessary for sentence and email extraction.
        """
        if not text:
            return ""

        bullets = ["•", "·", "▪", "●", "►", "■", "★", "–", "—", "✔", ""]
        cleaned = text
        for b in bullets:
            cleaned = cleaned.replace(b, " - ")

        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        """
        Extracts candidate contact details using regex patterns.
        """
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        email_match = re.search(email_pattern, text)
        email = email_match.group(0) if email_match else None

        phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        phone_match = re.search(phone_pattern, text)
        phone = phone_match.group(0) if phone_match else None

        linkedin_pattern = r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([A-Za-z0-9_-]+)"
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        github_pattern = r"(?:https?:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9_-]+)"
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None

        portfolio_pattern = r"(?:https?:\/\/)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+(?:com|io|dev|org|me|net|tech)(?:\/[^\s]*)?"
        portfolio = None
        for match in re.finditer(portfolio_pattern, text):
            url = match.group(0)
            if "linkedin.com" not in url.lower() and "github.com" not in url.lower():
                portfolio = url
                break

        return {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "portfolio": portfolio
        }

    @classmethod
    def segment_sections(cls, text: str) -> Dict[str, str]:
        """
        Segments the resume text into logical sections based on detected headers.
        """
        lines = text.splitlines()
        sections = {key: [] for key in cls.SECTION_PATTERNS}
        sections["header"] = []

        current_section = "header"

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            is_header = False
            if len(line_stripped) <= 40:
                for section_name, patterns in cls.SECTION_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, line_stripped, re.IGNORECASE):
                            current_section = section_name
                            is_header = True
                            break
                    if is_header:
                        break

            if not is_header:
                sections[current_section].append(line_stripped)

        return {key: "\n".join(val) for key, val in sections.items() if val}

    @classmethod
    def parse(cls, file_source: Any, is_pdf: bool = True) -> Dict[str, Any]:
        """
        Complete parsing pipeline returning text, contacts, sections, and metadata.
        """
        if is_pdf:
            raw_text = cls.extract_text_from_pdf(file_source)
        else:
            raw_text = str(file_source)

        cleaned = cls.clean_text(raw_text)
        contacts = cls.extract_contact_info(cleaned)
        sections = cls.segment_sections(cleaned)
        word_count = len(cleaned.split())

        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned,
            "contact_info": contacts,
            "sections": sections,
            "word_count": word_count,
            "detected_sections": list(sections.keys())
        }
