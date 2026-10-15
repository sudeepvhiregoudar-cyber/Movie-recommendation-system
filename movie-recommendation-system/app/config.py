import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional at runtime
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movies.db")
if DATABASE_URL.startswith("postgres://"):  # some hosts still use the old scheme
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "60"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
AUTO_SEED = os.getenv("AUTO_SEED", "true").lower() == "true"
SAMPLE_CSV = os.getenv("MOVIES_CSV", os.path.join(os.path.dirname(__file__), "..", "data", "movies_sample.csv"))
