"""
Skill Extractor Module
Multi-category technical and soft skill taxonomy with regex boundary matching,
phrase disambiguation, and alias normalization.
"""

import re
from typing import Dict, List, Set, Any


class SkillExtractor:
    """Extracts and categorizes technical and domain skills from resumes and job descriptions."""

    # Curated skill taxonomies grouped by domain
    TAXONOMY = {
        "AI / Machine Learning & Data": [
            "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP",
            "Computer Vision", "Large Language Models", "LLMs", "Generative AI", "GenAI",
            "Retrieval-Augmented Generation", "RAG", "PyTorch", "TensorFlow", "Keras",
            "Scikit-Learn", "OpenCV", "Pandas", "NumPy", "SciPy", "Hugging Face",
            "Transformers", "LangChain", "LlamaIndex", "MediaPipe", "XGBoost", "LightGBM",
            "Matplotlib", "Seaborn", "Tableau", "Power BI", "Statistics", "Linear Algebra",
            "Prompt Engineering", "Vector Databases", "ChromaDB", "FAISS", "Pinecone"
        ],
        "Programming Languages": [
            "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript",
            "Go", "Rust", "Kotlin", "Swift", "SQL", "R", "Bash", "Shell",
            "HTML", "CSS", "PHP", "Scala", "Dart"
        ],
        "Web & Full-Stack": [
            "FastAPI", "Flask", "Django", "React", "Next.js", "Vue.js", "Angular",
            "Node.js", "Express.js", "Spring Boot", "ASP.NET", "Streamlit",
            "Tailwind CSS", "Bootstrap", "Redux", "Zustand", "HTML5", "CSS3"
        ],
        "Databases & ORM": [
            "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Supabase",
            "Firebase", "Cassandra", "DynamoDB", "Oracle", "Prisma", "SQLAlchemy"
        ],
        "Cloud, DevOps & Tools": [
            "Docker", "Kubernetes", "AWS", "Google Cloud Platform", "GCP",
            "Microsoft Azure", "Linux", "Git", "GitHub", "GitLab", "CI/CD",
            "GitHub Actions", "Nginx", "Terraform", "Vercel", "Postman"
        ],
        "Core CS & Systems": [
            "Data Structures", "Algorithms", "Object-Oriented Programming", "OOP",
            "System Design", "Operating Systems", "DBMS", "Computer Networks",
            "REST API", "GraphQL", "Microservices", "Agile", "Scrum"
        ]
    }

    # Normalized aliases for acronyms and colloquial tool names
    ALIASES = {
        "sklearn": "Scikit-Learn",
        "scikit learn": "Scikit-Learn",
        "tf": "TensorFlow",
        "k8s": "Kubernetes",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "js": "JavaScript",
        "ts": "TypeScript",
        "gcp": "Google Cloud Platform",
        "aws": "AWS",
        "azure": "Microsoft Azure",
        "llm": "Large Language Models",
        "llms": "Large Language Models",
        "cv": "Computer Vision",
        "nlp": "Natural Language Processing",
        "ml": "Machine Learning",
        "dl": "Deep Learning",
        "genai": "Generative AI",
        "generative ai": "Generative AI",
        "rag": "Retrieval-Augmented Generation",
        "oops": "Object-Oriented Programming",
        "oop": "Object-Oriented Programming",
        "dsa": "Data Structures",
        "data structures and algorithms": "Data Structures",
        "restful api": "REST API",
        "rest apis": "REST API",
        "nextjs": "Next.js",
        "vue": "Vue.js",
        "vuejs": "Vue.js",
        "express": "Express.js",
        "springboot": "Spring Boot"
    }

    @classmethod
    def extract_skills(cls, text: str) -> Dict[str, Any]:
        """
        Scans input text and returns categorized matched skills as well as a flat list.
        Uses exact phrase boundary matching with order-of-length precedence to avoid sub-token collision.
        """
        if not text:
            return {"categorized": {}, "all_skills": [], "total_count": 0}

        text_lower = f" {text.lower()} "
        found_canonical_skills: Set[str] = set()

        # Step 1: Check aliases first
        for alias, canonical in cls.ALIASES.items():
            pattern = rf"(?<![a-zA-Z0-9#+]){re.escape(alias.lower())}(?![a-zA-Z0-9#+])"
            if re.search(pattern, text_lower):
                found_canonical_skills.add(canonical)

        # Step 2: Sort taxonomy skills by character length descending
        # (e.g. "Natural Language Processing" evaluated before "Language")
        all_taxonomy_items = []
        for category, skill_list in cls.TAXONOMY.items():
            for skill in skill_list:
                all_taxonomy_items.append((skill, category))

        all_taxonomy_items.sort(key=lambda x: len(x[0]), reverse=True)

        categorized_results: Dict[str, List[str]] = {cat: [] for cat in cls.TAXONOMY}

        for skill, category in all_taxonomy_items:
            escaped_skill = re.escape(skill.lower())
            
            # Special handling for C, C++, C#
            if skill.lower() == "c":
                pattern = r"(?<![a-zA-Z0-9#+])c(?![a-zA-Z0-9#+])"
            elif skill.lower() == "c++":
                pattern = r"(?<![a-zA-Z0-9])c\+\+(?![a-zA-Z0-9])"
            elif skill.lower() == "c#":
                pattern = r"(?<![a-zA-Z0-9])c\#(?![a-zA-Z0-9])"
            elif skill.lower() == "r":
                pattern = r"(?<![a-zA-Z0-9#+])r(?![a-zA-Z0-9#+])"
            else:
                pattern = rf"(?<![a-zA-Z0-9#+]){escaped_skill}(?![a-zA-Z0-9#+])"

            if skill in found_canonical_skills or re.search(pattern, text_lower):
                found_canonical_skills.add(skill)
                if skill not in categorized_results[category]:
                    categorized_results[category].append(skill)

        # Sort each category alphabetically
        for cat in categorized_results:
            categorized_results[cat].sort()

        # Filter out empty categories
        populated_categories = {k: v for k, v in categorized_results.items() if v}
        flat_list = sorted(list(found_canonical_skills))

        return {
            "categorized": populated_categories,
            "all_skills": flat_list,
            "total_count": len(flat_list)
        }
