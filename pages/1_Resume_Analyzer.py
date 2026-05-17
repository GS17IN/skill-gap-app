import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
matplotlib.use("Agg")
import pdfplumber
import docx
from utils.bert_parser import extract_skills_combined, detect_role_bert
from utils.db          import get_db
from utils.recommender import get_benchmark_skills, compute_gap, build_roadmap
from utils.job_scraper import get_job_market_recs
from utils.styles      import (inject_styles, page_banner, step_label,
                                skill_badges, gap_bar, section_divider,
                                chart_style)

st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="🧠", layout="wide"
)
inject_styles()

page_banner(
    "🧠", "BERT Resume Analyzer",
    "Semantic skill extraction powered by Sentence-BERT — "
    "understands context, not just keywords"
)

db = get_db()


with st.expander("How is this different from basic keyword matching?"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Basic Analyzer (Regex)**
        - Exact keyword matching only
        - Misses: "built REST APIs with Express" → Node.js
        - Misses: "deployed on EKS" → Kubernetes
        - Misses: "used GKE for orchestration" → Kubernetes
        - Fast but lower recall
        """)
    with col2:
        st.markdown("""
        **BERT Analyzer (Semantic)**
        - Understands meaning and context
        - Catches: "built REST APIs with Express" → Node.js 
        - Catches: "deployed on EKS" → Kubernetes 
        - Catches: "used GKE for orchestration" → Kubernetes 
        - Slightly slower but higher recall
        """)

section_divider()

# Step 1: Upload 
step_label(1, "Upload Resume")
uploaded = st.file_uploader(
    "Upload your resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

if not uploaded:
    st.info("Upload a resume to begin BERT analysis.")
    st.stop()

with st.spinner("Extracting text from resume..."):
    if uploaded.name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(uploaded) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    else:
        doc  = docx.Document(uploaded)
        text = "\n".join([p.text for p in doc.paragraphs])

if not text.strip():
    st.error("Could not extract text. Try a different file format.")
    st.stop()

st.success(f"Extracted {len(text):,} characters from resume")

with st.expander("View extracted text"):
    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

section_divider()

# Step 2: BERT Skill Extraction 
step_label(2, "BERT Skill Extraction")

with st.spinner("Running BERT semantic skill extraction... ~15 seconds"):
    skill_results = extract_skills_combined(text)

if not skill_results:
    st.warning("No skills detected. Make sure resume has technical content.")
    st.stop()

skills_df = pd.DataFrame(skill_results)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Skills Found",  len(skills_df))
c2.metric("High Confidence",
          len(skills_df[skills_df["confidence"] == "High"]))
c3.metric("BERT-only Finds",
          len(skills_df[skills_df["method"] == "BERT"]))
c4.metric("Both Methods",
          len(skills_df[skills_df["method"] == "Both"]))

st.markdown("#### Extracted Skills")
st.markdown("#### Extracted Skills")
tab1, tab2, tab3 = st.tabs(["All Skills", "High Confidence", "BERT-only Finds"])

with tab1:
    high = skills_df[skills_df["confidence"] == "High"]["skill"].tolist()
    med  = skills_df[skills_df["confidence"] != "High"]["skill"].tolist()
    if high:
        st.markdown("**🟢 High Confidence**")
        skill_badges(high, variant="high")
    if med:
        st.markdown("**🟡 Medium Confidence**")
        skill_badges(med, variant="medium")

with tab2:
    high_conf = skills_df[skills_df["confidence"] == "High"]
    if not high_conf.empty:
        skill_badges(high_conf["skill"].tolist(), variant="high")
    else:
        st.info("No high-confidence skills found.")

with tab3:
    bert_only = skills_df[skills_df["method"] == "BERT"]
    if bert_only.empty:
        st.info("No BERT-only finds — regex caught everything. "
                "Your resume uses standard terminology.")
    else:
        st.markdown("These skills were **missed by regex** but "
                    "**caught by BERT** through semantic understanding:")
        skill_badges(bert_only["skill"].tolist(), variant="medium")

section_divider()

# Step 3: BERT Role Detection
step_label(3, "BERT Role Detection")

with st.spinner("Running BERT role classification..."):
    role_rankings = detect_role_bert(text)

    st.session_state.resume_skills  = [r["skill"] for r in skill_results
                                    if r["confidence"] == "High"]
    st.session_state.detected_role  = role_rankings[0][0] if role_rankings else None
    st.session_state.resume_text    = text

st.markdown("**Role similarity scores — higher = better match:**")

top5_roles = role_rankings[:5]
mpl.rcParams.update(chart_style())
fig, ax    = plt.subplots(figsize=(10, 3))
roles_list = [r[0] for r in top5_roles]
scores     = [r[1] * 100 for r in top5_roles]
colors     = ["#00E676"] + ["#00D4FF"] * (len(top5_roles) - 1)
bars       = ax.barh(roles_list, scores, color=colors)
ax.bar_label(bars, fmt="%.1f%%", padding=3,
             color="#E8EDF5", fontsize=9)
ax.set_xlabel("Similarity Score (%)")
ax.set_title("BERT Role Detection — Top 5 Matches")
ax.invert_yaxis()
ax.set_xlim(0, 105)
plt.tight_layout()
st.pyplot(fig)
plt.close()

all_roles     = [r[0] for r in role_rankings]
detected_role = role_rankings[0][0]

selected_role = st.selectbox(
    f"BERT detected: **{detected_role}** — override if needed:",
    all_roles, index=0
)

high_conf_skills = skills_df[
    skills_df["confidence"] == "High"
]["skill"].tolist()
all_skills_list  = skills_df["skill"].tolist()

skill_set_choice = st.radio(
    "Which skills to use for gap analysis?",
    ["High confidence only", "All detected skills"],
    horizontal=True
)
resume_skills = (high_conf_skills
                 if skill_set_choice == "High confidence only"
                 else all_skills_list)

st.info(f"Using **{len(resume_skills)}** skills for gap analysis")

section_divider()

# Step 4: Gap Analysis 
step_label(4, "Skill Gap Analysis")

benchmark_df          = get_benchmark_skills(db, selected_role)
present, missing, gap = compute_gap(resume_skills, benchmark_df)

col1, col2, col3 = st.columns(3)
col1.metric("Your Gap Score",  f"{gap}%",  delta_color="inverse")
col2.metric("Skills Present",  len(present))
col3.metric("Skills Missing",  len(missing))

gap_bar(gap, label=f"{selected_role} benchmark coverage")

col1, col2 = st.columns(2)
with col1:
    st.markdown("** Skills you have:**")
    if present:
        skill_badges(present, variant="high")
    else:
        st.markdown("_None matched benchmark_")
with col2:
    st.markdown("**Skills missing from benchmark:**")
    if missing:
        skill_badges(missing, variant="missing")
    else:
        st.success("You have all benchmark skills!")

section_divider()

# Step 5: Personalized Roadmap
step_label(5, "Personalized Upskilling Roadmap")

job_recs = get_job_market_recs(db, selected_role, resume_skills)
roadmap  = build_roadmap(missing, job_recs)

if not roadmap.empty:
    # Priority breakdown
    high_p = roadmap[roadmap["Priority"] == 2]
    low_p  = roadmap[roadmap["Priority"] == 1]
    c1, c2 = st.columns(2)
    c1.metric("🔴 High Priority (2 signals)", len(high_p))
    c2.metric("🔵 Normal Priority (1 signal)", len(low_p))

    st.dataframe(
        roadmap,
        use_container_width=True,
        height=380,
        column_config={
            "Skill":    st.column_config.TextColumn("🛠️ Skill"),
            "Priority": st.column_config.NumberColumn("⭐ Priority"),
            "Sources":  st.column_config.TextColumn("📡 Sources"),
        }
    )

    # Roadmap bar chart
    mpl.rcParams.update(chart_style())
    fig2, ax2 = plt.subplots(figsize=(10, max(4, len(roadmap) * 0.38)))
    colors2   = ["#FF4560" if p == 2 else "#00D4FF"
                 for p in roadmap["Priority"]]
    ax2.barh(roadmap["Skill"], roadmap["Priority"], color=colors2)
    ax2.set_xlabel("Signal Strength")
    ax2.set_title(f"Skill Roadmap — {selected_role}")
    ax2.set_xlim(0, 2.8)
    ax2.set_xticks([1, 2])
    ax2.set_xticklabels(["1 source", "2 sources"])
    ax2.invert_yaxis()
    from matplotlib.patches import Patch
    ax2.legend(handles=[
        Patch(facecolor="#FF4560", label="High Priority"),
        Patch(facecolor="#00D4FF", label="Normal Priority"),
    ], loc="lower right")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    st.download_button(
        "Download Roadmap as CSV",
        roadmap.to_csv(index=False),
        file_name=f"roadmap_{selected_role.replace(' ','_')}.csv",
        mime="text/csv"
    )

section_divider()

# Step 6: Regex vs BERT Comparison
step_label(6, "Regex vs BERT Comparison")
st.markdown("See exactly what BERT found that basic regex missed.")

from utils.resume_parser import extract_skills as extract_regex
regex_skills = set(extract_regex(text))
bert_skills  = set(all_skills_list)
only_regex   = sorted(regex_skills - bert_skills)
only_bert    = sorted(bert_skills  - regex_skills)
both_found   = sorted(regex_skills & bert_skills)

col1, col2, col3 = st.columns(3)
col1.metric("Found by Both",     len(both_found))
col2.metric("Regex only",        len(only_regex))
col3.metric("BERT only (new!)",  len(only_bert))

if only_bert:
    st.success(
        f"BERT found **{len(only_bert)} additional skill(s)** "
        f"that regex missed:"
    )
    skill_badges(only_bert, variant="medium")
else:
    st.info("Both methods found the same skills for this resume.")
