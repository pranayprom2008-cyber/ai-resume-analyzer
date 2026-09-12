"""
ATS Scorer Module
Calculates multi-dimensional ATS match scores using Scikit-Learn TF-IDF,
cosine similarity, skill gap analysis, section completeness, and metric heuristics.
"""

import re
from typing import Dict, List, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parser import ResumeParser
from skill_extractor import SkillExtractor


class ATSScorer:
    """Computes comprehensive ATS compatibility, skill gaps, and optimization advice."""

    ACTION_VERBS = {
        "accelerated", "achieved", "analyzed", "architected", "automated", "benchmarked",
        "built", "collaborated", "configured", "containerized", "created", "debugged",
        "delivered", "deployed", "designed", "developed", "engineered", "enhanced",
        "evaluated", "executed", "formulated", "implemented", "improved", "increased",
        "integrated", "launched", "led", "managed", "migrated", "modeled", "monitored",
        "optimized", "orchestrated", "refactored", "resolved", "scaled", "spearheaded",
        "streamlined", "structured", "trained", "transformed", "upgraded", "validated"
    }

    @classmethod
    def calculate_semantic_similarity(cls, resume_text: str, jd_text: str) -> float:
        """
        Calculates cosine similarity of TF-IDF vectors (unigrams + bigrams)
        between the candidate resume and target job description.
        """
        if not resume_text or not jd_text:
            return 0.0

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=4000,
                sublinear_tf=True
            )
            tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
            sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            
            # Map raw cosine similarity (typically 0.10 - 0.50) into an intuitive 0 - 100 scale
            scaled = min(100.0, max(0.0, float(sim * 180.0)))
            return round(scaled, 1)
        except Exception:
            return 50.0

    @classmethod
    def analyze_quantifiable_impact(cls, text: str) -> Dict[str, Any]:
        """
        Evaluates the presence of quantifiable numbers, percentages,
        and strong action verbs in bullet points.
        """
        lines = text.splitlines()
        bullet_lines = [line.strip() for line in lines if len(line.strip()) > 20]

        total_bullets = len(bullet_lines)
        if total_bullets == 0:
            return {
                "score": 0.0,
                "quantifiable_count": 0,
                "action_verb_count": 0,
                "total_analyzed_lines": 0,
                "detected_verbs": []
            }

        metric_pattern = r"(\b\d+(?:\.\d+)?%|\b\d+x\b|\b\d+\s*ms\b|\$\d+|\b(?:increased|decreased|reduced|improved|boosted|saved|scaled)\s+(?:by\s+)?\d+)"
        
        quantifiable_count = 0
        found_verbs = set()

        for bullet in bullet_lines:
            lower = bullet.lower()
            if re.search(metric_pattern, lower) or re.search(r"\b\d{2,}\+?\b", lower):
                quantifiable_count += 1

            words = set(re.findall(r"\b[a-z]+\b", lower))
            matched_verbs = words.intersection(cls.ACTION_VERBS)
            found_verbs.update(matched_verbs)

        quant_ratio = min(1.0, float(quantifiable_count / max(total_bullets * 0.35, 1.0)))
        verb_ratio = min(1.0, float(len(found_verbs) / 6.0))

        composite_impact_score = round(float((quant_ratio * 60.0) + (verb_ratio * 40.0)), 1)

        return {
            "score": float(composite_impact_score),
            "quantifiable_count": int(quantifiable_count),
            "action_verb_count": int(len(found_verbs)),
            "total_analyzed_lines": int(total_bullets),
            "detected_verbs": sorted(list(found_verbs))[:12]
        }

    @classmethod
    def analyze_sections(cls, parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks for the presence and depth of standard ATS resume sections.
        """
        sections = parsed_resume.get("sections", {})
        contacts = parsed_resume.get("contact_info", {})

        checklist = {
            "Contact Info": bool(contacts.get("email") and contacts.get("phone")),
            "Education": "education" in sections,
            "Technical Skills": "skills" in sections,
            "Projects": "projects" in sections,
            "Experience / Internships": "experience" in sections,
            "Summary / Objective": "summary" in sections or "header" in sections
        }

        essential_keys = ["Contact Info", "Education", "Technical Skills", "Projects"]
        present_essentials = sum(1 for k in essential_keys if checklist[k])
        present_all = sum(1 for v in checklist.values() if v)

        section_score = round(float((present_essentials / len(essential_keys)) * 80.0 + (present_all / len(checklist)) * 20.0), 1)

        return {
            "score": float(min(100.0, section_score)),
            "checklist": checklist,
            "missing_sections": [k for k, v in checklist.items() if not v]
        }

    @classmethod
    def analyze_formatting(cls, parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic evaluation of resume length, email validity, and link hygiene.
        """
        word_count = int(parsed_resume.get("word_count", 0))
        contacts = parsed_resume.get("contact_info", {})

        score = 100.0
        warnings = []

        if word_count < 150:
            score -= 35.0
            warnings.append(f"Resume is very short ({word_count} words). Target 350 - 750 words for a student resume.")
        elif word_count < 250:
            score -= 15.0
            warnings.append(f"Resume content is somewhat brief ({word_count} words). Expand on project technical details.")
        elif word_count > 1100:
            score -= 15.0
            warnings.append(f"Resume is quite lengthy ({word_count} words). Keep within 1-2 pages without dense paragraphs.")

        if not contacts.get("email"):
            score -= 20.0
            warnings.append("Missing professional email address.")

        if not contacts.get("phone"):
            score -= 10.0
            warnings.append("Missing phone number.")

        if not contacts.get("github"):
            warnings.append("No GitHub link detected. For tech/AI roles, having your GitHub URL in the header is vital.")

        return {
            "score": float(max(0.0, round(score, 1))),
            "word_count": word_count,
            "warnings": warnings
        }

    @classmethod
    def score_resume(cls, resume_text: str, job_description: str, parsed_resume: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main scoring pipeline combining all five pillars into a unified ATS evaluation.
        """
        if parsed_resume is None:
            parsed_resume = ResumeParser.parse(resume_text, is_pdf=False)

        # 1. Skill Extraction & Gap Analysis (Weight: 40%)
        resume_skills_data = SkillExtractor.extract_skills(resume_text)
        jd_skills_data = SkillExtractor.extract_skills(job_description)

        resume_skills_set = set(resume_skills_data["all_skills"])
        jd_skills_set = set(jd_skills_data["all_skills"])

        matched_skills = sorted(list(resume_skills_set.intersection(jd_skills_set)))
        missing_skills = sorted(list(jd_skills_set - resume_skills_set))
        additional_skills = sorted(list(resume_skills_set - jd_skills_set))

        if len(jd_skills_set) > 0:
            skill_score = min(100.0, round(float((len(matched_skills) / len(jd_skills_set)) * 100.0), 1))
        else:
            skill_score = 75.0 if len(resume_skills_set) >= 5 else 45.0

        # 2. Semantic Similarity (Weight: 25%)
        semantic_score = float(cls.calculate_semantic_similarity(resume_text, job_description))

        # 3. Section Completeness (Weight: 15%)
        section_analysis = cls.analyze_sections(parsed_resume)
        section_score = float(section_analysis["score"])

        # 4. Action Verbs & Quantifiable Impact (Weight: 10%)
        impact_analysis = cls.analyze_quantifiable_impact(resume_text)
        impact_score = float(impact_analysis["score"])

        # 5. Formatting & Cleanliness (Weight: 10%)
        formatting_analysis = cls.analyze_formatting(parsed_resume)
        formatting_score = float(formatting_analysis["score"])

        # Composite ATS Score
        overall_score = round(
            float(
                (skill_score * 0.40) +
                (semantic_score * 0.25) +
                (section_score * 0.15) +
                (impact_score * 0.10) +
                (formatting_score * 0.10)
            ),
            1
        )

        recommendations = []

        if missing_skills:
            top_missing = missing_skills[:6]
            recommendations.append({
                "priority": "HIGH",
                "category": "Skills Gap",
                "message": f"Incorporate target skills from the job posting: {', '.join(top_missing)}."
            })

        if section_analysis["missing_sections"]:
            for sec in section_analysis["missing_sections"]:
                if sec in ["Projects", "Technical Skills", "Education"]:
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Section Header",
                        "message": f"Ensure a clear '{sec}' header exists. Standard headers guarantee parser parsing."
                    })

        if impact_score < 60.0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Quantifiable Metrics",
                "message": "Quantify bullet points: add latency reductions (e.g. 40%), accuracy stats, throughput, or user volumes."
            })

        if impact_analysis["action_verb_count"] < 5:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Action Verbs",
                "message": "Lead project bullet points with strong verbs (e.g. 'Engineered', 'Architected', 'Optimized') rather than passive phrasing."
            })

        for warn in formatting_analysis["warnings"]:
            recommendations.append({
                "priority": "LOW",
                "category": "Formatting",
                "message": warn
            })

        verdict = "Excellent Match" if overall_score >= 75 else ("Strong Candidate" if overall_score >= 60 else "Needs Optimization")

        return {
            "overall_score": overall_score,
            "verdict": verdict,
            "component_scores": {
                "skill_match": skill_score,
                "semantic_similarity": semantic_score,
                "section_completeness": section_score,
                "impact_and_metrics": impact_score,
                "formatting_and_length": formatting_score
            },
            "skills": {
                "matched": matched_skills,
                "missing": missing_skills,
                "additional": additional_skills,
                "resume_skills_categorized": resume_skills_data["categorized"]
            },
            "contacts": parsed_resume.get("contact_info", {}),
            "impact_details": {
                "quantifiable_count": impact_analysis["quantifiable_count"],
                "action_verb_count": impact_analysis["action_verb_count"],
                "detected_verbs": impact_analysis["detected_verbs"]
            },
            "section_checklist": section_analysis["checklist"],
            "word_count": parsed_resume.get("word_count", 0),
            "recommendations": recommendations
        }
