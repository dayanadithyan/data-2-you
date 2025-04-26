import os

from sqlalchemy import create_engine
from langchain_experimental.sql import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain_huggingface import HuggingFaceHub, HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer

# 1. database setup (sqlite)
SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./dota.db")
engine = create_engine(SQLITE_URL, echo=False)

# 2. wrap in LangChain SQLDatabase
db = SQLDatabase(engine)

# 3. embeddings (optional for retrieval)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# 4. open-source LLM for SQL generation
llm = HuggingFaceHub(
    repo_id="google/flan-t5-small",
    model_kwargs={"temperature": 0.0, "max_length": 512},
)

# 5. build SQLDatabaseChain
db_chain = SQLDatabaseChain.from_llm(
    llm=llm,
    database=db,
    verbose=True
)
