from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DecimalField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp, Optional
from app.models import User, Account, Transaction
from app.extensions import db
import sqlalchemy as sa

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
     #enter this later. phone_number = StringField
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        email = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if email:
            raise ValidationError('Please use a different email address.')

class VerificationForm(FlaskForm):
    code = StringField(
        "Verification Code",
        validators=[
            DataRequired(),
            Length(min=6, max=6),
            Regexp(r'^\d{6}$', message="Enter a 6-digit code")
        ]
    )
    submit = SubmitField("Verify")

class PhoneForm(FlaskForm):
    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Regexp(r'^\+?[0-9]{10,15}$',
                   message="Enter a valid phone number"),
            Length(min=10, max=15)
        ]
    )
    submit = SubmitField("Continue")

class MoneyForm(FlaskForm):
    account_type = SelectField(
        "Account Type",
        choices=[
            ("checking", "Checking"),
            ("savings", "Savings")
        ],
        validators=[DataRequired()]
    )
    amount = DecimalField(
        'Amount',
        places=2,  # show 2 decimals
        validators=[DataRequired()]
    )
    submit = SubmitField('Submit')


class TransferForm(FlaskForm):
    choice_field = SelectField(
        'Transfer between accounts or between users?',
        choices=[
            ('', ''),
            ('between_accounts', 'Between Accounts'),
            ('between_users', 'Between Users')
        ],
        validators=[DataRequired()]
    )
    user_field = StringField(
        'Which user would you like to transfer to?',
        validators=[Optional()]
    )

    request_type = SelectField(
        'Send or receive?',
        choices=[            
            ('', ''),
            ('send', 'Send'),
            ('receive', 'Receive')
        ],
        validators=[Optional()]
    )

    account1 = SelectField(
        'From...',
        choices=[
            ('', ''),
            ('checking', 'Checking Account'),
            ('savings', 'Savings Account')
        ],
        validators=[Optional()]
    )

    account2 = SelectField(
        'To...',
        choices=[
            ('', ''),
            ('checking', 'Checking Account'),
            ('savings', 'Savings Account')
        ],
        validators=[Optional()]

    )
    amount = DecimalField(
        'Enter the amount you would like to transfer',
        places=2,
        validators=[DataRequired()]
    )


    submit = SubmitField('Submit')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        if self.choice_field.data == "between_users":
            if not self.user_field.data:
                self.user_field.errors.append("User required")
                return False
            if not self.request_type.data:
                self.request_type.errors.append("Request type required")
                return False

        elif self.choice_field.data == "between_accounts":
            if not self.account1.data or not self.account2.data:
                self.account1.errors.append("Both accounts required")
                return False
            if self.account1.data == self.account2.data:
                self.account1.errors.append("You cannot send to the same account")
                return False

        if not self.amount.data:
            self.amount.errors.append("Amount required")
            return False

        return True




