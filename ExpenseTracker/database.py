"""
database.py - SQLite database operations for Expense Tracker
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

CATEGORIES = [
    "Food", "Travel", "Shopping", "Entertainment",
    "Health", "Education", "Utilities", "Rent", "Other"
]


def get_connection():
    """Return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like row access
    return conn


def initialize_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            created_at TEXT  DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            date        TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL DEFAULT 1,
            category TEXT    NOT NULL,
            amount   REAL    NOT NULL,
            month    TEXT    NOT NULL,
            UNIQUE(user_id, category, month),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Seed a default user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        import hashlib
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", pwd)
        )

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# EXPENSE CRUD
# ──────────────────────────────────────────────

def add_expense(date: str, amount: float, category: str,
                description: str, user_id: int = 1) -> int:
    """Insert a new expense. Returns the new row id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, date, amount, category, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, date, amount, category, description)
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_all_expenses(user_id: int = 1) -> list:
    """Return all expenses for a user, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_expense_by_id(expense_id: int, user_id: int = 1) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_expense(expense_id: int, date: str, amount: float,
                   category: str, description: str, user_id: int = 1):
    conn = get_connection()
    conn.execute(
        "UPDATE expenses SET date=?, amount=?, category=?, description=? "
        "WHERE id=? AND user_id=?",
        (date, amount, category, description, expense_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int, user_id: int = 1):
    conn = get_connection()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# SEARCH / FILTER
# ──────────────────────────────────────────────

def search_expenses(user_id: int = 1, date: str = None,
                    category: str = None, min_amt: float = None,
                    max_amt: float = None, keyword: str = None) -> list:
    """Flexible search across expenses."""
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params: list = [user_id]

    if date:
        query += " AND date = ?"
        params.append(date)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if min_amt is not None:
        query += " AND amount >= ?"
        params.append(min_amt)
    if max_amt is not None:
        query += " AND amount <= ?"
        params.append(max_amt)
    if keyword:
        query += " AND description LIKE ?"
        params.append(f"%{keyword}%")

    query += " ORDER BY date DESC, id DESC"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# SUMMARY / ANALYTICS
# ──────────────────────────────────────────────

def get_monthly_summary(year: int, month: int, user_id: int = 1) -> dict:
    """Return total and per-category totals for a given month."""
    month_str = f"{year}-{month:02d}"
    conn = get_connection()

    total_row = conn.execute(
        "SELECT SUM(amount) FROM expenses "
        "WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
        (user_id, month_str)
    ).fetchone()
    total = total_row[0] or 0.0

    cat_rows = conn.execute(
        "SELECT category, SUM(amount) as total "
        "FROM expenses "
        "WHERE user_id = ? AND strftime('%Y-%m', date) = ? "
        "GROUP BY category ORDER BY total DESC",
        (user_id, month_str)
    ).fetchall()
    # Get total budget for the month
    budget_row = conn.execute(
        "SELECT SUM(amount) FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month_str)
    ).fetchone()
    total_budget = budget_row[0] or 0.0

    conn.close()

    return {
        "total": total,
        "total_budget": total_budget,
        "by_category": {r["category"]: r["total"] for r in cat_rows},
        "month": month_str,
    }


def get_category_totals(user_id: int = 1, year: int = None,
                        month: int = None) -> dict:
    """Return category → total mapping, optionally filtered by month."""
    query = ("SELECT category, SUM(amount) as total FROM expenses "
             "WHERE user_id = ?")
    params: list = [user_id]
    if year and month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(f"{year}-{month:02d}")
    query += " GROUP BY category ORDER BY total DESC"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {r["category"]: r["total"] for r in rows}


def get_monthly_trend(user_id: int = 1, months: int = 6) -> list:
    """Return last N months of (month, total) tuples."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT strftime('%Y-%m', date) as month, SUM(amount) as total "
        "FROM expenses WHERE user_id = ? "
        "GROUP BY month ORDER BY month DESC LIMIT ?",
        (user_id, months)
    ).fetchall()
    conn.close()
    return [(r["month"], r["total"]) for r in reversed(rows)]


# ──────────────────────────────────────────────
# BUDGET
# ──────────────────────────────────────────────

def set_budget(category: str, amount: float,
               month: str = None, user_id: int = 1):
    """Upsert a budget for category + month."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    conn = get_connection()
    conn.execute(
        "INSERT INTO budgets (user_id, category, amount, month) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id, category, month) DO UPDATE SET amount=excluded.amount",
        (user_id, category, amount, month)
    )
    conn.commit()
    conn.close()


def get_budgets(month: str = None, user_id: int = 1) -> dict:
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, amount FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month)
    ).fetchall()
    conn.close()
    return {r["category"]: r["amount"] for r in rows}


def check_budget_alerts(user_id: int = 1, month: str = None) -> list:
    """Return list of (category, spent, budget, pct) where spent >= 80% of budget."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    budgets = get_budgets(month=month, user_id=user_id)
    totals = get_category_totals(user_id=user_id,
                                 year=int(month[:4]),
                                 month=int(month[5:]))
    alerts = []
    for cat, budget in budgets.items():
        spent = totals.get(cat, 0.0)
        pct = (spent / budget * 100) if budget > 0 else 0
        if pct >= 80:
            alerts.append({
                "category": cat,
                "spent": spent,
                "budget": budget,
                "pct": round(pct, 1),
            })
    return alerts


def get_past_months_budget_info(user_id: int) -> list:
    """Return budget and actual spending summary for all months with activity."""
    conn = get_connection()
    # Find all months from both budgets and expenses
    months_query = """
        SELECT DISTINCT month FROM budgets WHERE user_id = ?
        UNION
        SELECT DISTINCT strftime('%Y-%m', date) as month FROM expenses WHERE user_id = ?
        ORDER BY month DESC
    """
    rows = conn.execute(months_query, (user_id, user_id)).fetchall()
    
    now_str = datetime.now().strftime("%Y-%m")
    history = []
    for r in rows:
        month_str = r["month"]
        if not month_str or month_str > now_str:
            continue
            
        # Total budget for this month
        budget_row = conn.execute(
            "SELECT SUM(amount) FROM budgets WHERE user_id = ? AND month = ?",
            (user_id, month_str)
        ).fetchone()
        total_budget = budget_row[0] or 0.0
        
        # Total expenses for this month
        expense_row = conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, month_str)
        ).fetchone()
        total_spent = expense_row[0] or 0.0
        
        # Format month for display
        try:
            dt = datetime.strptime(month_str, "%Y-%m")
            display_month = dt.strftime("%B %Y")
        except ValueError:
            display_month = month_str
            
        history.append({
            "month": month_str,
            "display_month": display_month,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining": total_budget - total_spent,
            "pct": (total_spent / total_budget * 100) if total_budget > 0 else 0
        })
        
    conn.close()
    return history


# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

def verify_user(username: str, password: str) -> int | None:
    """Return user_id if credentials match, else None."""
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, pwd_hash)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def register_user(username: str, password: str) -> bool:
    """Create a new user. Returns False if username already exists."""
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, pwd_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
