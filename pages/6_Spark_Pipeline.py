import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
matplotlib.use("Agg")
import os
import tempfile
import seaborn as sns
from utils.spark_engine import (get_spark, load_and_preprocess,
                                 build_benchmark, compute_skill_gaps)
from utils.styles       import (inject_styles, page_banner, step_label,
                                 section_divider, chart_style)
import pyspark.sql.functions as F
from pyspark.ml.feature    import StringIndexer
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation  import RegressionEvaluator

st.set_page_config(
    page_title="Spark Pipeline",
    page_icon="⚡", layout="wide"
)
inject_styles()

page_banner(
    "⚡", "Apache Spark Pipeline",
    "Run the full Big Data pipeline — upload any Stack Overflow "
    "survey CSV and watch Spark process it live"
)

# Step 1: Upload CSVs 
step_label(1, "Upload Survey CSV Files")
st.info(
    "Upload any Stack Overflow Annual Developer Survey CSV files. "
    "Year will be detected automatically from the data."
)

uploaded_files = st.file_uploader(
    "Upload survey CSV files (one or more)",
    type=["csv"],
    accept_multiple_files=True,
    help="survey_results_public.csv from any Stack Overflow Annual Survey"
)

if not uploaded_files:
    st.warning("Please upload at least one survey CSV to proceed.")
    st.stop()

section_divider()

# Step 2: Year detection 
step_label(2, "Auto-detecting Survey Years")

def detect_year_from_df(df):
    for col_name in ["Year", "SurveyYear", "year", "survey_year"]:
        if col_name in df.columns:
            val = df[col_name].dropna().iloc[0]
            try:
                return int(str(val)[:4])
            except:
                pass
    for col in df.columns:
        for year in range(2020, 2030):
            if str(year) in col:
                return year
    date_cols = [c for c in df.columns
                 if any(kw in c.lower()
                        for kw in ["date","time","when","start"])]
    for col in date_cols:
        for val in df[col].dropna().head(10):
            for year in range(2020, 2030):
                if str(year) in str(val):
                    return year
    col_set = set(df.columns)
    if "AINextYears5"              in col_set: return 2025
    if "AIToolCurrently Using"     in col_set: return 2024
    if "AISearchHaveWorkedWith"    in col_set: return 2023
    if "VCInteraction"             in col_set: return 2022
    if "SOVisitFreq" in col_set and "SOAccount" in col_set: return 2021
    return None

file_info = {}

for f in uploaded_files:
    try:
        preview_df = pd.read_csv(f, nrows=100)
        f.seek(0)
    except Exception as e:
        st.error(f"Could not read {f.name}: {e}")
        continue

    detected_year = detect_year_from_df(preview_df)

    col1, col2, col3 = st.columns([3, 1, 2])
    with col1:
        st.markdown(
            f"**{f.name}** "
            f"({f.size/1e6:.1f} MB · "
            f"{len(preview_df.columns)} columns)"
        )
    with col2:
        if detected_year:
            st.success(f"Year: {detected_year}")
        else:
            st.warning("Not detected")
    with col3:
        manual_year = st.number_input(
            "Set year manually",
            min_value=2015, max_value=2030,
            value=detected_year if detected_year else 2023,
            key=f"year_{f.name}",
            help="Override if auto-detection is wrong"
        )

    file_info[f.name] = {
        "file":    f,
        "year":    manual_year,
        "preview": preview_df,
        "n_cols":  len(preview_df.columns),
    }

if not file_info:
    st.error("No valid files found.")
    st.stop()

years_assigned = [v["year"] for v in file_info.values()]
if len(years_assigned) != len(set(years_assigned)):
    st.warning("Duplicate years detected. Check manual year inputs.")

st.markdown(
    f"**Ready to process:** {len(file_info)} file(s) — "
    f"Years: `{sorted(set(years_assigned))}`"
)

section_divider()

# Step 3: Preview 
step_label(3, "Preview Uploaded Data")

selected_preview = st.selectbox(
    "Select file to preview:", list(file_info.keys())
)
info = file_info[selected_preview]
st.markdown(
    f"**Year: {info['year']} · Columns: {info['n_cols']}**"
)
st.dataframe(info["preview"].head(5), use_container_width=True)

relevant = ["ResponseId", "DevType", "LanguageHaveWorkedWith",
            "LanguageWantToWorkWith", "YearsCodePro",
            "ConvertedCompYearly", "Country", "EdLevel"]
found   = [c for c in relevant if c in info["preview"].columns]
missing = [c for c in relevant if c not in info["preview"].columns]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Relevant columns found:**")
    st.markdown(" · ".join([f"`{c}`" for c in found]))
with col2:
    if missing:
        st.markdown("**Missing columns:**")
        st.markdown(" · ".join([f"`{c}`" for c in missing]))

section_divider()

# Step 4: Pipeline Settings
step_label(4, "Pipeline Settings")

col1, col2, col3 = st.columns(3)
with col1:
    threshold = st.slider(
        "Benchmark Threshold (%)", 10, 50, 30, 5,
        help="Skills used by X% or more of a role = benchmark skill"
    )
with col2:
    als_rank = st.selectbox("ALS Rank", [5, 10, 20, 50], index=1)
with col3:
    als_iter = st.selectbox("ALS Max Iterations", [5, 10, 15, 20], index=2)

st.markdown(f"""
<div class="stat-card" style="margin-top:8px">
    <div style="font-family:'Space Mono',monospace; font-size:0.78rem;
                color:#8892A4; line-height:2.2">
        <span style="color:#00D4FF">›</span>
        Process <strong style="color:#E8EDF5">{len(file_info)} year(s)</strong>
        of survey data &nbsp;·&nbsp;
        Benchmark threshold <strong style="color:#E8EDF5">{threshold}%</strong>
        &nbsp;·&nbsp;
        ALS rank=<strong style="color:#E8EDF5">{als_rank}</strong>
        maxIter=<strong style="color:#E8EDF5">{als_iter}</strong>
    </div>
</div>
""", unsafe_allow_html=True)

section_divider()

# Step 5: Run Pipeline 
step_label(5, "Run Spark Pipeline")

run_btn = st.button(
    f"⚡ Run Spark Pipeline on {len(file_info)} file(s)",
    type="primary"
)

if run_btn:
    log_placeholder = st.empty()
    log_lines       = []

    def progress_cb(msg):
        log_lines.append(msg)
        log_placeholder.code("\n".join(log_lines), language="bash")

    # Save to temp files
    temp_paths = {}
    for fname, info in file_info.items():
        f = info["file"]
        f.seek(0)
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv",
            prefix=f"so_survey_{info['year']}_"
        )
        tmp.write(f.read())
        tmp.close()
        temp_paths[info["year"]] = tmp.name

    with st.spinner("Running Spark pipeline... 3–5 minutes"):
        try:
            spark = get_spark()
            progress_cb(f"Spark {spark.version} started")
            progress_cb(
                f"   Processing years: {sorted(temp_paths.keys())}"
            )

            # Load & preprocess
            dfs = []
            for year, path in sorted(temp_paths.items()):
                df = load_and_preprocess(path, year, progress_cb)
                dfs.append(df)

            # Union
            progress_cb(f"\nCombining {len(dfs)} dataset(s)...")
            df_all = dfs[0]
            for df in dfs[1:]:
                common = list(set(df_all.columns) & set(df.columns))
                df_all = df_all.select(common).union(df.select(common))

            total_rows    = df_all.count()
            unique_users  = df_all.select("ResponseId").distinct().count()
            unique_skills = df_all.select("skill").distinct().count()
            unique_roles  = df_all.select("DevType").distinct().count()

            progress_cb(f"   Skill rows    : {total_rows:,}")
            progress_cb(f"   Developers    : {unique_users:,}")
            progress_cb(f"   Unique skills : {unique_skills}")
            progress_cb(f"   Unique roles  : {unique_roles}")

            # Benchmark
            benchmark_full, benchmark_skills = build_benchmark(
                df_all, threshold=threshold, progress_cb=progress_cb
            )

            # ALS
            progress_cb(
                f"\nTraining ALS "
                f"(rank={als_rank}, maxIter={als_iter})..."
            )

            user_indexer  = StringIndexer(
                inputCol="ResponseId", outputCol="userIndex"
            )
            df_indexed    = user_indexer.fit(df_all).transform(df_all)
            skill_indexer = StringIndexer(
                inputCol="skill", outputCol="skillIndex"
            )
            df_indexed    = skill_indexer.fit(df_indexed).transform(df_indexed)
            df_indexed    = (df_indexed
                             .withColumn("rating",     F.lit(1.0))
                             .withColumn("userIndex",  F.col("userIndex").cast("integer"))
                             .withColumn("skillIndex", F.col("skillIndex").cast("integer")))

            train, test = df_indexed.randomSplit([0.8, 0.2], seed=42)
            progress_cb(
                f"   Train: {train.count():,} | Test: {test.count():,}"
            )

            als = ALS(
                rank=als_rank, maxIter=als_iter, regParam=0.1,
                userCol="userIndex", itemCol="skillIndex",
                ratingCol="rating",
                coldStartStrategy="drop", implicitPrefs=True
            )
            als_model = als.fit(train)

            evaluator = RegressionEvaluator(
                metricName="rmse", labelCol="rating",
                predictionCol="prediction"
            )
            rmse = evaluator.evaluate(als_model.transform(test))
            progress_cb(f"ALS trained | RMSE: {rmse:.4f}")

            # Skill gaps
            gap_df, role_gap = compute_skill_gaps(
                df_all, benchmark_skills, progress_cb
            )

            # Skill trends
            progress_cb("\nComputing skill trends...")
            total_per_year = df_all.groupBy("year").agg(
                F.countDistinct("ResponseId").alias("total_users")
            )
            skill_per_year = df_all.groupBy("year", "skill").agg(
                F.countDistinct("ResponseId").alias("user_count")
            )
            skill_trends = (skill_per_year
                            .join(total_per_year, on="year", how="left")
                            .withColumn("prevalence_pct",
                                F.round((F.col("user_count") /
                                         F.col("total_users")) * 100, 2))
                            .select("year", "skill", "user_count",
                                    "total_users", "prevalence_pct")
                            .orderBy("year",
                                     F.col("prevalence_pct").desc()))
            skill_trends.cache()
            skill_trends.count()
            progress_cb(
                f"{skill_trends.count()} trend entries computed"
            )

            # Cache everything
            progress_cb("\nCaching results to memory...")
            df_all.cache();           df_all.count()
            benchmark_full.cache();   benchmark_full.count()
            benchmark_skills.cache(); benchmark_skills.count()
            role_gap.cache();         role_gap.count()
            gap_df.cache();           gap_df.count()
            bench_count = benchmark_skills.count()
            progress_cb("   All DataFrames cached")

            st.session_state["spark_results"] = {
                "df_skills":        df_all,
                "benchmark_full":   benchmark_full,
                "benchmark_skills": benchmark_skills,
                "als_model":        als_model,
                "df_indexed":       df_indexed,
                "gap_df":           gap_df,
                "skill_trends":     skill_trends,
                "role_gap":         role_gap,
                "rmse":             rmse,
                "years":            sorted(temp_paths.keys()),
                "threshold":        threshold,
                "als_rank":         als_rank,
                "total_rows":       total_rows,
                "unique_users":     unique_users,
                "benchmark_count":  bench_count,
            }

            progress_cb("\nPipeline complete!")
            st.success("Pipeline completed successfully!")
            st.balloons()

        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.exception(e)

        finally:
            for path in temp_paths.values():
                try:
                    os.unlink(path)
                except:
                    pass

# Step 6: Results
if "spark_results" in st.session_state:
    results = st.session_state["spark_results"]

    section_divider()
    step_label(6, "Pipeline Results")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Years",            str(results["years"]))
    c2.metric("Skill Rows",       f"{results['total_rows']:,}")
    c3.metric("Developers",       f"{results['unique_users']:,}")
    c4.metric("Benchmark Skills", results["benchmark_count"])
    c5.metric("ALS RMSE",         f"{results['rmse']:.4f}")

    section_divider()

    # Top missing skills
    st.markdown("####Top Missing Skills by Role")
    role_gap_pdf   = results["role_gap"].toPandas()
    all_roles      = sorted(role_gap_pdf["DevType"].unique().tolist())
    selected_roles = st.multiselect(
        "Select roles to display:",
        all_roles,
        default=[r for r in
                 ["Back-End Dev", "Data Scientist",
                  "Full-Stack Dev", "DevOps specialist"]
                 if r in all_roles]
    )

    for role in selected_roles:
        role_df = role_gap_pdf[
            role_gap_pdf["DevType"] == role
        ].head(10)
        if role_df.empty:
            continue
        mpl.rcParams.update(chart_style())
        fig, ax = plt.subplots(figsize=(10, 3))
        norm_r  = plt.Normalize(role_df["gap_count"].min(),
                                role_df["gap_count"].max())
        col_r   = plt.cm.Reds(norm_r(role_df["gap_count"].values))
        bars_r  = ax.barh(role_df["missing_skill"],
                          role_df["gap_count"], color=col_r)
        ax.bar_label(bars_r, padding=3, color="#E8EDF5", fontsize=8)
        ax.set_title(f"Top Missing Skills — {role}")
        ax.set_xlabel("Developers missing this skill")
        ax.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    section_divider()

    # Heatmap
    st.markdown("#### Skill Prevalence Heatmap")
    bench_pdf  = results["benchmark_full"].toPandas()
    top_skills = (bench_pdf.groupby("skill")["prevalence_pct"]
                  .mean().nlargest(15).index.tolist())
    top_roles  = selected_roles if selected_roles else all_roles[:6]
    heat_data  = (bench_pdf[
                      bench_pdf["skill"].isin(top_skills) &
                      bench_pdf["DevType"].isin(top_roles)
                  ].pivot_table(index="skill", columns="DevType",
                                values="prevalence_pct", fill_value=0))

    if not heat_data.empty:
        mpl.rcParams.update(chart_style())
        fig2, ax2 = plt.subplots(
            figsize=(max(10, len(top_roles) * 2.5), 8)
        )
        sns.heatmap(
            heat_data, annot=True, fmt=".0f",
            cmap="YlOrRd", linewidths=0.5,
            linecolor="#0A0E1A", ax=ax2,
            cbar_kws={"shrink": 0.8}
        )
        ax2.set_title("Skill Prevalence % by Role",
                      fontsize=13, pad=12)
        ax2.set_xlabel("")
        ax2.set_ylabel("")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
    else:
        st.info("Select roles above to see the heatmap.")

    section_divider()

    # ALS summary
    st.markdown("#### 🤖 ALS Model Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.json({
            "algorithm":           "ALS (Alternating Least Squares)",
            "rank":                results["als_rank"],
            "regParam":            0.1,
            "implicitPrefs":       True,
            "coldStartStrategy":   "drop",
            "trainTestSplit":      "80 / 20",
            "RMSE":                round(results["rmse"], 4),
            "years_processed":     results["years"],
            "benchmark_threshold": f"{results['threshold']}%",
        })
    with col2:
        st.markdown("""
        **How ALS works in this project:**
        - Builds a user × skill matrix (1 = knows, 0 = doesn't)
        - Factorizes into latent factor vectors
        - Finds developers with similar skill patterns
        - Recommends skills those similar developers have
        - Personalised per developer, not just role-based

        **Why implicit feedback:**
        - No ratings (1–5 stars) exist here
        - We only know if someone has a skill or not
        - `implicitPrefs=True` treats 1 as confidence
        """)

    section_divider()

    # MongoDB push
    st.markdown("#### 💾 Save Results to MongoDB")
    st.markdown(
        "Push freshly computed Spark results to MongoDB Atlas. "
        "Skill trends are merged — existing years not overwritten."
    )

    if st.button("Push Pipeline Results to MongoDB",
                 type="primary"):
        try:
            from utils.db import get_db
            import math

            db_conn = get_db()

            def clean(obj):
                if isinstance(obj, dict):
                    return {k: clean(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean(i) for i in obj]
                elif isinstance(obj, float) and math.isnan(obj):
                    return None
                elif hasattr(obj, "item"):
                    return obj.item()
                return obj

            with st.spinner("Pushing to MongoDB Atlas..."):

                # Benchmarks
                bench_recs = [
                    clean(r) for r in
                    results["benchmark_full"]
                    .toPandas().to_dict(orient="records")
                ]
                db_conn["role_benchmarks"].drop()
                db_conn["role_benchmarks"].insert_many(bench_recs)
                st.success(
                    f"role_benchmarks: {len(bench_recs)} docs"
                )

                # Gap summary
                gap_recs = [
                    clean(r) for r in
                    results["role_gap"]
                    .toPandas().to_dict(orient="records")
                ]
                db_conn["skill_gaps"].drop()
                db_conn["skill_gaps"].insert_many(gap_recs)
                st.success(
                    f"skill_gaps: {len(gap_recs)} docs"
                )

                # Skill trends — merge, don't overwrite
                new_trend_recs = [
                    clean(r) for r in
                    results["skill_trends"]
                    .toPandas().to_dict(orient="records")
                ]
                for year in results["years"]:
                    db_conn["skill_trends"].delete_many({"year": year})
                db_conn["skill_trends"].insert_many(new_trend_recs)

                total_trend = db_conn["skill_trends"].count_documents({})
                all_years   = sorted(
                    db_conn["skill_trends"].distinct("year")
                )
                st.success(
                    f"skill_trends: {total_trend} docs "
                    f"| Years in DB: {all_years}"
                )

            st.success(" MongoDB Atlas updated with fresh Spark results!")
            st.info(
                "Go to Skill Trends → click Refresh "
                "to see the updated years."
            )

        except Exception as e:
            st.error(f"MongoDB push failed: {e}")
            st.exception(e)
