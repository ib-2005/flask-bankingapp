from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import Numeric, Enum
from app import db
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_required
from flask import flash, redirect, url_for
import enum


class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TransactionType(enum.Enum):
    SEND = "send"
    RECEIVE = "receive"

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    phone_number: so.Mapped[Optional[str]] = so.mapped_column(sa.String(15), index=True,
                                                    unique=True)
    sessions: so.WriteOnlyMapped[list['Session']] = so.relationship(
        back_populates='user'
    )
    accounts: so.Mapped[list['Account']] = so.relationship(
        back_populates='user'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    def __repr__(self) -> str:
        return '<User {}>'.format(self.username)
    

class Account(db.Model): #make it so that only checking accounts can send transactions
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user: so.Mapped['User'] = so.relationship(
        back_populates='accounts'
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    balance: so.Mapped[sa.Numeric] = so.mapped_column(sa.Numeric(12, 2),
                                                 nullable = False, 
                                                  default=0)
    account_type: so.Mapped[AccountType] = so.mapped_column(sa.Enum(AccountType))
    incoming_transactions: so.WriteOnlyMapped[list['Transaction']] = so.relationship(
        back_populates='to_account',
        foreign_keys='Transaction.to_account_id'
    )
    outgoing_transactions: so.WriteOnlyMapped[list['Transaction']] = so.relationship(
        back_populates='from_account',
        foreign_keys='Transaction.from_account_id'
    )


class Transaction(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    from_account_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Account.id), #see if you need to make str l8r
                                               index=True)
    to_account_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Account.id),
                                               index=True)
    from_account: so.Mapped['Account'] = so.relationship(
        back_populates='outgoing_transactions',
        foreign_keys=[from_account_id]
    )
    to_account: so.Mapped['Account'] = so.relationship(
        back_populates='incoming_transactions',
        foreign_keys=[to_account_id]
    )

    transaction_type: so.Mapped[TransactionType] = so.mapped_column(sa.Enum(TransactionType))
    amount: so.Mapped[Numeric] = so.mapped_column(Numeric(12, 2),
                                                  nullable = False)
    status: so.Mapped[TransactionStatus] = so.mapped_column(sa.Enum(TransactionStatus))
    time_initiated: so.Mapped[datetime] = so.mapped_column(index=True, 
                                                           default=lambda: datetime.now(timezone.utc))
    time_completed: so.Mapped[datetime] = so.mapped_column(index=True, 
                                                           default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Transaction {self.id}: {self.amount} ({self.transaction_type})>"
    
    def complete_transaction(self) -> bool: #returns true or false based on if the transaction passed or failed 
        if self.from_account.balance < self.amount:
            self.time_completed = datetime.now(timezone.utc)
            self.status = TransactionStatus.FAILED
            db.session.commit()
            return False
        else:
            self.from_account.balance -= self.amount
            self.to_account.balance += self.amount
            self.time_completed = datetime.now(timezone.utc)
            self.status = TransactionStatus.POSTED
            db.session.commit()
            return True

    def is_internal(self):
        return self.from_account.user_id == self.to_account.user_id



class Session(db.Model): 
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                index=True)
    user: so.Mapped[User] = so.relationship(
        back_populates='sessions'
    )
    
    ip: so.Mapped[str] = so.mapped_column(sa.String(45))
    starting_time: so.Mapped[datetime] = so.mapped_column(index=True, 
                                                           default=lambda: datetime.now(timezone.utc))
    ending_time: so.Mapped[datetime] = so.mapped_column(index=True, 
                                                           default=lambda: datetime.now(timezone.utc))

