"""Entry point to start the playground server."""

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "src.playground.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
