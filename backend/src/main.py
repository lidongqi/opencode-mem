import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from api.routes import app


def main():
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
