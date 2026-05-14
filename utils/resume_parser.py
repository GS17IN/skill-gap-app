import re
import pdfplumber
import docx

KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "C", "Go",
    "Rust", "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "SQL", "HTML",
    "CSS", "Bash", "PowerShell", "Dart", "Lua", "MATLAB", "Perl",
    "Assembly", "Groovy", "Elixir", "Clojure", "Haskell", "Julia",
    "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
    "Spring", "TensorFlow", "PyTorch", "Kubernetes", "Docker", "Spark",
    "Hadoop", "Kafka", "Airflow", "AWS", "Azure", "GCP", "Linux",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Terraform", "Ansible", "Jenkins", "Git", "Grafana", "Prometheus"
]

ROLE_KEYWORDS = {
    "Data Scientist":     ["data scientist", "machine learning", "deep learning",
                           "nlp", "neural network", "tensorflow", "pytorch"],
    "Data Engineer":      ["data engineer", "data pipeline", "etl", "airflow",
                           "kafka", "spark", "hadoop", "data warehouse"],
    "Full-Stack Dev":     ["full stack", "fullstack", "mern", "mean stack"],
    "Back-End Dev":       ["backend", "back-end", "rest api", "microservices",
                           "spring boot", "fastapi", "graphql"],
    "Front-End Dev":      ["frontend", "front-end", "ui developer",
                           "react", "angular", "vue"],
    "DevOps specialist":  ["devops", "ci/cd", "jenkins", "kubernetes",
                           "terraform", "ansible", "infrastructure"],
    "Cloud Engineer":     ["cloud engineer", "aws", "azure", "gcp",
                           "cloud architect", "serverless"],
    "Mobile Dev":         ["mobile developer", "android", "ios",
                           "flutter", "react native", "swift", "kotlin"],
    "Security Engineer":  ["security engineer", "cybersecurity",
                           "penetration", "soc analyst", "vulnerability"],
    "Data Analyst":       ["data analyst", "business analyst", "power bi",
                           "tableau", "sql analyst", "reporting"],
    "QA Engineer":        ["qa engineer", "quality assurance",
                           "test automation", "selenium", "pytest"],
    "Blockchain Dev":     ["blockchain", "solidity", "smart contract",
                           "web3", "ethereum"],
}

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def extract_text_from_docx(file):
    doc  = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_skills(text):
    found = []
    for skill in KNOWN_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found.append(skill)
    return found

def detect_role(text):
    text_lower = text.lower()
    scores     = {}
    for role, keywords in ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[role] = score
    if not scores:
        return "Back-End Dev"
    return max(scores, key=scores.get)