from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from utils.helpers import clean_text


class ScheduledTaskForm(FlaskForm):
    title = StringField(
        "Title", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    description = TextAreaField("Description", filters=[clean_text], validators=[Optional()])
    task_type = SelectField(
        "Type", default="general", validators=[DataRequired()], choices=[]
    )
    due_at = DateTimeLocalField(
        "Due date and time", format="%Y-%m-%dT%H:%M", validators=[Optional()]
    )
    scope = SelectField(
        "Scope", default="personal", validators=[DataRequired()], choices=[]
    )
    submit = SubmitField("Schedule task")
