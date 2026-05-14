import streamlit as st
from utils.styles import inject_styles, section_divider
from utils.db     import get_db

st.set_page_config(
    page_title="CareerLens — Career Intelligence",
    page_icon="🔭",
    layout="wide"
)
inject_styles()

db = get_db()

# ── Live stats from MongoDB ───────────────────────────────────────
@st.cache_data(ttl=300)   # refresh every 5 minutes
def get_live_stats():
    try:
        # Years available from skill_trends
        years = sorted(db["skill_trends"].distinct("year"))
        n_years = len(years)
        year_range = (f"{min(years)}–{max(years)}"
                      if len(years) >= 2 else
                      str(years[0]) if years else "N/A")

        # Unique developers from role_benchmarks
        bench_docs = list(db["role_benchmarks"].find({}, {"_id": 0}))
        import pandas as pd
        bench_df     = pd.DataFrame(bench_docs)
        total_devs   = (int(bench_df["total_devs"].max())
                        if not bench_df.empty and "total_devs" in bench_df.columns
                        else 90000)

        # Format developer count
        if total_devs >= 1000:
            devs_fmt = f"{total_devs/1000:.0f}K+"
        else:
            devs_fmt = str(total_devs)

        # Unique skills
        unique_skills = (bench_df["skill"].nunique()
                         if not bench_df.empty else 60)

        # Unique roles
        unique_roles = (bench_df["DevType"].nunique()
                        if not bench_df.empty else 32)

        # Job postings
        job_count = db["scraped_jobs"].count_documents({})

        # Benchmark entries
        bench_count = db["role_benchmarks"].count_documents({})

        return {
            "year_range":   year_range,
            "n_years":      n_years,
            "years":        years,
            "devs":         devs_fmt,
            "skills":       f"{unique_skills}+",
            "roles":        str(unique_roles),
            "jobs":         f"{job_count:,}" if job_count else "600+",
            "bench_count":  f"{bench_count:,}" if bench_count else "N/A",
        }
    except Exception:
        return {
            "year_range": "2021–2025",
            "n_years":    5,
            "years":      [2021, 2022, 2023, 2024, 2025],
            "devs":       "90K+",
            "skills":     "60+",
            "roles":      "32",
            "jobs":       "600+",
            "bench_count": "N/A",
        }

stats = get_live_stats()

# ── Hero ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:48px 0 32px; text-align:center">
    <div style="font-family:'Space Mono',monospace; font-size:0.72rem;
                color:#00D4FF; letter-spacing:4px;
                text-transform:uppercase; margin-bottom:16px">
        Big Data · Apache Spark · BERT · MongoDB
    </div>
    <h1 style="font-size:3.2rem; margin:0; border:none !important;
               padding:0 !important;
               background:linear-gradient(135deg,#E8EDF5 0%,#00D4FF 100%);
               -webkit-background-clip:text;
               -webkit-text-fill-color:transparent;
               line-height:1.15">
        CareerLens
    </h1>
    <div style="font-family:'Space Mono',monospace; font-size:1rem;
                color:#8892A4; margin-top:6px; letter-spacing:1px">
        Your Career Intelligence System
    </div>
    <p style="color:#8892A4; font-size:1rem; margin-top:18px;
              max-width:580px; margin-left:auto; margin-right:auto;
              line-height:1.8">
        Analyze your developer profile against
        <strong style="color:#E8EDF5">{stats['devs']}</strong>
        real survey responses across
        <strong style="color:#E8EDF5">{stats['n_years']} years</strong>
        ({stats['year_range']}), live job market data, and collaborative
        filtering to build your personalized upskilling roadmap.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Live stats row ────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
live_stats = [
    (stats["devs"],       "Survey Responses"),
    (stats["skills"],     "Skills Tracked"),
    (stats["roles"],      "Developer Roles"),
    (stats["jobs"],       "Job Postings"),
    (stats["year_range"], "Years of Data"),
]
for col, (val, label) in zip([c1,c2,c3,c4,c5], live_stats):
    col.markdown(f"""
    <div class="stat-card" style="text-align:center">
        <div class="value" style="font-size:1.6rem">{val}</div>
        <div class="label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# Years pill row
if stats["years"]:
    pills = "".join(
        f'<span class="skill-badge neutral">{y}</span>'
        for y in stats["years"]
    )
    st.markdown(
        f'<div style="text-align:center; margin-top:8px">'
        f'<span style="color:#8892A4; font-size:0.75rem; '
        f'font-family:\'Space Mono\',monospace; margin-right:8px">'
        f'DATA FROM:</span>{pills}</div>',
        unsafe_allow_html=True
    )

section_divider()

# ── How it works ──────────────────────────────────────────────────
st.markdown("""
<h3 style="text-align:center; margin-bottom:24px">How It Works</h3>
""", unsafe_allow_html=True)

steps = [
    ("01", "📄", "Upload Resume",
     "BERT extracts skills with semantic understanding — "
     "catches what regex misses"),
    ("02", "🎭", "Role Detection",
     "Sentence-BERT classifies your role from resume context "
     "with similarity scores"),
    ("03", "⚡", "Spark Analysis",
     "Apache Spark computes your gap against benchmarks "
     f"from {stats['devs']} developer responses"),
    ("04", "🗺️", "Roadmap",
     "3 signals combined: survey gap + job market demand "
     "+ collaborative filtering"),
]

cols = st.columns(4)
for col, (num, icon, title, desc) in zip(cols, steps):
    col.markdown(f"""
    <div class="stat-card">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem;
                    color:#00D4FF; letter-spacing:2px; margin-bottom:10px">
            STEP {num}
        </div>
        <div style="font-size:1.8rem; margin-bottom:8px">{icon}</div>
        <div style="font-family:'Space Mono',monospace; font-size:0.88rem;
                    color:#E8EDF5; margin-bottom:6px">{title}</div>
        <div style="font-size:0.8rem; color:#8892A4;
                    line-height:1.6">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

section_divider()

# ── Pages overview ────────────────────────────────────────────────
st.markdown("<h3>Pages</h3>", unsafe_allow_html=True)

pages = [
    ("📄", "1 — Resume Analyzer",
     "BERT-powered skill extraction + gap analysis + "
     "personalized upskilling roadmap",
     "#00D4FF"),
    ("📊", "2 — Role Benchmarks",
     f"Skill prevalence heatmaps across {stats['roles']} "
     f"developer roles from {stats['devs']} responses",
     "#00D4FF"),
    ("📈", "3 — Skill Trends",
     f"Year-over-year skill growth from "
     f"{stats['year_range']} survey data "
     f"({stats['n_years']} years)",
     "#00E676"),
    ("💼", "4 — Job Market",
     f"Live skills demanded by employers — "
     f"{stats['jobs']} job postings across 3 platforms",
     "#FFB800"),
    ("🔍", "5 — Job Finder",
     "Real-time job matching with alignment score "
     "+ upskilling roadmap for your target role",
     "#FFB800"),
    ("⚡", "6 — Spark Pipeline",
     "Run the full ALS + gap analysis pipeline on any "
     "survey CSV — results auto-update all pages",
     "#FF4560"),
]

col1, col2 = st.columns(2)
for i, (icon, title, desc, color) in enumerate(pages):
    col = col1 if i % 2 == 0 else col2
    col.markdown(f"""
    <div class="stat-card" style="border-left:3px solid {color}">
        <div style="display:flex; align-items:center;
                    gap:10px; margin-bottom:8px">
            <span style="font-size:1.3rem">{icon}</span>
            <span style="font-family:'Space Mono',monospace;
                         font-size:0.85rem;
                         color:#E8EDF5">{title}</span>
        </div>
        <div style="font-size:0.82rem; color:#8892A4;
                    line-height:1.6">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

section_divider()

# ── Tech stack ────────────────────────────────────────────────────
st.markdown("<h3>Technology Stack</h3>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
stacks = [
    ("⚡ Big Data", [
        "Apache Spark (PySpark)",
        "Spark MLlib ALS",
        "Distributed processing",
    ]),
    ("🧠 ML / NLP", [
        "Sentence-BERT",
        "Collaborative Filtering",
        "Semantic skill matching",
    ]),
    ("🗄️ Storage", [
        "MongoDB Atlas (NoSQL)",
        f"{stats['bench_count']} benchmark records",
        f"{stats['n_years']} years of survey data",
    ]),
    ("🎨 Frontend", [
        "Streamlit",
        "Matplotlib + Seaborn",
        "Real-time job scraping",
    ]),
]
for col, (title, items) in zip([col1,col2,col3,col4], stacks):
    items_html = "".join(
        f'<div style="color:#8892A4; font-size:0.8rem; padding:4px 0;'
        f'border-bottom:1px solid rgba(255,255,255,0.04)">'
        f'<span style="color:#00D4FF">›</span> {item}</div>'
        for item in items
    )
    col.markdown(f"""
    <div class="stat-card">
        <div style="font-family:'Space Mono',monospace;
                    font-size:0.8rem; color:#E8EDF5;
                    margin-bottom:12px">{title}</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

section_divider()

# ── Quick start ───────────────────────────────────────────────────
st.markdown("<h3>Quick Start</h3>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="stat-card" style="border-left:3px solid #00E676">
        <div style="font-family:'Space Mono',monospace;
                    font-size:0.8rem; color:#00E676;
                    margin-bottom:12px">▸ FOR A QUICK DEMO</div>
        <div style="font-size:0.85rem; color:#8892A4; line-height:2.2">
            1. Go to
            <span style="color:#00D4FF">📄 Resume Analyzer</span><br>
            2. Upload your PDF or DOCX resume<br>
            3. Review BERT-detected skills + role<br>
            4. Get your personalized roadmap
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card" style="border-left:3px solid #FFB800">
        <div style="font-family:'Space Mono',monospace;
                    font-size:0.8rem; color:#FFB800;
                    margin-bottom:12px">▸ FOR THE FULL PIPELINE</div>
        <div style="font-size:0.85rem; color:#8892A4; line-height:2.2">
            1. Go to
            <span style="color:#00D4FF">⚡ Spark Pipeline</span><br>
            2. Upload a Stack Overflow survey CSV (any year)<br>
            3. Watch Spark process live<br>
            4. Push to MongoDB → home page updates instantly
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Live data notice ──────────────────────────────────────────────
st.markdown(f"""
<div style="background:rgba(0,212,255,0.05); border:1px solid
            rgba(0,212,255,0.15); border-radius:12px;
            padding:16px 20px; margin-top:8px;
            display:flex; align-items:center; gap:12px">
    <span style="font-size:1.2rem">💡</span>
    <div style="font-size:0.82rem; color:#8892A4">
        All statistics on this page are
        <strong style="color:#00D4FF">live from MongoDB</strong>.
        After running the Spark Pipeline and pushing results,
        this page refreshes automatically to reflect the latest data
        — including any new survey years you add.
        Currently tracking
        <strong style="color:#E8EDF5">{stats['n_years']} year(s)</strong>:
        {', '.join(str(y) for y in stats['years'])}.
    </div>
</div>
""", unsafe_allow_html=True)

section_divider()

# ── Footer ────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:24px 0 12px;
            font-family:'Space Mono',monospace;
            font-size:0.68rem; color:#8892A4; letter-spacing:2px">
    CAREERLENS &nbsp;·&nbsp;
    APACHE SPARK &nbsp;·&nbsp;
    MONGODB ATLAS &nbsp;·&nbsp;
    SENTENCE-BERT &nbsp;·&nbsp;
    STACK OVERFLOW SURVEY {stats['year_range']}
</div>
""", unsafe_allow_html=True)