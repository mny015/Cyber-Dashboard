from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class RoleForm(FlaskForm):
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Update role")
