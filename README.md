# Restaurant Order Management System — Group12

A desktop restaurant order management application built with **Python 3**, **Tkinter**, **SQLite** and **MVC-style separation**.

## Group members

- Lê Việt Quang
- Phan Tấn Thành
- Nguyễn Văn Duy
- Lăng Minh Đức

## Features

- Manager setup, login and role-based navigation (Manager / Waiter / Kitchen / Cashier)
- Table status and order creation
- Menu management (add/edit/availability)
- Order item quantities, notes, removal while pending
- Kitchen tickets with Pending → Cooking → Ready status
- Cash, Card, QR payment recording; fixed-amount discount and receipt confirmation
- Paid-order revenue summary
- SQLite persistence, PBKDF2 password hashes, basic payment audit log

## Windows quick start

1. Install Python 3.11+ from python.org, including Tkinter.
2. Extract the project and open its folder in VS Code.
3. In Terminal, run `python main.py` (or `py main.py`).
4. On first launch, enter a password of at least 8 characters in the terminal. Login with username **admin** and your chosen password.
5. Use the **Users** tab to create Waiter, Kitchen and Cashier accounts.

SQLite data is created automatically in `restaurant.db`. It is intentionally excluded from GitHub.

## Tests

```bash
python -m pip install -r requirements.txt
python -m pytest -v
```

Tests use temporary SQLite databases and do not modify your application data.

## MVC structure

- `models/` — SQLite schema, business rules and password verification
- `controllers/` — app state and role permissions
- `views/` — Tkinter GUI
- `tests/` — pytest service tests

## Scope and limitations

This is a local desktop educational prototype, **not** a deployed multi-terminal restaurant system. It does not provide real-time network kitchen notifications, live stock tracking, payment gateway integration, printing, VAT computation, or offline network synchronization. The `Card` and `QR` choices record a manually confirmed payment, not a real payment authorization. Database updates are transactional locally; concurrent multi-device support and the performance requirements in the specification are not yet validated. The UI should be manually tested on the target Windows machine.

See `docs/TESTING_AND_GITHUB.md` for the manual test checklist and GitHub evidence instructions.
