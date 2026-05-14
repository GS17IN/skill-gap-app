import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
matplotlib.use("Agg")
from utils.db     import get_db
from utils.styles import (inject_styles, page_banner, step_label,
                           section_divider, chart_style)

st.set_page_config(
    page_title="Job Market Demand",
    page_icon="💼", layout="wide"
)
inject_styles()

page_banner(
    "💼", "Job Market Demand",
    "Skills demanded by real job postings scraped live "
    "from RemoteOK, Remotive, and TheMuse"
)

db = get_db()

@st.cache_data
def load_jobs():
    docs = list(db["scraped_jobs"].find({}, {"_id": 0}))
    return pd.DataFrame(docs)

df = load_jobs()

if df.empty:
    st.warning("Job market data not found in MongoDB. "
               "Run the Spark Pipeline and scrape jobs first.")
    st.stop()

# Summary stat card 
col_stat, col_src, col_role = st.columns([1, 2, 2])

with col_stat:
    st.markdown(f"""
    <div class="stat-card" style="text-align:center">
        <div class="label">Total Job Postings</div>
        <div class="value">{len(df):,}</div>
        <div class="sub">{df['source'].nunique()} sources · {df['role'].nunique()} roles</div>
    </div>
    """, unsafe_allow_html=True)

section_divider()

# Step 1: Source & Role breakdown 
step_label(1, "Job Postings Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Source**")
    source_counts = df["source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Count"]

    mpl.rcParams.update(chart_style())
    fig, ax = plt.subplots(figsize=(6, 3))

    colors_bar = ["#00D4FF", "#FFB800", "#00E676",
                  "#FF4560", "#9B59B6"][:len(source_counts)]

    bars = ax.barh(
        source_counts["Source"],
        source_counts["Count"],
        color=colors_bar,
        edgecolor="#0A0E1A",
        linewidth=0.5,
        height=0.5
    )
    ax.bar_label(
        bars,
        labels=[f"{v:,} ({v/source_counts['Count'].sum()*100:.1f}%)"
                for v in source_counts["Count"]],
        padding=6,
        color="#E8EDF5",
        fontsize=9
    )
    ax.set_xlabel("Number of Postings")
    ax.set_title("Jobs by Source")
    ax.set_xlim(0, source_counts["Count"].max() * 1.35)
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.markdown("**By Role**")
    role_counts = df["role"].value_counts()
    mpl.rcParams.update(chart_style())
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    norm2   = plt.Normalize(role_counts.min(), role_counts.max())
    colors2 = plt.cm.Blues(norm2(role_counts.values))
    bars2   = ax2.barh(role_counts.index, role_counts.values,
                       color=colors2)
    ax2.bar_label(bars2, padding=3, color="#E8EDF5", fontsize=8)
    ax2.set_xlabel("Number of Postings")
    ax2.set_title("Jobs by Role")
    ax2.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

section_divider()

# Step 2: Top skills per role
step_label(2, "Top Skills Demanded by Role")

roles    = sorted(df["role"].dropna().unique().tolist())
selected = st.selectbox("Select role to explore:", roles)

role_df    = df[df["role"] == selected].copy()
skills_exp = (role_df["skills"]
              .str.split(", ")
              .explode()
              .str.strip()
              .replace("N/A", pd.NA)
              .dropna())

if skills_exp.empty:
    st.warning(f"No skill data found for {selected}.")
else:
    top_skills = skills_exp.value_counts().head(15).reset_index()
    top_skills.columns = ["skill", "count"]

    mpl.rcParams.update(chart_style())
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    norm3   = plt.Normalize(top_skills["count"].min(),
                            top_skills["count"].max())
    colors3 = plt.cm.YlOrRd(norm3(top_skills["count"].values))
    bars3   = ax3.barh(top_skills["skill"],
                       top_skills["count"], color=colors3)
    ax3.bar_label(bars3, padding=3, color="#E8EDF5", fontsize=9)
    ax3.set_xlabel("Number of Job Postings Requiring Skill")
    ax3.set_title(f"Top 15 Skills Demanded — {selected}")
    ax3.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

    # Skills table
    with st.expander("View full skill demand table"):
        all_skills = skills_exp.value_counts().reset_index()
        all_skills.columns = ["Skill", "Job Postings"]
        st.dataframe(
            all_skills.style.background_gradient(
                subset=["Job Postings"], cmap="YlOrRd"
            ),
            use_container_width=True,
            height=350
        )

section_divider()

# Step 3: Cross-role skill demand
step_label(3, "Cross-Role Skill Demand")
st.markdown("Which skills appear across the most roles?")

all_exploded = (df[["role", "skills"]]
                .copy()
                .assign(skill=df["skills"].str.split(", "))
                .explode("skill")
                .assign(skill=lambda x: x["skill"].str.strip())
                .query("skill != 'N/A' and skill != ''")
                .dropna(subset=["skill"]))

cross_role = (all_exploded
              .groupby("skill")["role"]
              .nunique()
              .sort_values(ascending=False)
              .head(15)
              .reset_index())
cross_role.columns = ["Skill", "Roles Requiring It"]

mpl.rcParams.update(chart_style())
fig4, ax4 = plt.subplots(figsize=(10, 5))
norm4   = plt.Normalize(cross_role["Roles Requiring It"].min(),
                        cross_role["Roles Requiring It"].max())
colors4 = plt.cm.Blues(norm4(cross_role["Roles Requiring It"].values))
bars4   = ax4.barh(cross_role["Skill"],
                   cross_role["Roles Requiring It"],
                   color=colors4)
ax4.bar_label(bars4, padding=3, color="#E8EDF5", fontsize=9,
              fmt="%d roles")
ax4.set_xlabel("Number of Roles Requiring This Skill")
ax4.set_title("Most Universally Demanded Skills")
ax4.invert_yaxis()
ax4.set_xlim(0, cross_role["Roles Requiring It"].max() + 2)
plt.tight_layout()
st.pyplot(fig4)
plt.close()

st.dataframe(
    cross_role.style.background_gradient(
        subset=["Roles Requiring It"], cmap="Blues"
    ),
    use_container_width=True
)
