from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    display_name = StringField("Display name", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class MfaTokenForm(FlaskForm):
    token = StringField("MFA code", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify code")


class MfaSetupForm(FlaskForm):
    token = StringField("MFA code", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Enable MFA")
