from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import func
from extensions import db
from models import Transaction

def resolve_range(key, start=None, end=None):
    """Turn a filter name into (start_date, end_date). Raises ValueError on bad custom ranges."""
    today = date.today()
    first = today.replace(day=1)
    if key == "last_month":
        end_d = first - timedelta(days=1)
        return end_d.replace(day=1), end_d
    if key == "last_3_months":
        s = (first - timedelta(days=1)).replace(day=1)
        s = (s - timedelta(days=1)).replace(day=1)
        return s, today
    if key == "this_year":
        return today.replace(month=1, day=1), today
    if key == "custom":
        s = datetime.strptime(start or "", "%Y-%m-%d").date()
        e = datetime.strptime(end or "", "%Y-%m-%d").date()
        if s > e:
            raise ValueError("Start date must be on or before end date.")
        return s, e
    return first, today  # default: this month

def summary(user_id, start, end):
    # Every query is filtered by user_id: this is what isolates each user's data.
    rows = (db.session.query(Transaction.transaction_type, func.coalesce(func.sum(Transaction.amount), 0), func.count())
            .filter(Transaction.user_id == user_id, Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end)
            .group_by(Transaction.transaction_type).all())
    totals = {"income": Decimal("0"), "expense": Decimal("0")}
    count = 0
    for t_type, total, n in rows:
        totals[t_type] = Decimal(str(total))
        count += n
    savings = totals["income"] - totals["expense"]
    rate = (savings / totals["income"] * 100).quantize(Decimal("0.1")) if totals["income"] > 0 else None
    days = (end - start).days + 1
    return {"income": totals["income"], "expense": totals["expense"], "savings": savings,
            "savings_rate": rate, "count": count,
            "avg_daily_spend": (totals["expense"] / days).quantize(Decimal("0.01"))}

def category_expenses(user_id, start, end):
    rows = (db.session.query(Transaction.category, func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.transaction_type == "expense",
                    Transaction.transaction_date >= start, Transaction.transaction_date <= end)
            .group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all())
    return [(c, float(a)) for c, a in rows]

def recent_transactions(user_id, start, end, limit=5):
    return (Transaction.query.filter(Transaction.user_id == user_id, Transaction.transaction_date >= start,
                                     Transaction.transaction_date <= end)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).limit(limit).all())
