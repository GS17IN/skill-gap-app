import requests
import re
import time
import pandas as pd

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

SKILLS_LOWER = {s.lower(): s for s in KNOWN_SKILLS}

ROLE_TAGS = {
    "Data Scientist":     ["data", "machine-learning"],
    "Data Engineer":      ["data", "backend"],
    "Full-Stack Dev":     ["fullstack", "javascript"],
    "Back-End Dev":       ["backend", "python"],
    "Front-End Dev":      ["frontend", "react"],
    "DevOps specialist":  ["devops", "kubernetes"],
    "Cloud Engineer":     ["cloud", "aws"],
    "Mobile Dev":         ["mobile", "react-native"],
    "Security Engineer":  ["security"],
    "Data Analyst":       ["data", "sql"],
    "QA Engineer":        ["qa", "testing"],
    "Blockchain Dev":     ["blockchain", "web3"],
}

# Experience level keywords
EXPERIENCE_LEVELS = {
    "junior":  ["junior", "entry", "graduate", "fresher", "0-2", "1 year"],
    "mid":     ["mid", "intermediate", "2-4", "2-5", "3 years", "4 years"],
    "senior":  ["senior", "lead", "principal", "5+", "6+", "7+", "experienced"],
}

def extract_skills_from_text(text):
    found = []
    text_lower = text.lower()
    for skill_lower, skill_original in SKILLS_LOWER.items():
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill_original)
    return found

def detect_experience_level(text):
    text_lower = text.lower()
    for level, keywords in EXPERIENCE_LEVELS.items():
        if any(kw in text_lower for kw in keywords):
            return level
    return "mid"  # default

def scrape_remoteok_live(role, max_jobs=15):
    tags     = ROLE_TAGS.get(role, ["developer"])
    all_jobs = []

    for tag in tags[:2]:   # max 2 tags to avoid rate limiting
        url     = f"https://remoteok.com/api?tag={tag}"
        headers = {"User-Agent": "skill-gap-research/1.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            jobs = data[1:] if len(data) > 1 else []
            for job in jobs[:max_jobs]:
                text   = " ".join([
                    job.get("position", ""),
                    job.get("description", ""),
                    " ".join(job.get("tags", []))
                ])
                skills = extract_skills_from_text(text)
                desc   = re.sub(r"<[^>]+>", " ", job.get("description", ""))
                exp    = detect_experience_level(
                    job.get("position", "") + " " + desc
                )
                all_jobs.append({
                    "title":      job.get("position", "N/A"),
                    "company":    job.get("company", "N/A"),
                    "skills":     skills,
                    "experience": exp,
                    "url":        job.get("url", "#"),
                    "salary":     job.get("salary", "Not specified"),
                    "source":     "RemoteOK",
                    "role_tag":   tag,
                })
            time.sleep(1)
        except Exception as e:
            print(f"RemoteOK [{tag}] error: {e}")

    return all_jobs


def scrape_remotive_live(role, max_jobs=15):
    query   = role.lower().replace("-", " ").replace("specialist", "").strip()
    url     = "https://remotive.com/api/remote-jobs"
    params  = {"search": query, "limit": max_jobs}
    results = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        jobs = data.get("jobs", [])
        for job in jobs[:max_jobs]:
            tags   = job.get("tags", [])
            desc   = re.sub(r"<[^>]+>", " ", job.get("description", ""))
            text   = f"{job.get('title','')} {' '.join(tags)} {desc}"
            skills = extract_skills_from_text(text)
            exp    = detect_experience_level(job.get("title","") + " " + desc)
            results.append({
                "title":      job.get("title", "N/A"),
                "company":    job.get("company_name", "N/A"),
                "skills":     skills,
                "experience": exp,
                "url":        job.get("url", "#"),
                "salary":     job.get("salary", "Not specified"),
                "source":     "Remotive",
                "role_tag":   query,
            })
    except Exception as e:
        print(f"Remotive [{role}] error: {e}")
    return results


def scrape_jobs_live(role, max_jobs=15):
    """Combine both sources."""
    jobs = scrape_remoteok_live(role, max_jobs)
    jobs += scrape_remotive_live(role, max_jobs)
    return jobs


def compute_job_match_score(resume_skills, resume_role,
                             job, target_role, target_exp):
    """
    Match score = weighted combination of:
      - Skill overlap     : 60%
      - Role title match  : 25%
      - Experience match  : 15%
    Returns score 0-100.
    """
    resume_set  = set(resume_skills)
    job_set     = set(job["skills"])

    # 1. Skill overlap (Jaccard)
    if resume_set | job_set:
        skill_score = len(resume_set & job_set) / len(resume_set | job_set) * 100
    else:
        skill_score = 0.0

    # 2. Role title match
    title_lower = job["title"].lower()
    role_lower  = target_role.lower().replace("-", " ") \
                             .replace(" dev", " developer") \
                             .replace("specialist", "engineer")
    role_keywords = role_lower.split()
    role_hits     = sum(1 for kw in role_keywords if kw in title_lower)
    role_score    = (role_hits / max(len(role_keywords), 1)) * 100

    # 3. Experience match
    exp_score = 100 if job["experience"] == target_exp else \
                50  if abs(
                    ["junior", "mid", "senior"].index(job["experience"]) -
                    ["junior", "mid", "senior"].index(target_exp)
                ) == 1 else 20

    # Weighted total
    total = (skill_score * 0.60) + (role_score * 0.25) + (exp_score * 0.15)
    return round(total, 1), round(skill_score, 1), round(role_score, 1), exp_score


def compute_role_alignment(resume_skills, benchmark_df):
    """
    How aligned is the user with a target role.
    Returns alignment %, present skills, missing skills.
    """
    if benchmark_df.empty:
        return 0.0, [], []
    benchmark_set = set(benchmark_df["skill"].tolist())
    resume_set    = set(resume_skills)
    present       = list(benchmark_set & resume_set)
    missing       = list(benchmark_set - resume_set)
    alignment     = round(len(present) / len(benchmark_set) * 100, 1) \
                    if benchmark_set else 0.0
    return alignment, present, missing


def get_job_market_recs(db, selected_role, resume_skills):
    """
    Build market-based recommendations from live job scraping.
    Returns a DataFrame compatible with build_roadmap().
    """

    jobs = scrape_jobs_live(selected_role, max_jobs=20)

    if not jobs:
        return pd.DataFrame(columns=["Skill", "Priority", "Sources"])

    # Count how often skills appear in jobs
    market_demand = {}

    for job in jobs:
        for skill in job["skills"]:
            if skill not in resume_skills:
                market_demand[skill] = market_demand.get(skill, 0) + 1

    if not market_demand:
        return pd.DataFrame(columns=["Skill", "Priority", "Sources"])

    rows = []

    for skill, freq in sorted(
        market_demand.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        rows.append({
            "Skill": skill,
            "Priority": 2 if freq >= 3 else 1,
            "Sources": f"{freq} live job postings"
        })

    return pd.DataFrame(rows)