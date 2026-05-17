import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
matplotlib.use("Agg")
from utils.db            import get_db
from utils.resume_parser import (extract_text_from_pdf, extract_text_from_docx,
                                  extract_skills, detect_role, ROLE_KEYWORDS)
from utils.recommender   import get_benchmark_skills, build_roadmap
from utils.job_scraper   import (scrape_jobs_live, compute_job_match_score,
                                  compute_role_alignment)
from utils.styles        import (inject_styles, page_banner, step_label,
                                  skill_badges, gap_bar, section_divider,
                                  chart_style)

st.set_page_config(
    page_title="Job Finder & Role Alignment",
    page_icon="🔍", layout="wide"
)
inject_styles()

page_banner(
    "🔍", "Job Finder & Role Alignment",
    "Real-time job matching + target role alignment score "
    "powered by live scraping from RemoteOK & Remotive"
)

db = get_db()

# Session state 
if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = []
if "detected_role" not in st.session_state:
    st.session_state.detected_role = None
if "live_jobs" not in st.session_state:
    st.session_state.live_jobs = []

# Check for resume from Resume Analyzer 
step_label(1, "Resume Profile")

if st.session_state.get("resume_skills"):
    col1, col2 = st.columns([3,1])

    with col1:
        st.success(
            f"Using resume from BERT Analyzer — "
            f"**{len(st.session_state.resume_skills)} skills** detected"
        )

    with col2:
        if st.button("Re-analyse resume"):
            st.switch_page("pages/1_Resume_Analyzer.py")

    if st.session_state.get("last_resume_hash"):
        st.caption(
            f"Resume ID: `{st.session_state.last_resume_hash[:8]}...`"
        )

    skill_badges(
        sorted(st.session_state.resume_skills),
        variant="high"
    )

    if st.session_state.get("detected_role"):
        st.info(
            f"BERT detected role: "
            f"**{st.session_state.detected_role}**"
        )

section_divider()

# Step 2: Preferences 
step_label(2, "Set Your Preferences")

all_roles = list(ROLE_KEYWORDS.keys())

col1, col2, col3 = st.columns(3)
with col1:
    current_role = st.selectbox(
        "Your Current / Detected Role",
        all_roles,
        index=(all_roles.index(st.session_state.detected_role)
               if st.session_state.get("detected_role") in all_roles else 0)
    )
with col2:
    target_role = st.selectbox(
        "Target Role (aspirational)",
        all_roles,
        index=(all_roles.index(st.session_state.detected_role)
               if st.session_state.detected_role in all_roles else 0)
    )
with col3:
    target_exp = st.selectbox(
        "Experience Level",
        ["junior", "mid", "senior"],
        index=1
    )

section_divider()

# Step 3: Role Alignment
step_label(3, "Role Alignment Analysis")

if st.session_state.resume_skills:
    benchmark_df             = get_benchmark_skills(db, target_role)
    alignment, present, missing = compute_role_alignment(
        st.session_state.resume_skills, benchmark_df
    )

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alignment Score",  f"{alignment}%")
    col2.metric("Skills Matched",   len(present))
    col3.metric("Skills to Learn",  len(missing))
    col4.metric("Benchmark Total",  len(present) + len(missing))

    # Alignment bar
    gap_bar(100 - alignment,
            label=f"Alignment with {target_role}")

    # Verdict
    if alignment >= 70:
        st.success(
            f"You are well aligned with **{target_role}**! "
            f"Focus on the remaining {len(missing)} skills to reach 100%."
        )
    elif alignment >= 40:
        st.warning(
            f"Moderately aligned with **{target_role}**. "
            f"Upskill in {len(missing)} areas to improve."
        )
    else:
        st.error(
            f"Significant upskilling needed for **{target_role}**. "
            f"{len(missing)} skills to learn."
        )

    # Skills breakdown
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Skills you already have:**")
        if present:
            skill_badges(present, variant="high")
        else:
            st.markdown("_None matched benchmark_")
    with col_b:
        st.markdown("**Skills to learn:**")
        if missing:
            skill_badges(missing, variant="missing")
        else:
            st.success("You have all benchmark skills!")

    # Upskilling roadmap
    if missing:
        section_divider()
        step_label("→", f"Upskilling Roadmap for {target_role}")

        job_recs = []
        if st.session_state.live_jobs:
            from collections import Counter
            job_skills     = []
            for job in st.session_state.live_jobs:
                job_skills.extend(job["skills"])
            job_skill_counts = Counter(job_skills)
            resume_set       = set(st.session_state.resume_skills)
            job_recs         = [s for s, _ in
                                 job_skill_counts.most_common(20)
                                 if s not in resume_set][:15]

        roadmap = build_roadmap(missing, job_recs)

        c1, c2 = st.columns(2)
        c1.metric("🔴 High Priority (2 signals)",
                  len(roadmap[roadmap["Priority"] == 2]))
        c2.metric("🔵 Normal Priority (1 signal)",
                  len(roadmap[roadmap["Priority"] == 1]))

        st.dataframe(
            roadmap,
            use_container_width=True,
            column_config={
                "Skill":    st.column_config.TextColumn("🛠️ Skill"),
                "Priority": st.column_config.NumberColumn("⭐ Priority"),
                "Sources":  st.column_config.TextColumn("📡 Sources"),
            }
        )
        st.download_button(
            f"Download Roadmap for {target_role}",
            roadmap.to_csv(index=False),
            file_name=f"upskilling_{target_role.replace(' ','_')}.csv",
            mime="text/csv"
        )

else:
    st.info("Upload your resume above to see alignment analysis.")

section_divider()

# Step 4: Live Job Search
step_label(4, "Find Matching Jobs — Live")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(
        f"Scraping live jobs for **{target_role}** "
        f"at **{target_exp}** level from RemoteOK & Remotive."
    )
with col2:
    scrape_btn = st.button(
        "Find Jobs Now",
        type="primary",
        disabled=not bool(st.session_state.resume_skills)
    )

if not st.session_state.resume_skills:
    st.info("Upload your resume first to enable job search.")

if scrape_btn and st.session_state.resume_skills:
    with st.spinner(
        f"Scraping live jobs for {target_role}... ~10 seconds"
    ):
        jobs = scrape_jobs_live(target_role, max_jobs=15)
        st.session_state.live_jobs = jobs

    if jobs:
        st.success(f"Found {len(jobs)} live job postings!")
    else:
        st.warning(
            "No jobs found. APIs may be rate-limiting. "
            "Try again in a moment."
        )

# Job Results
if st.session_state.live_jobs:
    jobs = st.session_state.live_jobs

    # Score all jobs
    scored_jobs = []
    for job in jobs:
        total, skill_s, role_s, exp_s = compute_job_match_score(
            st.session_state.resume_skills,
            current_role, job,
            target_role, target_exp
        )
        scored_jobs.append({
            **job,
            "match_score": total,
            "skill_score": skill_s,
            "role_score":  role_s,
            "exp_score":   exp_s,
        })
    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    section_divider()

    # Score distribution chart
    step_label(5, "Match Score Distribution")

    scores  = [j["match_score"] for j in scored_jobs]
    colors  = ["#00E676" if s >= 60 else
               "#FFB800" if s >= 35 else
               "#FF4560" for s in scores]

    mpl.rcParams.update(chart_style())
    fig, ax = plt.subplots(figsize=(10, 3))
    bars_sc = ax.bar(range(len(scores)), scores, color=colors,
                     edgecolor="#0A0E1A", linewidth=0.5)
    ax.bar_label(bars_sc, fmt="%.0f%%", padding=2,
                 color="#E8EDF5", fontsize=7)
    ax.axhline(y=60, color="#00E676", linestyle="--",
               alpha=0.6, label="Good match (60%)")
    ax.axhline(y=35, color="#FFB800", linestyle="--",
               alpha=0.6, label="Moderate match (35%)")
    ax.set_xlabel("Jobs (sorted by match score)")
    ax.set_ylabel("Match Score %")
    ax.set_title("Job Match Score Distribution")
    ax.legend(framealpha=0.3)
    ax.set_ylim(0, 110)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Legend
    st.markdown("""
    <div style="display:flex; gap:20px; margin:8px 0 16px">
        <span class="skill-badge high">🟢 Good match ≥60%</span>
        <span class="skill-badge medium">🟡 Moderate 35–60%</span>
        <span class="skill-badge missing">🔴 Low &lt;35%</span>
    </div>
    """, unsafe_allow_html=True)

    section_divider()

    # Filter controls
    step_label(6, "Job Listings")

    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider("Minimum Match Score", 0, 100, 30)
    with col2:
        source_filter = st.multiselect(
            "Filter by Source",
            ["RemoteOK", "Remotive"],
            default=["RemoteOK", "Remotive"]
        )

    filtered = [
        j for j in scored_jobs
        if j["match_score"] >= min_score
        and j["source"] in source_filter
    ]

    st.markdown(
        f"Showing **{len(filtered)}** jobs above "
        f"**{min_score}%** match"
    )

    if not filtered:
        st.info("No jobs match your filters. Try lowering the minimum score.")

    # Job cards
    for job in filtered:
        score      = job["match_score"]
        score_cls  = ("score-high"   if score >= 60 else
                      "score-medium" if score >= 35 else
                      "score-low")
        emoji      = ("🟢" if score >= 60 else
                      "🟡" if score >= 35 else "🔴")

        with st.expander(
            f"{emoji} {job['title']} @ {job['company']} "
            f"— {score:.0f}% match | {job['source']}"
        ):
            # Score breakdown
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall Match", f"{score:.0f}%")
            c2.metric("Skill Match",   f"{job['skill_score']:.0f}%")
            c3.metric("Role Match",    f"{job['role_score']:.0f}%")
            c4.metric("Exp Match",     f"{job['exp_score']:.0f}%")

            # Score pill HTML
            st.markdown(f"""
            <span class="skill-badge {'high' if score>=60 else 'medium' if score>=35 else 'missing'}">
                {score:.0f}% Match
            </span>
            """, unsafe_allow_html=True)

            section_divider()

            # Skills breakdown
            resume_set   = set(st.session_state.resume_skills)
            job_set      = set(job["skills"])
            matching     = sorted(resume_set & job_set)
            not_matching = sorted(job_set - resume_set)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Your matching skills:**")
                if matching:
                    skill_badges(matching, variant="high")
                else:
                    st.markdown("_None matched_")
            with col_b:
                st.markdown("**📚 Skills you need for this job:**")
                if not_matching:
                    skill_badges(not_matching, variant="missing")
                else:
                    st.markdown("_You have all required skills!_ 🎉")

            # Meta info
            st.markdown(f"""
            <div style="margin-top:12px; font-size:0.82rem;
                        color:#8892A4; font-family:'Space Mono',monospace">
                Experience: {job['experience'].capitalize()} &nbsp;|&nbsp;
                Salary: {job['salary']} &nbsp;|&nbsp;
                Source: {job['source']}
            </div>
            """, unsafe_allow_html=True)

            if job.get("url") and job["url"] != "#":
                st.markdown(
                    f"[View Job Posting →]({job['url']})"
                )

    section_divider()

    # Export
    if filtered:
        export_df = pd.DataFrame([{
            "Title":        j["title"],
            "Company":      j["company"],
            "Match Score":  j["match_score"],
            "Skill Score":  j["skill_score"],
            "Role Score":   j["role_score"],
            "Experience":   j["experience"],
            "Salary":       j["salary"],
            "Source":       j["source"],
            "URL":          j["url"],
        } for j in filtered])

        st.download_button(
            "Download Job Matches as CSV",
            export_df.to_csv(index=False),
            file_name="job_matches.csv",
            mime="text/csv"
        )
