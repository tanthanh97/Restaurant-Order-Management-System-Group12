# Testing and GitHub evidence — Group12

## Manual test walkthrough

1. Start `python main.py` and set the first Manager password.
2. Login with a wrong password (expect an error), then the correct one.
3. Create staff users (Waiter, Kitchen, Cashier) in Users.
4. Add a dish and update its availability in Menu.
5. Select an Available table, create an order, add dishes, modify quantity and notes, and remove a Pending dish.
6. Check Kitchen for incoming dishes; advance each from Pending to Cooking to Ready.
7. In Checkout, select the order, choose Cash/Card/QR and enter a discount; confirm the receipt message.
8. Verify table is Available and Reports revenue increased.
9. Exit and reopen app; verify records persist.
10. Log in as each staff role; confirm navigation only displays permitted pages.

**Testing template:** Use the original `Testing Document Template (2).xlsx` from Elearning 5. Keep its five columns unchanged. Enter test cases and compare Expected Result with actual execution. This project does not claim that all manual cases have passed.

## GitHub evidence

1. Upload the project source to your repository using **Add file → Upload files**, or `git clone`, copy files, `git add .`, `git commit`, `git push`.
2. Never upload `restaurant.db`, credentials or private data.
3. Screenshot the Code tab showing source folders, README and commits.
4. Run `python -m pytest -v` and screenshot the terminal results.
5. Have each teammate accept a collaborator invitation and make **real** code contributions with their own account. Screenshot Commits, Pull Requests and Contributors after contributions appear.
6. Add screenshots and the real repository URL to the Stage 3 report.

## Suggested task split

- Lê Việt Quang — SQLite models, menu and tables
- Phan Tấn Thành — Tkinter GUI, order entry
- Nguyễn Văn Duy — login and kitchen workflow
- Lăng Minh Đức — payment, reports, tests and documentation

These are suggested assignments; commit history should reflect actual work performed.
