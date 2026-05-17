# CareerLens
## A Scalable Big Data Platform for Developer Skill Gap Analysis and Career Intelligence

CareerLens is a scalable workforce intelligence platform that combines Apache Spark, MongoDB Atlas, Sentence-BERT, and collaborative filtering to analyze developer skill trends, benchmark workforce competencies, and generate personalized career upskilling recommendations. The platform integrates multi-year Stack Overflow Developer Survey datasets, live job market intelligence, and semantic resume analysis to provide adaptive, market-aligned career guidance.

## Key Features

- Distributed ETL pipeline using Apache Spark
- Multi-year workforce trend analytics (2021–2025)
- Skill prevalence and velocity computation
- Semantic resume intelligence using Sentence-BERT
- Collaborative filtering recommendations using Spark MLlib ALS
- Real-time job market analytics
- MongoDB-based workforce intelligence persistence
- Interactive Streamlit dashboard

# Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/CareerLens.git
cd CareerLens
```

---

## 2. Create Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure MongoDB Atlas

Create the following file:

```text
.streamlit/secrets.toml
```

Add your MongoDB connection string:

```toml
MONGO_URI = "your_mongodb_connection_string"
```

---

## 5. Run the Streamlit Application

```bash
streamlit run app.py
```

The application will launch at:

```text
http://localhost:8501
```
