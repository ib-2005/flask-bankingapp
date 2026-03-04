from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, session
from flask_login import current_user, login_user, logout_user, login_required
from decimal import Decimal
from app.forms import LoginForm, RegistrationForm, MoneyForm, TransferForm, RequestResetForm, VerifyCodeForm, ResetPasswordForm
from app.models import User, Account, Transaction, Session, AccountType, VerificationCode, TransactionStatus, TransactionType, VerificationCodePurpose
from app.extensions import db
from app.email import password_email, generate_recovery_code
from app.services import start_password_reset, clear_password_reset, ensure_utc
from urllib.parse import urlsplit
import sqlalchemy as sa 
from flask_login import login_required
from datetime import datetime, timezone
import logging
import requests

bp = Blueprint("main", __name__)
logging.basicConfig(level=logging.DEBUG)

@bp.route('/')
def index():
    return render_template('base.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.Select(User).where(User.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        ip = request.remote_addr
        session = Session(ip=ip, user=current_user, )
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.home')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        accounts = [
                    Account(user=user, balance=Decimal('292.12'), account_type=AccountType.CHECKING),
                    Account(user=user, balance=Decimal('914.34'), account_type=AccountType.SAVINGS)
                    ]
        user.accounts = accounts
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        return redirect(url_for('main.home'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@bp.route('/home')
@login_required
def home():
    return render_template('home.html', title='home', user=current_user, accounts=current_user.accounts, AccountType=AccountType)

@bp.route('/add_money', methods=['GET', 'POST'])
@login_required
def add_money():
    form = MoneyForm()
    if form.validate_on_submit():
        print(form.account_type.data)
        user_account = db.session.scalar(
            sa.select(Account)
            .where(Account.user == current_user,
                    Account.account_type == AccountType(form.account_type.data)
            )
        )
        if not user_account:
            flash('Banking Account not found')
            return redirect(url_for('main.add_money'))
        user_account.balance += form.amount.data
        db.session.commit()
        flash(f'Successfully added {form.amount.data} to your {form.account_type.data} account')
    return render_template('add_money.html', form=form)

@bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()
    action = request.form.get('action')

    if action in ["accept", "decline", "cancel"]:
        transaction_id = request.form.get('transaction_id')

        if not transaction_id:
            flash("Missing transaction id")

        transaction = db.session.get(Transaction, int(transaction_id))

        if action == 'accept':
            if transaction.complete_transaction():
                flash('Transaction successfully completed')
            else:
                flash('Failed to complete transaction')

        if action == 'decline':
            transaction.cancel_transaction()
            flash('Transaction successfully declined')

        if action == 'cancel':
            transaction.cancel_transaction()
            flash('Transaction succesfully cancelled')

    if form.validate_on_submit():
        logging.debug("testingu1298123")
        if form.choice_field.data == "between_users":
            logging.debug('between_users')
            to_user = db.session.scalar(
                sa.select(User)
                .where(User.username == form.user_field.data)
            )
            if not to_user:
                flash('User not found')
                return redirect(url_for('main.transfer'))
            
            sending_account = db.session.scalar(
                sa.select(Account)
                .where(Account.user == current_user,
                    Account.account_type == AccountType.CHECKING
                )
            )

            receiving_account = db.session.scalar(
                sa.select(Account)
                .where(Account.user == to_user,
                    Account.account_type == AccountType.CHECKING
                )
            )

            transaction = Transaction(from_account=sending_account, 
                                      to_account=receiving_account, 
                                      transaction_type=TransactionType(form.request_type.data),
                                      status = TransactionStatus.PENDING,
                                      amount=form.amount.data)
            db.session.add(transaction)
            db.session.commit()

        if form.choice_field.data == "between_accounts":
            logging.debug('between_accounts')
            sending_account = db.session.scalar(
                sa.select(Account)
                .where(Account.user == current_user,
                    Account.account_type == AccountType(form.account1.data)
                )
            )
            logging.debug(sending_account)
            receiving_account = db.session.scalar(
                sa.select(Account)
                .where(Account.user == current_user,
                    Account.account_type == AccountType(form.account2.data)
                )
            )
            logging.debug(receiving_account)
            transaction = Transaction(from_account=sending_account, 
                                      to_account=receiving_account, 
                                      transaction_type=TransactionType.SEND,
                                      status = TransactionStatus.PENDING, 
                                      amount=form.amount.data)
            db.session.add(transaction)
            db.session.commit()

            if transaction.complete_transaction():
                flash(f'Successfully transferred ${transaction.amount}' )
            else:
                flash('Insufficient balance')
                
            return redirect(url_for('main.transfer'))

    return render_template('transfer.html', form=form, user=current_user, TransactionType=TransactionType, AccountType=AccountType)
    


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        abort(403)
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.Select(User)
            .where(User.email == form.email.data)
        )
        
        if not user:
            flash('Email not registered with an account')
            return redirect(url_for('main.forgot_password'))

        if user.get_active_code():
            flash('There is already an active verification code, please try again')
            return redirect(url_for('main.forgot_password'))
        
        recovery_code = generate_recovery_code()
        verification_code = VerificationCode(user=user, 
                                             purpose=VerificationCodePurpose.RESET_PASSWORD)
        verification_code.set_code_hash(recovery_code)
        db.session.add(verification_code)
        db.session.commit()
        start_password_reset(user, verification_code)
        session['user_id'] = int(user.id)
        password_email(session.get('current_email'), recovery_code)
        return redirect(url_for('main.verify_code'))
    
    return render_template('auth/forgot_password.html', form=form)

@bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    user = db.session.get(User, session.get('user_id'))
    verification_code = user.get_active_code()
    if not verification_code: 
        abort(403)
    form = VerifyCodeForm()
    if form.validate_on_submit():
        inputted_code = form.code.data

        if not verification_code.check_code(inputted_code):
            flash('The code does not match.')
            return redirect(url_for('main.verify_code'))
        if verification_code.used:
            flash('Verification code already used')
            return redirect(url_for('main.verify_code'))
        expires_at = ensure_utc(verification_code.expires_at)
        if datetime.now(timezone.utc) > expires_at:
            flash('Verification code expired!')
            return redirect(url_for())
        else:
            verification_code.used = True
            db.session.commit()
            session['is_resetting_password'] = True
            return redirect(url_for('main.reset_password'))
    return render_template('auth/verify_code.html', form=form)

@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    user = db.session.get(User, session.get('user_id'))
    if not session.get('is_resetting_password'):
        abort(403)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if user.check_password(form.new_password2.data):
            flash('New password cannot be the same as the old one,')
            return redirect(url_for('main.reset_password'))
        user.set_password(form.new_password2.data)
        db.session.commit()
        flash('Successfully changed password.')
        login_user(user)
        clear_password_reset()
        return redirect(url_for('main.home')) 

    return render_template('auth/reset_password.html', form=form)