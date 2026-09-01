import sys
import os

# Configure UTF-8 for console output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("[*] Starting FaceMark Backend Server...")
    print("[*] API Documentation: http://localhost:8001/docs")
    print("[*] Frontend App:      http://localhost:8001/app")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
