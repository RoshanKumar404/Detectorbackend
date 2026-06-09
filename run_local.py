import os
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("OSM_ROAD_CHECK_ENABLED", "false")

from run import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 1000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
