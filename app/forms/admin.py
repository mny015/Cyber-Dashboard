from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from app.utils.validation import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class RoleForm(FlaskForm):
    role = SelectField("Account role", choices=[("user", "User"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Save role")


class AdminPasswordResetForm(FlaskForm):
    password = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Set new password")
