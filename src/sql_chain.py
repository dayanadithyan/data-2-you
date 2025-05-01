import os
import logging

from sqlalchemy import create_engine
from langchain_experimental.sql import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# 1. database setup (sqlite)
SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./dota.db")
engine = create_engine(SQLITE_URL, echo=False)

# 2. wrap in LangChain SQLDatabase
db = SQLDatabase(engine)

# 3. embeddings (keeping the existing HuggingFace embeddings)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# 4. Claude LLM for SQL generation (replacing Hugging Face)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

llm = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    anthropic_api_key=ANTHROPIC_API_KEY,
    temperature=0.0,
    max_tokens=1024
)

# 5. build SQLDatabaseChain
db_chain = SQLDatabaseChain.from_llm(
    llm=llm,
    database=db,
    verbose=True
)