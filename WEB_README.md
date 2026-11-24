# Group 12 — Maison POS (Web version)
Open this folder in VS Code. In Terminal run:

    python -m pip install -r requirements.txt
    python web_app.py

Open http://127.0.0.1:5000 in Chrome or Edge. First run creates a new local database; choose your own admin password (at least 8 characters), then sign in as admin. Alternatively double-click run_web.bat and open the same URL. Keep the terminal running; Ctrl+C stops it.

Workflow: Tables → Start order → Orders → Add dish → Kitchen → Mark Cooking → Mark Ready → Payment → Confirm payment. Menu, Staff and Reports are manager pages. Payments are local records only; no online payment gateway. The original Tkinter entry point main.py is retained. The database is not bundled. Do not commit restaurant.db or passwords.

Testing: `python -m pytest tests/ -v`. Nine original service tests passed in the build environment; four new Flask tests are included but could not be executed here because Flask was unavailable. Run them on your machine after installing requirements. Existing testing evidence applies only to the original service tests, not the new web interface. Update the design report and capture new evidence before submitting.
