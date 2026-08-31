import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

required = ("DATABASE_URL", "API_SECRET_KEY", "S3_ACCESS_KEY", "S3_SECRET_KEY")
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise RuntimeError(
        "Missing required local environment variables: " + ", ".join(missing)
    )

os.environ.setdefault("S3_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("S3_BUCKET_NAME", "himma-audio")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENV", "development")

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
