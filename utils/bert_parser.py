import os
os.environ["USE_TF"] = "0"

import re
import numpy as np
from sentence_transformers import SentenceTransformer, util


# Known skills with variations
SKILL_VARIANTS = {
    "Python":                   ["python", "py"],
    "JavaScript":               ["javascript", "js", "node", "nodejs", "node.js"],
    "TypeScript":               ["typescript", "ts"],
    "Java":                     ["java", "spring", "springboot", "spring boot"],
    "C#":                       ["c#", "csharp", "dotnet", ".net"],
    "C++":                      ["c++", "cpp"],
    "C":                        ["c programming", " c ", "embedded c"],
    "Go":                       ["golang", " go "],
    "Rust":                     ["rust", "rustlang"],
    "Kotlin":                   ["kotlin"],
    "Swift":                    ["swift", "swiftui"],
    "PHP":                      ["php", "laravel", "symfony"],
    "Ruby":                     ["ruby", "rails", "ruby on rails"],
    "Scala":                    ["scala", "akka"],
    "R":                        [" r ", "rstudio", "tidyverse"],
    "SQL":                      ["sql", "mysql", "postgresql", "sqlite",
                                 "oracle sql", "t-sql", "plsql"],
    "HTML/CSS":                 ["html", "css", "scss", "sass", "html5", "css3"],
    "Bash/Shell (all shells)":  ["bash", "shell", "zsh", "powershell",
                                 "shell scripting", "bash scripting"],
    "React":                    ["react", "reactjs", "react.js", "next.js", "nextjs"],
    "Angular":                  ["angular", "angularjs"],
    "Vue":                      ["vue", "vuejs", "vue.js", "nuxt"],
    "Node.js":                  ["node.js", "nodejs", "express", "expressjs"],
    "Django":                   ["django", "drf", "django rest"],
    "Flask":                    ["flask"],
    "FastAPI":                  ["fastapi", "fast api"],
    "Spring":                   ["spring", "spring boot", "spring mvc"],
    "TensorFlow":               ["tensorflow", "tf", "keras"],
    "PyTorch":                  ["pytorch", "torch"],
    "Kubernetes":               ["kubernetes", "k8s", "kubectl"],
    "Docker":                   ["docker", "dockerfile", "docker-compose",
                                 "containerization"],
    "Spark":                    ["apache spark", "pyspark", "spark streaming"],
    "Hadoop":                   ["hadoop", "hdfs", "mapreduce", "hive"],
    "Kafka":                    ["kafka", "apache kafka"],
    "Airflow":                  ["airflow", "apache airflow"],
    "AWS":                      ["aws", "amazon web services", "ec2", "s3",
                                 "lambda", "sagemaker", "cloudwatch"],
    "Azure":                    ["azure", "microsoft azure", "azure devops"],
    "GCP":                      ["gcp", "google cloud", "bigquery",
                                 "google cloud platform"],
    "Linux":                    ["linux", "ubuntu", "centos", "unix", "debian"],
    "PostgreSQL":               ["postgresql", "postgres"],
    "MySQL":                    ["mysql"],
    "MongoDB":                  ["mongodb", "mongo", "nosql"],
    "Redis":                    ["redis"],
    "Elasticsearch":            ["elasticsearch", "elastic", "elk stack"],
    "Terraform":                ["terraform", "infrastructure as code", "iac"],
    "Ansible":                  ["ansible"],
    "Jenkins":                  ["jenkins", "ci/cd", "cicd", "pipeline"],
    "Git":                      ["git", "github", "gitlab", "version control",
                                 "bitbucket"],
    "Grafana":                  ["grafana", "monitoring", "observability"],
    "Prometheus":               ["prometheus"],
    "PowerShell":               ["powershell"],
    "Dart":                     ["dart", "flutter"],
    "Kotlin":                   ["kotlin", "android"],
    "Swift":                    ["swift", "ios", "xcode"],
}

# Skill descriptions for semantic matching 
SKILL_DESCRIPTIONS = {
    "Python":        "Python programming language for data science, web development and automation",
    "JavaScript":    "JavaScript web development frontend and backend programming",
    "TypeScript":    "TypeScript typed JavaScript superset for large applications",
    "Java":          "Java enterprise application development object oriented programming",
    "Docker":        "Docker containerization platform for deployment and microservices",
    "Kubernetes":    "Kubernetes container orchestration cluster management",
    "AWS":           "Amazon Web Services cloud computing infrastructure",
    "React":         "React JavaScript library for building user interfaces",
    "SQL":           "SQL database querying and relational database management",
    "TensorFlow":    "TensorFlow machine learning deep learning framework",
    "PyTorch":       "PyTorch deep learning neural network framework",
    "Spark":         "Apache Spark distributed data processing big data",
    "Kafka":         "Apache Kafka message streaming distributed systems",
    "Terraform":     "Terraform infrastructure as code cloud provisioning",
    "Git":           "Git version control source code management",
    "Linux":         "Linux operating system server administration",
    "MongoDB":       "MongoDB NoSQL document database",
    "PostgreSQL":    "PostgreSQL relational database management system",
    "Go":            "Go Golang programming language for systems and cloud",
    "Rust":          "Rust systems programming language for safety and performance",
    "Azure":         "Microsoft Azure cloud platform services",
    "GCP":           "Google Cloud Platform cloud computing services",
    "Node.js":       "Node.js JavaScript runtime server side programming",
    "Django":        "Django Python web framework for rapid development",
    "Flask":         "Flask Python lightweight web framework microservices",
    "Airflow":       "Apache Airflow workflow orchestration data pipelines",
    "Redis":         "Redis in memory data structure store cache",
    "Elasticsearch": "Elasticsearch search and analytics engine",
    "Jenkins":       "Jenkins continuous integration continuous deployment automation",
    "Grafana":       "Grafana metrics visualization monitoring dashboards",
}

# Singleton model loader 
_model = None

def get_model():
    global _model
    if _model is None:
        # all-MiniLM-L6-v2: only 80MB, fast, accurate for skill matching
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# Method 1: Regex-based extraction
def extract_skills_regex(text):
    found  = set()
    text_l = text.lower()
    for skill, variants in SKILL_VARIANTS.items():
        for variant in variants:
            pattern = r'\b' + re.escape(variant.strip()) + r'\b'
            if re.search(pattern, text_l):
                found.add(skill)
                break
    return list(found)


# Method 2: BERT semantic matching
def extract_skills_bert(text, threshold=0.45):
    """
    Use sentence-transformers to semantically match resume sentences
    against skill descriptions. Catches paraphrased skill mentions.
    """
    model = get_model()
    found = set()

    # Split text into sentences
    sentences = [s.strip() for s in re.split(r'[.\n]', text)
                 if len(s.strip()) > 10]
    if not sentences:
        return []

    # Encode sentences and skill descriptions
    skill_names  = list(SKILL_DESCRIPTIONS.keys())
    skill_descs  = list(SKILL_DESCRIPTIONS.values())

    try:
        sentence_embs = model.encode(sentences,
                                     convert_to_tensor=True,
                                     show_progress_bar=False)
        skill_embs    = model.encode(skill_descs,
                                     convert_to_tensor=True,
                                     show_progress_bar=False)

        # Cosine similarity between each sentence and each skill
        similarities = util.cos_sim(sentence_embs, skill_embs)

        # For each skill, check if any sentence is above threshold
        for skill_idx, skill_name in enumerate(skill_names):
            max_sim = similarities[:, skill_idx].max().item()
            if max_sim >= threshold:
                found.add(skill_name)

    except Exception as e:
        print(f"BERT extraction error: {e}")

    return list(found)


#  Combined extraction 
def extract_skills_combined(text):
    """
    Combine regex (high precision) + BERT (high recall).
    Returns skills with source labels.
    """
    regex_skills = set(extract_skills_regex(text))
    bert_skills  = set(extract_skills_bert(text))

    # Skills found by both = high confidence
    both   = regex_skills & bert_skills
    # Skills found only by regex
    regex_only = regex_skills - bert_skills
    # Skills found only by BERT = semantic matches
    bert_only  = bert_skills - regex_skills

    results = []
    for s in sorted(both):
        results.append({"skill": s, "method": "Both",  "confidence": "High"})
    for s in sorted(regex_only):
        results.append({"skill": s, "method": "Regex", "confidence": "High"})
    for s in sorted(bert_only):
        results.append({"skill": s, "method": "BERT",  "confidence": "Medium"})

    return results


# Role detection with BERT 
ROLE_DESCRIPTIONS = {
    "Data Scientist":    "machine learning model training deep learning NLP data analysis statistical modeling",
    "Data Engineer":     "data pipeline ETL data warehouse Apache Spark Kafka data infrastructure",
    "Full-Stack Dev":    "full stack web development frontend backend React Node.js API database",
    "Back-End Dev":      "backend server API REST microservices database Python Java Node.js",
    "Front-End Dev":     "frontend UI React Angular Vue HTML CSS JavaScript user interface",
    "DevOps specialist": "DevOps CI/CD Docker Kubernetes infrastructure automation deployment cloud",
    "Cloud Engineer":    "cloud AWS Azure GCP infrastructure serverless cloud architecture",
    "Mobile Dev":        "mobile Android iOS Flutter React Native Swift Kotlin app development",
    "Security Engineer": "cybersecurity penetration testing vulnerability security operations",
    "Data Analyst":      "data analysis SQL business intelligence Tableau Power BI reporting",
    "QA Engineer":       "quality assurance testing automation Selenium pytest test cases",
    "Blockchain Dev":    "blockchain Solidity smart contracts Web3 Ethereum DeFi",
    "SRE":               "site reliability engineering uptime SLO monitoring Prometheus Grafana",
    "Embedded Dev":      "embedded systems firmware microcontroller RTOS Arduino C programming",
}

def detect_role_bert(text):
    """
    Use BERT to detect role — more accurate than keyword matching.
    Returns ranked list of (role, score).
    """
    model      = get_model()
    role_names = list(ROLE_DESCRIPTIONS.keys())
    role_descs = list(ROLE_DESCRIPTIONS.values())

    try:
        text_emb  = model.encode([text[:512]],  # limit text length
                                  convert_to_tensor=True,
                                  show_progress_bar=False)
        role_embs = model.encode(role_descs,
                                  convert_to_tensor=True,
                                  show_progress_bar=False)

        sims = util.cos_sim(text_emb, role_embs)[0]
        ranked = sorted(
            zip(role_names, sims.tolist()),
            key=lambda x: x[1],
            reverse=True
        )
        return ranked

    except Exception as e:
        print(f"BERT role detection error: {e}")
        return [(r, 0.0) for r in role_names]
