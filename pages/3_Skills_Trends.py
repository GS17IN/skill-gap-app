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
    page_title="Skill Trends",
    page_icon="📈", layout="wide"
)
inject_styles()

db = get_db()

# ── Load data ─────────────────────────────────────────────────────
def load_trends():
    docs = list(db["skill_trends"].find({}, {"_id": 0}))
    return pd.DataFrame(docs)

col_refresh, col_info = st.columns([1, 4])
with col_refresh:
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()
with col_info:
    st.info("Click Refresh after pushing new years via the Spark Pipeline.")

df = load_trends()

if df.empty:
    st.warning("No trend data found. Run the Spark Pipeline and push to MongoDB.")
    st.stop()

available_years = sorted(df["year"].dropna().unique().astype(int).tolist())
first_year      = available_years[0]
last_year       = available_years[-1]
n_years         = len(available_years)

page_banner(
    "📈", "Skill Trends Over Time",
    f"Year-over-year skill growth analysis across "
    f"{n_years} survey year(s): {available_years}"
)

if n_years < 2:
    st.info("Upload at least 2 years of survey data via the "
            "Spark Pipeline page to see trends.")

# ── Summary metrics ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Years Available",  str(available_years))
col2.metric("Skills Tracked",   df["skill"].nunique())
col3.metric("First Year",       first_year)
col4.metric("Latest Year",      last_year)

section_divider()

# ── Build pivot ───────────────────────────────────────────────────
pivot = df.pivot_table(
    index="skill", columns="year",
    values="prevalence_pct", fill_value=0
).reset_index()
pivot.columns = (["skill"] +
                 [str(int(y)) for y in pivot.columns[1:]])

first_col = str(first_year)
last_col  = str(last_year)
pivot["growth"] = pivot[last_col] - pivot[first_col]

# ── Step 1: Growing vs Declining ─────────────────────────────────
if n_years >= 2:
    step_label(1, f"Skill Growth: {first_year} → {last_year}")
    top_n = st.slider("Number of skills to show", 5, 20, 10)

    top_growing   = pivot.nlargest(top_n,  "growth")
    top_declining = pivot.nsmallest(top_n, "growth")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Top {top_n} Growing Skills**")
        mpl.rcParams.update(chart_style())
        fig, ax = plt.subplots(figsize=(8, top_n * 0.5 + 1))
        bars = ax.barh(
            top_growing["skill"],
            top_growing["growth"],
            color="#00E676"
        )
        ax.bar_label(bars, fmt="+%.1f%%", padding=3,
                     color="#E8EDF5", fontsize=9)
        ax.set_xlabel("Growth in Prevalence (%)")
        ax.set_title(f"{first_year} → {last_year}")
        ax.invert_yaxis()
        ax.axvline(x=0, color="#8892A4", linewidth=0.8)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown(f"**📉 Top {top_n} Declining Skills**")
        mpl.rcParams.update(chart_style())
        fig2, ax2 = plt.subplots(figsize=(8, top_n * 0.5 + 1))
        bars2 = ax2.barh(
            top_declining["skill"],
            top_declining["growth"],
            color="#FF4560"
        )
        ax2.bar_label(bars2, fmt="%.1f%%", padding=3,
                      color="#E8EDF5", fontsize=9)
        ax2.set_xlabel("Change in Prevalence (%)")
        ax2.set_title(f"{first_year} → {last_year}")
        ax2.invert_yaxis()
        ax2.axvline(x=0, color="#8892A4", linewidth=0.8)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    section_divider()

    # ── Step 2: Full growth table ─────────────────────────────────
    step_label(2, "Full Growth Table")
    display_pivot = pivot.copy().sort_values("growth", ascending=False)
    display_pivot["growth"] = display_pivot["growth"].round(2)
    st.dataframe(
        display_pivot.style.background_gradient(
            subset=["growth"], cmap="RdYlGn"
        ),
        use_container_width=True,
        height=400
    )

section_divider()

# ── Step 3: Line chart ────────────────────────────────────────────
step_label(3, "Skill Prevalence Over Time")

if n_years < 2:
    st.info("Add more years of data to see trend lines.")
else:
    all_skills_list = sorted(df["skill"].unique().tolist())
    default_skills  = [s for s in
                       ["Python", "JavaScript", "TypeScript",
                        "SQL", "Rust", "Go"]
                       if s in all_skills_list]

    selected_skills = st.multiselect(
        "Select skills to track:",
        all_skills_list,
        default=default_skills[:5]
    )

    if selected_skills:
        mpl.rcParams.update(chart_style())
        fig3, ax3 = plt.subplots(figsize=(12, 6))

        palette = ["#00D4FF", "#00E676", "#FFB800",
                   "#FF4560", "#9B59B6", "#E8EDF5"]
        for i, skill in enumerate(selected_skills):
            skill_df = (df[df["skill"] == skill]
                        .sort_values("year"))
            color    = palette[i % len(palette)]
            ax3.plot(
                skill_df["year"].astype(int),
                skill_df["prevalence_pct"],
                marker="o", label=skill,
                linewidth=2.5, markersize=7,
                color=color
            )
            if not skill_df.empty:
                last = skill_df.iloc[-1]
                ax3.annotate(
                    f"{last['prevalence_pct']:.1f}%",
                    xy=(int(last["year"]), last["prevalence_pct"]),
                    xytext=(6, 0),
                    textcoords="offset points",
                    fontsize=8, color=color
                )

        ax3.set_xlabel("Year")
        ax3.set_ylabel("% of Developers Using Skill")
        ax3.set_title("Skill Prevalence Over Time")
        ax3.set_xticks(available_years)
        ax3.set_xticklabels([str(y) for y in available_years])
        ax3.legend(loc="upper left",
                   bbox_to_anchor=(1, 1),
                   framealpha=0.3)
        ax3.grid(True, alpha=0.15)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()
    else:
        st.info("Select at least one skill to display the trend chart.")

section_divider()

# ── Step 4: Year-by-year snapshot ────────────────────────────────
step_label(4, "Year-by-Year Snapshot")
st.markdown("Top 15 skills for each available year.")

year_tabs = st.tabs([str(y) for y in available_years])

for tab, year in zip(year_tabs, available_years):
    with tab:
        year_df = (df[df["year"] == year]
                   .sort_values("prevalence_pct", ascending=False)
                   .head(15))
        if year_df.empty:
            st.warning(f"No data for {year}")
            continue

        mpl.rcParams.update(chart_style())
        fig4, ax4 = plt.subplots(figsize=(10, 5))
        norm4  = plt.Normalize(
            year_df["prevalence_pct"].min(),
            year_df["prevalence_pct"].max()
        )
        colors4 = plt.cm.Blues(norm4(year_df["prevalence_pct"].values))
        bars4   = ax4.barh(
            year_df["skill"],
            year_df["prevalence_pct"],
            color=colors4
        )
        ax4.bar_label(bars4, fmt="%.1f%%", padding=3,
                      color="#E8EDF5", fontsize=9)
        ax4.set_xlabel("% of Developers")
        ax4.set_title(f"Top 15 Skills — {year}")
        ax4.invert_yaxis()
        ax4.set_xlim(0, 105)
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

if n_years < 3:
    st.info(
        f" You have **{n_years}** year(s) of data ({available_years}). "
        f"Upload more survey CSVs via **⚡ Spark Pipeline** for richer analysis."
    )