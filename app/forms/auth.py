from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from app.utils.validation import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class RegisterForm(FlaskForm):
    display_name = StringField(
        "Display name",
        validators=[
            DataRequired(message="Enter a display name."),
            Length(min=2, max=120, message="Use between 2 and 120 characters."),
        ],
    )
    email = EmailField(
        "Email address",
        validators=[DataRequired(message="Enter your email address."), Email(message="Enter a valid email address.")],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Enter a password."),
            Length(
                min=PASSWORD_MIN_LENGTH,
                max=PASSWORD_MAX_LENGTH,
                message=(
                    f"Use between {PASSWORD_MIN_LENGTH} and "
                    f"{PASSWORD_MAX_LENGTH} characters."
                ),
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = EmailField(
        "Email address",
        validators=[DataRequired(message="Enter your email address."), Email(message="Enter a valid email address.")],
    )
    password = PasswordField("Password", validators=[DataRequired(message="Enter your password.")])
    submit = SubmitField("Log in")


class MfaTokenForm(FlaskForm):
    token = StringField(
        "6-digit MFA code",
        validators=[
            DataRequired(message="Enter your MFA code."),
            Length(min=6, max=6, message="Enter the 6-digit code from your authenticator app."),
        ],
    )
    submit = SubmitField("Verify code")


class MfaSetupForm(FlaskForm):
    token = StringField(
        "6-digit MFA code",
        validators=[
            DataRequired(message="Enter your MFA code."),
            Length(min=6, max=6, message="Enter the 6-digit code from your authenticator app."),
        ],
    )
    submit = SubmitField("Enable MFA")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH),
        ],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="New passwords must match.")],
    )
    submit = SubmitField("Change password")


class ReconfirmationForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[Optional()])
    mfa_token = StringField(
        "6-digit MFA code",
        validators=[Optional(), Length(min=6, max=6, message="Enter a 6-digit MFA code.")],
    )
    submit = SubmitField("Confirm identity")

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators=extra_validators)
        if not self.current_password.data and not self.mfa_token.data:
            self.current_password.errors.append("Enter your password or current MFA code.")
            return False
        return valid
