from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Transaction
from services import analytics_service as svc

bp = Blueprint("main", __name__)
CATEGORIES = {
    "expense": ["Food", "Transportation", "Shopping", "Education", "Entertainment",
                "Healthcare", "Rent", "Utilities", "Travel", "Other"],
    "income": ["Salary", "Freelancing", "Business", "Scholarship", "Investments", "Other"],
}

@bp.route("/")
@login_required
def dashboard():
    key = request.args.get("range", "this_month")
    try:
        start, end = svc.resolve_range(key, request.args.get("start"), request.args.get("end"))
    except ValueError as e:
        flash(str(e) if "Start" in str(e) else "Invalid date range; showing this month.", "warning")
        key = "this_month"
        start, end = svc.resolve_range(key)
    cats = svc.category_expenses(current_user.id, start, end)
    return render_template("dashboard.html", s=svc.summary(current_user.id, start, end), cats=cats,
                           recent=svc.recent_transactions(current_user.id, start, end),
                           top=cats[0] if cats else None, key=key, start=start, end=end)

def _validate(form):
    """Return (clean_dict, error_message)."""
    t = form.get("transaction_type", "")
    if t not in CATEGORIES:
        return None, "Choose income or expense."
    if form.get("category") not in CATEGORIES[t]:
        return None, "Choose a valid category."
    try:
        amount = Decimal(form.get("amount", "")).quantize(Decimal("0.01"))
        if amount <= 0:
            raise InvalidOperation
    except InvalidOperation:
        return None, "Amount must be a number greater than zero."
    try:
        d = datetime.strptime(form.get("transaction_date", ""), "%Y-%m-%d").date()
    except ValueError:
        return None, "Enter a valid date."
    return {"transaction_type": t, "amount": amount, "category": form["category"], "transaction_date": d,
            "description": form.get("description", "").strip()[:200],
            "payment_method": form.get("payment_method", "Cash")[:30]}, None

@bp.route("/transactions")
@login_required
def transactions():
    q = Transaction.query.filter_by(user_id=current_user.id)
    if request.args.get("q"):
        q = q.filter(Transaction.description.ilike(f"%{request.args['q']}%"))
    if request.args.get("category"):
        q = q.filter_by(category=request.args["category"])
    if request.args.get("type") in CATEGORIES:
        q = q.filter_by(transaction_type=request.args["type"])
    rows = q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()
    return render_template("transactions.html", rows=rows,
                           all_cats=sorted(set(CATEGORIES["expense"] + CATEGORIES["income"])))

@bp.route("/transactions/new", methods=["GET", "POST"])
@bp.route("/transactions/<int:tx_id>/edit", methods=["GET", "POST"])
@login_required
def transaction_form(tx_id=None):
    tx = None
    if tx_id:
        # 404 (not 403) for other users' records so their existence isn't revealed
        tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first() or abort(404)
    if request.method == "POST":
        data, err = _validate(request.form)
        if err:
            flash(err, "danger")
        else:
            tx = tx or Transaction(user_id=current_user.id)
            for k, v in data.items():
                setattr(tx, k, v)
            db.session.add(tx)
            db.session.commit()
            flash("Transaction saved.", "success")
            return redirect(url_for("main.transactions"))
    return render_template("transaction_form.html", tx=tx, cats=CATEGORIES)

@bp.route("/transactions/<int:tx_id>/delete", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first() or abort(404)
    db.session.delete(tx)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("main.transactions"))
