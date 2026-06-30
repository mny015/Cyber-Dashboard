from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class RoleForm(FlaskForm):
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Update role")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[Optional(), Length(min=8, max=128)])
    submit = SubmitField("Reset password")
