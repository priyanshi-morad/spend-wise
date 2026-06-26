"""
app.py - Flask web application for Expense Tracker
Run: python app.py
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
from datetime import datetime
import os, io, csv

import database as db

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_2026"

db.initialize_db()


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("welcome"))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    return session.get("user_id")


# ──────────────────────────────────────────────
# LANDING & AUTH
# ──────────────────────────────────────────────

@app.route("/")
def welcome():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = db.verify_user(request.form["username"],
                             request.form["password"])
        if uid:
            session["user_id"] = uid
            session["username"] = request.form["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        ok = db.register_user(request.form["username"],
                               request.form["password"])
        if ok:
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        flash("Username already taken.", "error")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("welcome"))


# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    uid = current_user()
    now = datetime.now()
    
    # Retrieve month from query parameters
    month = request.args.get("month", "").strip()
    if not month:
        month = now.strftime("%Y-%m")
        
    try:
        year, month_int = map(int, month.split("-"))
        if year > now.year or (year == now.year and month_int > now.month):
            year, month_int = now.year, now.month
            month = now.strftime("%Y-%m")
    except ValueError:
        year, month_int = now.year, now.month
        month = now.strftime("%Y-%m")

    summary = db.get_monthly_summary(year, month_int, uid)
    recent  = db.get_all_expenses(uid)[:5]
    alerts  = db.check_budget_alerts(uid, month)
    
    # Format month beautifully for display
    try:
        dt = datetime.strptime(month, "%Y-%m")
        display_month = dt.strftime("%B %Y")
    except ValueError:
        display_month = month

    current_month_str = now.strftime("%Y-%m")
    return render_template(
        "index.html",
        summary=summary,
        recent=recent,
        alerts=alerts,
        categories=db.CATEGORIES,
        username=session.get("username", "User"),
        now=now,
        month=month,
        current_month=current_month_str,
        display_month=display_month,
    )


# ──────────────────────────────────────────────
# ADD EXPENSE
# ──────────────────────────────────────────────

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid positive amount.", "error")
            return redirect(url_for("add"))

        # Validate date is not in the future
        submitted_date_str = request.form["date"]
        try:
            submitted_date = datetime.strptime(submitted_date_str, "%Y-%m-%d").date()
            if submitted_date > datetime.now().date():
                flash("Cannot add expenses for future dates.", "error")
                return redirect(url_for("add"))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("add"))

        db.add_expense(
            date=submitted_date_str,
            amount=amount,
            category=request.form["category"],
            description=request.form.get("description", ""),
            user_id=current_user(),
        )
        flash("Expense added successfully! 🎉", "success")
        return redirect(url_for("dashboard"))

    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("add.html", categories=db.CATEGORIES, today=today)


# ──────────────────────────────────────────────
# VIEW / SEARCH EXPENSES
# ──────────────────────────────────────────────

@app.route("/expenses")
@login_required
def expenses():
    uid = current_user()
    date     = request.args.get("date", "")
    category = request.args.get("category", "All")
    keyword  = request.args.get("keyword", "")
    min_amt  = request.args.get("min_amt", "")
    max_amt  = request.args.get("max_amt", "")

    results = db.search_expenses(
        user_id=uid,
        date=date or None,
        category=category if category != "All" else None,
        keyword=keyword or None,
        min_amt=float(min_amt) if min_amt else None,
        max_amt=float(max_amt) if max_amt else None,
    )
    total = sum(r["amount"] for r in results)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "expenses.html",
        expenses=results,
        total=total,
        categories=db.CATEGORIES,
        filters={"date": date, "category": category,
                 "keyword": keyword, "min_amt": min_amt,
                 "max_amt": max_amt},
        today=today,
    )


# ──────────────────────────────────────────────
# EDIT / DELETE
# ──────────────────────────────────────────────

@app.route("/edit/<int:eid>", methods=["GET", "POST"])
@login_required
def edit(eid):
    uid = current_user()
    expense = db.get_expense_by_id(eid, uid)
    if not expense:
        flash("Expense not found.", "error")
        return redirect(url_for("expenses"))

    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
        except ValueError:
            flash("Invalid amount.", "error")
            return redirect(url_for("edit", eid=eid))

        # Validate date is not in the future
        submitted_date_str = request.form["date"]
        try:
            submitted_date = datetime.strptime(submitted_date_str, "%Y-%m-%d").date()
            if submitted_date > datetime.now().date():
                flash("Cannot add expenses for future dates.", "error")
                return redirect(url_for("edit", eid=eid))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("edit", eid=eid))

        db.update_expense(
            expense_id=eid,
            date=submitted_date_str,
            amount=amount,
            category=request.form["category"],
            description=request.form.get("description", ""),
            user_id=uid,
        )
        flash("Expense updated.", "success")
        return redirect(url_for("expenses"))

    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("add.html", categories=db.CATEGORIES,
                           expense=expense, edit=True, today=today)


@app.route("/delete/<int:eid>", methods=["POST"])
@login_required
def delete(eid):
    db.delete_expense(eid, current_user())
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses"))


# ──────────────────────────────────────────────
# REPORTS
# ──────────────────────────────────────────────

@app.route("/reports")
@login_required
def reports():
    uid = current_user()
    now = datetime.now()
    
    month_param = request.args.get("month", "").strip()
    if "-" in month_param:
        try:
            year, month = map(int, month_param.split("-"))
            if year > now.year or (year == now.year and month > now.month):
                year, month = now.year, now.month
        except ValueError:
            year, month = now.year, now.month
    else:
        try:
            year = int(request.args.get("year", now.year))
            month = int(request.args.get("month", now.month))
            if year > now.year or (year == now.year and month > now.month):
                year, month = now.year, now.month
        except ValueError:
            year, month = now.year, now.month

    summary  = db.get_monthly_summary(year, month, uid)
    budgets  = db.get_budgets(f"{year}-{month:02d}", uid)
    cat_data = db.get_category_totals(uid, year, month)
    
    # Extra stats for reports
    expenses = db.get_all_expenses(uid)
    period_expenses = [e for e in expenses if e['date'].startswith(f"{year}-{month:02d}")]
    largest = max([e['amount'] for e in period_expenses]) if period_expenses else 0
    daily_avg = summary['total'] / 30 # Simple approximation

    months_list = [(y, m) for y in range(now.year - 2, now.year + 1)
                   for m in range(1, 13)
                   if not (y == now.year and m > now.month)]
                   
    spending_history = db.get_past_months_budget_info(uid)
    
    current_month_str = now.strftime("%Y-%m")
    return render_template(
        "reports.html",
        summary=summary,
        budgets=budgets,
        actuals=cat_data,
        year=year, month=month,
        months_list=months_list,
        datetime=datetime,
        largest=largest,
        daily_avg=daily_avg,
        spending_history=spending_history,
        current_month=current_month_str,
    )


# ──────────────────────────────────────────────
# BUDGET MANAGEMENT
# ──────────────────────────────────────────────

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    uid = current_user()
    now = datetime.now()
    
    # Retrieve month from query parameters or POST data
    month = request.args.get("month", "").strip()
    if not month and request.method == "POST":
        month = request.form.get("month", "").strip()
    if not month:
        month = now.strftime("%Y-%m")

    # Enforce no future months budget setting
    try:
        y, m = map(int, month.split("-"))
        if y > now.year or (y == now.year and m > now.month):
            flash("Cannot set or view budgets for future months.", "error")
            return redirect(url_for("budget"))
    except ValueError:
        pass

    if request.method == "POST":
        for cat in db.CATEGORIES:
            val = request.form.get(cat, "").strip()
            if val:
                try:
                    db.set_budget(cat, float(val), month, uid)
                except ValueError:
                    pass
        flash("Budgets saved.", "success")
        return redirect(url_for("budget", month=month))

    try:
        y, m = map(int, month.split("-"))
    except ValueError:
        y, m = now.year, now.month

    budgets = db.get_budgets(month, uid)
    actuals = db.get_category_totals(uid, y, m)
    alerts  = db.check_budget_alerts(uid, month)
    history = db.get_past_months_budget_info(uid)

    # Generate list of months for the selection dropdown
    selectable_months = set()
    selectable_months.add(now.strftime("%Y-%m"))
    
    # Add any historical months
    for h in history:
        selectable_months.add(h["month"])
        
    select_months_sorted = sorted(list(selectable_months), reverse=True)
    dropdown_months = []
    for sm in select_months_sorted:
        try:
            dt = datetime.strptime(sm, "%Y-%m")
            label = dt.strftime("%B %Y")
        except ValueError:
            label = sm
        dropdown_months.append({"value": sm, "label": label})

    selected_label = month
    for m in dropdown_months:
        if m["value"] == month:
            selected_label = m["label"]
            break

    current_month_str = now.strftime("%Y-%m")
    return render_template(
        "budget.html",
        categories=db.CATEGORIES,
        budgets=budgets,
        actuals=actuals,
        alerts=alerts,
        month=month,
        current_month=current_month_str,
        display_month=selected_label,
        history=history,
        dropdown_months=dropdown_months,
    )


# ──────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────

@app.route("/export/csv")
@login_required
def export_csv():
    expenses = db.get_all_expenses(current_user())
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "date", "amount", "category", "description", "created_at"]
    )
    writer.writeheader()
    for e in expenses:
        writer.writerow({
            "id":          e.get("id", ""),
            "date":        str(e.get("date", ""))[:10],          # YYYY-MM-DD only
            "amount":      f"{e.get('amount', 0):.2f}",          # 2 decimal places
            "category":    e.get("category", ""),
            "description": e.get("description", ""),
            "created_at":  str(e.get("created_at", ""))[:10],   # strip time part
        })

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
    )


# ──────────────────────────────────────────────
# API endpoints (for Chart.js)
# ──────────────────────────────────────────────

@app.route("/api/summary")
@login_required
def api_summary():
    uid = current_user()
    now = datetime.now()
    month_str = request.args.get("month", now.strftime("%Y-%m"))
    try:
        y, m = map(int, month_str.split("-"))
    except ValueError:
        y, m = now.year, now.month
    return jsonify(db.get_monthly_summary(y, m, uid))


@app.route("/api/charts/category")
@login_required
def api_chart_category():
    uid = current_user()
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    data = db.get_category_totals(uid, year, month)
    return jsonify(data)


@app.route("/api/charts/trend")
@login_required
def api_chart_trend():
    uid = current_user()
    months = request.args.get("months", 6, type=int)
    data = db.get_monthly_trend(uid, months)
    # Convert list of tuples to list of dicts for JS
    result = [{"month": m, "total": t} for m, t in data]
    return jsonify(result)


@app.route("/api/charts/budget")
@login_required
def api_chart_budget():
    uid = current_user()
    month_str = request.args.get("month", datetime.now().strftime("%Y-%m"))
    budgets = db.get_budgets(month_str, uid)
    actuals = db.get_category_totals(uid, int(month_str[:4]), int(month_str[5:]))
    
    cats = list(budgets.keys())
    return jsonify({
        "categories": cats,
        "budgets": [budgets[c] for c in cats],
        "actuals": [actuals.get(c, 0) for c in cats]
    })


if __name__ == "__main__":
    print("\n🚀 SpendWise Premium running at http://127.0.0.1:5000")
    print("   Default login → username: admin | password: admin123\n")
    app.run(debug=True)
