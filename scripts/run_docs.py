import os
import sys

# all scripts should be run from the repository root so we need to insert cwd to path
# to import docs
sys.path.insert(0, os.getcwd())

from docs.app import make_app

app = make_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )
