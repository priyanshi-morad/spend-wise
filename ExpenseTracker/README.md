# 💸 SpendWise — Python Expense Tracker

A full-featured expense tracking web application built with **Python + Flask + SQLite + Matplotlib**.

---

## Features

| Feature | Description |
|---|---|
| ✅ Add/Edit/Delete Expenses | Full CRUD with date, amount, category, description |
| 🔍 Search & Filter | Filter by date, category, keyword, amount range |
| 📊 Charts | Pie, Bar, Trend, and Budget vs Actual charts |
| 📈 Monthly Reports | Category-wise summaries with visual breakdowns |
| 🎯 Budget Manager | Set limits per category with progress bars & alerts |
| ⬇️ Export CSV | Download all expenses as a spreadsheet |
| 🔐 User Auth | Login / Register with hashed passwords |

---

## Tech Stack

- **Backend** — Python 3.10+, Flask
- **Database** — SQLite (via `sqlite3` standard library)
- **Charts** — Matplotlib + NumPy
- **Frontend** — Jinja2 templates, vanilla CSS (dark mode UI)

---

## Project Structure

```
ExpenseTracker/
├── app.py          ← Flask routes / application entry point
├── database.py     ← All SQLite DB operations
├── charts.py       ← Matplotlib chart generators
├── requirements.txt
├── expenses.db     ← Created automatically on first run
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── index.html      ← Dashboard
│   ├── add.html        ← Add/Edit expense
│   ├── expenses.html   ← List + Search
│   ├── reports.html    ← Monthly reports
│   └── budget.html     ← Budget manager
│
└── static/
    ├── style.css
    └── charts/         ← Generated chart images (auto-created)
```

---

## Quick Start

### 1. Install Python 3.10 or higher
Download from https://python.org

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open your browser
Navigate to: **http://127.0.0.1:5000**



Or register a new account.

---

## Database Schema

```sql
-- Users (for login)
users (id, username, password, created_at)

-- Expenses (main table)
expenses (id, user_id, date, amount, category, description, created_at)

-- Budgets (per category per month)
budgets (id, user_id, category, amount, month)
```

---

## Categories
Food, Travel, Shopping, Entertainment, Health, Education, Utilities, Rent, Other

---

## Resume Description

> **Expense Tracker using Python & Flask**
> Developed a full-stack Python web application for tracking, categorizing and analyzing daily expenses. Features include SQLite database integration with complete CRUD operations, real-time budget alerts, monthly reports, and dynamic data visualizations (pie, bar, trend charts) using Matplotlib. Implemented user authentication with SHA-256 password hashing and CSV export functionality.

---

