from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class RoleForm(FlaskForm):
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Update role")


class AdminPasswordResetForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), Length(min=12, max=128)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Change password")
