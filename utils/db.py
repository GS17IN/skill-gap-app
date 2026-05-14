import streamlit as st
from pymongo import MongoClient
import certifi

@st.cache_resource
def get_db():
    uri    = st.secrets["MONGO_URI"]
    client = MongoClient(uri, tlsCAFile=certifi.where())
    return client["skill_gap_db"]