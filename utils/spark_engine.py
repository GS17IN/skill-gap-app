import re
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

# Singleton Spark session 
_spark = None

def get_spark():
    global _spark
    if _spark is None:
        _spark = SparkSession.builder \
            .appName("SkillGapAnalysis") \
            .config("spark.driver.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "8") \
            .config("spark.hadoop.fs.defaultFS", "file:///") \
            .config("spark.hadoop.fs.file.impl",
                    "org.apache.hadoop.fs.LocalFileSystem") \
            .config("spark.hadoop.fs.hdfs.impl",
                    "org.apache.hadoop.hdfs.DistributedFileSystem") \
            .master("local[*]") \
            .getOrCreate()
        _spark.sparkContext.setLogLevel("ERROR")
    return _spark


# Skill list
KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "C", "Go",
    "Rust", "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "SQL",
    "HTML/CSS", "Bash/Shell (all shells)", "PowerShell", "Dart", "Lua",
    "MATLAB", "Perl", "Assembly", "Groovy", "Elixir", "Clojure",
    "Haskell", "Julia", "React", "Angular", "Vue", "Node.js", "Django",
    "Flask", "FastAPI", "Spring", "TensorFlow", "PyTorch", "Kubernetes",
    "Docker", "Spark", "Hadoop", "Kafka", "Airflow", "AWS", "Azure",
    "GCP", "Linux", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Elasticsearch", "Terraform", "Ansible", "Jenkins", "Git",
    "Grafana", "Prometheus"
]

DEVTYPE_MAP = {
    "Developer, full-stack":                         "Full-Stack Dev",
    "Developer, back-end":                           "Back-End Dev",
    "Developer, front-end":                          "Front-End Dev",
    "Developer, mobile":                             "Mobile Dev",
    "Data scientist or machine learning specialist": "Data Scientist",
    "Data or business analyst":                      "Data Analyst",
    "Engineer, data":                                "Data Engineer",
    "DevOps specialist":                             "DevOps specialist",
    "Engineer, site reliability":                    "SRE",
    "Security professional":                         "Security Engineer",
    "Developer, embedded applications or devices":   "Embedded Dev",
    "Developer, desktop or enterprise applications": "Desktop Dev",
    "Developer, game or graphics":                   "Game/Graphics Dev",
    "Cloud infrastructure engineer":                 "Cloud Engineer",
    "Engineer, hardware":                            "Hardware Engineer",
    "Developer, QA or test":                         "QA Engineer",
    "Blockchain":                                    "Blockchain Dev",
    "Developer Experience":                          "Dev Experience",
    "Developer Advocate":                            "Dev Advocate",
    "Database administrator":                        "DBA",
    "System administrator":                          "SysAdmin",
    "Engineering manager":                           "Eng Manager",
    "Product manager":                               "Product Manager",
    "Project manager":                               "Project Manager",
    "Scientist":                                     "Scientist",
    "Researcher":                                    "Researcher",
    "Educator":                                      "Educator",
    "Designer":                                      "Designer",
    "Senior Executive (C-Suite, VP, etc.)":          "Executive",
    "Marketing or sales professional":               "Sales/Marketing",
    "Student":                                       "Student",
}

# Step 1: Load & preprocess survey CSV

def load_and_preprocess(csv_path, year, progress_cb=None):
    spark = get_spark()
    if progress_cb: progress_cb(f"Loading {year} survey CSV...")


    if not csv_path.startswith("file://"):
        csv_path = "file://" + csv_path

    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    if progress_cb: progress_cb(f" Loaded {df.count():,} rows")

    # Select relevant columns
    cols = ["ResponseId", "DevType", "LanguageHaveWorkedWith"]
    df   = df.select(cols) \
             .filter(F.col("DevType").isNotNull()) \
             .filter(F.col("LanguageHaveWorkedWith").isNotNull()) \
             .filter(F.col("DevType") != "NA") \
             .filter(F.col("LanguageHaveWorkedWith") != "NA")

    # Map DevType
    map_expr = F.create_map(*[
        item for pair in
        [(F.lit(k), F.lit(v)) for k, v in DEVTYPE_MAP.items()]
        for item in pair
    ])
    df = df.withColumn("DevType", map_expr[F.col("DevType")]) \
           .filter(F.col("DevType").isNotNull()) \
           .withColumn("year", F.lit(year))

    # Explode skills
    df_skills = df \
        .withColumn("skill_raw",
            F.explode(F.split(F.col("LanguageHaveWorkedWith"), ";"))) \
        .withColumn("skill", F.trim(F.col("skill_raw"))) \
        .filter(F.col("skill") != "") \
        .filter(F.col("skill") != "NA") \
        .select("ResponseId", "DevType", "skill", "year")

    if progress_cb:
        progress_cb(f" {df_skills.count():,} skill rows after preprocessing")

    return df_skills


# Step 2: Build role benchmark 
def build_benchmark(df_skills, threshold=30, progress_cb=None):
    if progress_cb: progress_cb("Building role benchmark...")

    role_skill_freq = df_skills \
        .groupBy("DevType", "skill") \
        .agg(F.count("*").alias("dev_count"))

    role_total = df_skills \
        .select("DevType", "ResponseId").distinct() \
        .groupBy("DevType") \
        .agg(F.count("ResponseId").alias("total_devs"))

    benchmark = role_skill_freq \
        .join(role_total, on="DevType", how="left") \
        .withColumn("prevalence_pct",
            F.round((F.col("dev_count") / F.col("total_devs")) * 100, 2))

    benchmark_skills = benchmark \
        .filter(F.col("prevalence_pct") >= threshold) \
        .select(
            F.col("DevType").cast("string"),
            F.col("skill").cast("string"),
            F.col("prevalence_pct")
        )

    count = benchmark_skills.count()
    if progress_cb:
        progress_cb(f" {count} benchmark skill-role pairs (threshold={threshold}%)")

    return benchmark, benchmark_skills


# Step 3: Train ALS model 
def train_als(df_skills, progress_cb=None):
    if progress_cb: progress_cb("Training ALS Collaborative Filtering model...")

    # Index users and skills
    user_indexer  = StringIndexer(inputCol="ResponseId", outputCol="userIndex")
    df_indexed    = user_indexer.fit(df_skills).transform(df_skills)
    skill_indexer = StringIndexer(inputCol="skill",      outputCol="skillIndex")
    df_indexed    = skill_indexer.fit(df_indexed).transform(df_indexed)

    df_indexed = df_indexed \
        .withColumn("rating",     F.lit(1.0)) \
        .withColumn("userIndex",  F.col("userIndex").cast("integer")) \
        .withColumn("skillIndex", F.col("skillIndex").cast("integer"))

    train, test = df_indexed.randomSplit([0.8, 0.2], seed=42)
    if progress_cb:
        progress_cb(f"  Train: {train.count():,} | Test: {test.count():,}")

    als = ALS(
        rank=10, maxIter=15, regParam=0.1,
        userCol="userIndex", itemCol="skillIndex", ratingCol="rating",
        coldStartStrategy="drop", implicitPrefs=True
    )
    model = als.fit(train)

    # Evaluate
    evaluator = RegressionEvaluator(
        metricName="rmse", labelCol="rating", predictionCol="prediction"
    )
    rmse = evaluator.evaluate(model.transform(test))
    if progress_cb:
        progress_cb(f" ALS trained | RMSE: {rmse:.4f}")

    return model, df_indexed


# Step 4: Compute skill gaps
def compute_skill_gaps(df_skills, benchmark_skills, progress_cb=None):
    if progress_cb: progress_cb("Computing skill gaps...")

    user_has  = df_skills.select("ResponseId", "DevType", "skill").distinct()
    user_roles = user_has.select("ResponseId", "DevType").distinct()

    user_benchmark = user_roles.join(benchmark_skills, on="DevType", how="left")
    gap_df = user_benchmark.join(
        user_has,
        on=["ResponseId", "DevType", "skill"],
        how="left_anti"
    ).withColumnRenamed("skill", "missing_skill")

    role_gap = gap_df \
        .groupBy("DevType", "missing_skill") \
        .agg(F.count("*").alias("gap_count")) \
        .orderBy("DevType", F.col("gap_count").desc())

    if progress_cb:
        progress_cb(f" {gap_df.count():,} total skill gaps found")

    return gap_df, role_gap


# Step 5: Resume gap using Spark 
def compute_resume_gap_spark(resume_skills, detected_role,
                              benchmark_skills_df, progress_cb=None):
    if progress_cb: progress_cb("Computing resume gap with Spark...")

    spark = get_spark()

    # Create resume skills DataFrame
    resume_data = [(s,) for s in resume_skills]
    resume_sdf  = spark.createDataFrame(resume_data, ["skill"])

    # Get benchmark for role
    role_bench = benchmark_skills_df \
        .filter(F.col("DevType") == detected_role) \
        .select("skill")

    # Left anti join → missing skills
    missing_sdf = role_bench.join(resume_sdf, on="skill", how="left_anti")
    present_sdf = role_bench.join(resume_sdf, on="skill", how="inner")

    missing = [r["skill"] for r in missing_sdf.collect()]
    present = [r["skill"] for r in present_sdf.collect()]

    import builtins
    gap_score = builtins.round(
        len(missing) / max(len(missing) + len(present), 1) * 100, 2
    )

    if progress_cb:
        progress_cb(
            f"  Gap Score: {gap_score}% | "
            f"Have: {len(present)} | Missing: {len(missing)}"
        )

    return present, missing, gap_score


# Step 6: ALS recommendations for resume user
def get_als_recommendations(resume_skills, detected_role,
                             df_skills, als_model,
                             df_indexed, progress_cb=None):
    if progress_cb: progress_cb("Running ALS recommendations...")

    spark     = get_spark()
    resume_set = set(resume_skills)

    # Find similar users by Jaccard similarity using Spark
    role_users = df_skills \
        .filter(F.col("DevType") == detected_role) \
        .groupBy("ResponseId") \
        .agg(F.collect_list("skill").alias("skills_list"))

    # Collect and compute similarity in Python
    user_rows    = role_users.collect()
    similarities = []
    for row in user_rows:
        user_set  = set(row["skills_list"])
        union     = len(resume_set | user_set)
        intersect = len(resume_set & user_set)
        jaccard   = intersect / union if union > 0 else 0
        similarities.append((row["ResponseId"], jaccard, user_set))

    similarities.sort(key=lambda x: x[1], reverse=True)
    top_50 = similarities[:50]

    # Collect skills from similar users
    skill_weights = {}
    for _, sim, skills in top_50:
        for skill in skills:
            if skill not in resume_set:
                skill_weights[skill] = skill_weights.get(skill, 0) + sim

    cf_recs = sorted(skill_weights.items(), key=lambda x: x[1], reverse=True)
    cf_recs = [s for s, _ in cf_recs[:15]]

    if progress_cb:
        progress_cb(f"  {len(cf_recs)} CF-based recommendations")

    return cf_recs


# Full pipeline 
def run_full_pipeline(csv_paths_by_year, progress_cb=None):
    """
    Run complete Spark pipeline on survey CSVs.
    csv_paths_by_year: dict like {2023: "path", 2024: "path", 2025: "path"}
    Returns all computed artifacts.
    """
    spark = get_spark()

    # Load all years
    dfs = []
    for year, path in csv_paths_by_year.items():
        df = load_and_preprocess(path, year, progress_cb)
        dfs.append(df)

    # Union all years
    if progress_cb: progress_cb(" Combining all years...")
    df_all = dfs[0]
    for df in dfs[1:]:
        df_all = df_all.union(df)
    if progress_cb: progress_cb(f"  Combined: {df_all.count():,} rows")

    # Build benchmark
    benchmark_full, benchmark_skills = build_benchmark(
        df_all, threshold=30, progress_cb=progress_cb
    )

    # Train ALS
    als_model, df_indexed = train_als(df_all, progress_cb=progress_cb)

    # Compute gaps
    gap_df, role_gap = compute_skill_gaps(
        df_all, benchmark_skills, progress_cb=progress_cb
    )

    if progress_cb: progress_cb("Full pipeline complete!")

    return {
        "df_skills":        df_all,
        "benchmark_full":   benchmark_full,
        "benchmark_skills": benchmark_skills,
        "als_model":        als_model,
        "df_indexed":       df_indexed,
        "gap_df":           gap_df,
        "role_gap":         role_gap,
    }
