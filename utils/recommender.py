import pandas as pd

def get_benchmark_skills(db, role):
    docs = list(db["role_benchmarks"].find(
        {"DevType": role, "prevalence_pct": {"$gte": 30}},
        {"_id": 0, "skill": 1, "prevalence_pct": 1}
    ))
    return pd.DataFrame(docs)

def compute_gap(resume_skills, benchmark_df):
    benchmark_set  = set(benchmark_df["skill"].tolist())
    resume_set     = set(resume_skills)
    missing        = list(benchmark_set - resume_set)
    present        = list(benchmark_set & resume_set)
    gap_score      = round(len(missing) / len(benchmark_set) * 100, 2) \
                     if benchmark_set else 0.0
    return present, missing, gap_score

def get_job_market_recs(db, role, resume_skills):
    docs = list(db["scraped_jobs"].find())
    df   = pd.DataFrame(docs)
    if df.empty:
        return []

    # Filter by role
    role_df = df[df["role"] == role].copy()
    if role_df.empty:
        # Try DevType column as fallback
        role_df = df[df.get("DevType", pd.Series()) == role].copy()
    if role_df.empty:
        return []

    # Explode comma-separated skills and count frequency
    skills_series = (
        role_df["skills"]
        .dropna()
        .str.split(", ")
        .explode()
        .str.strip()
    )
    top_skills = (
        skills_series
        .value_counts()
        .reset_index()
    )
    top_skills.columns = ["skill", "count"]  # no job_count — use count

    resume_set = set(resume_skills)
    return [
        row["skill"]
        for _, row in top_skills.iterrows()
        if row["skill"] not in resume_set
        and row["skill"] != "N/A"
        and row["skill"] != ""
    ][:15]

def build_roadmap(missing_skills, job_market_recs):
    survey_set     = set(missing_skills)
    job_set        = set(job_market_recs)
    all_skills     = survey_set | job_set
    roadmap = []
    for skill in all_skills:
        sources = []
        if skill in survey_set: sources.append("Survey Gap")
        if skill in job_set:    sources.append("Job Market")
        roadmap.append({
            "Skill":    skill,
            "Priority": len(sources),
            "Sources":  ", ".join(sources)
        })
    return pd.DataFrame(roadmap) \
             .sort_values(["Priority", "Skill"],
                          ascending=[False, True]) \
             .reset_index(drop=True)