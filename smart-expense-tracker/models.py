from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship("Transaction", backref="user", cascade="all, delete-orphan")

class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        db.CheckConstraint("amount > 0", name="ck_amount_positive"),
        db.Index("ix_tx_user_date", "user_id", "transaction_date"),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # "income" or "expense"
    amount = db.Column(db.Numeric(12, 2), nullable=False)        # Numeric avoids float rounding errors
    category = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(200), default="")
    transaction_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(30), default="Cash")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
