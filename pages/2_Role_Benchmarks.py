import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
matplotlib.use("Agg")
from utils.db     import get_db
from utils.styles import (inject_styles, page_banner, step_label,
                           section_divider, chart_style)

st.set_page_config(
    page_title="Role Benchmarks",
    page_icon="📊", layout="wide"
)
inject_styles()

page_banner(
    "📊", "Role Benchmarks",
    "Skill prevalence across 32 developer roles — "
    "based on 90,000+ Stack Overflow responses"
)

db = get_db()

@st.cache_data
def load_benchmarks():
    docs = list(db["role_benchmarks"].find({}, {"_id": 0}))
    return pd.DataFrame(docs)

df = load_benchmarks()

if df.empty:
    st.warning("No benchmark data found. Run the Spark Pipeline first.")
    st.stop()

# Role selector
roles    = sorted(df["DevType"].unique().tolist())
selected = st.multiselect(
    "Select roles to compare:",
    roles,
    default=[r for r in
             ["Back-End Dev", "Data Scientist",
              "Full-Stack Dev", "DevOps specialist"]
             if r in roles]
)

if not selected:
    st.info("Select at least one role to see benchmarks.")
    st.stop()

filtered = df[df["DevType"].isin(selected)] \
             .sort_values("prevalence_pct", ascending=False)

section_divider()

# Step 1: Top skills per role
step_label(1, "Top 10 Skills per Role")

for role in selected:
    role_df = filtered[filtered["DevType"] == role].head(10)
    if role_df.empty:
        continue

    mpl.rcParams.update(chart_style())
    fig, ax = plt.subplots(figsize=(10, 4))

    # Gradient color by prevalence
    norm   = plt.Normalize(
        role_df["prevalence_pct"].min(),
        role_df["prevalence_pct"].max()
    )
    colors = plt.cm.Blues(norm(role_df["prevalence_pct"].values))

    bars = ax.barh(
        role_df["skill"],
        role_df["prevalence_pct"],
        color=colors
    )
    ax.bar_label(bars, fmt="%.1f%%", padding=4,
                 color="#E8EDF5", fontsize=9)
    ax.set_title(f"{role} — Top 10 Skills",
                 fontsize=13, pad=12)
    ax.set_xlabel("% of Developers with this Skill")
    ax.set_ylabel("")
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

section_divider()

# Step 2: Heatmap
step_label(2, "Skill Prevalence Heatmap")
st.markdown("Darker = more developers in that role know the skill.")

top_skills = (filtered.groupby("skill")["prevalence_pct"]
              .mean().nlargest(15).index.tolist())
heat_df    = (filtered[filtered["skill"].isin(top_skills)]
              .pivot_table(index="skill", columns="DevType",
                           values="prevalence_pct", fill_value=0))

if heat_df.empty:
    st.info("Not enough data for heatmap with selected roles.")
else:
    mpl.rcParams.update(chart_style())
    fig3, ax3 = plt.subplots(figsize=(max(10, len(selected) * 2.5), 8))
    sns.heatmap(
        heat_df,
        annot=True, fmt=".0f",
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="#0A0E1A",
        ax=ax3,
        cbar_kws={"shrink": 0.8}
    )
    ax3.set_title("Skill Prevalence % by Role", fontsize=13, pad=12)
    ax3.set_xlabel("")
    ax3.set_ylabel("")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

section_divider()

# Step 3: Role comparison table
step_label(3, "Full Benchmark Table")

role_filter = st.selectbox(
    "View all benchmark skills for:", selected
)
role_table = (df[df["DevType"] == role_filter]
              .sort_values("prevalence_pct", ascending=False)
              [["skill", "prevalence_pct", "dev_count", "total_devs"]]
              .rename(columns={
                  "skill":           "Skill",
                  "prevalence_pct":  "Prevalence %",
                  "dev_count":       "Devs with Skill",
                  "total_devs":      "Total Devs in Role"
              })
              .reset_index(drop=True))

st.dataframe(
    role_table.style.background_gradient(
        subset=["Prevalence %"], cmap="Blues"
    ),
    use_container_width=True,
    height=420
)
