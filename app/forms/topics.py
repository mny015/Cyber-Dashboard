from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms.common import optional_int
from app.utils.validation import clean_text


class TopicForm(FlaskForm):
    title = StringField(
        "Title", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    category_id = SelectField(
        "Category", coerce=optional_int, validators=[Optional()], choices=[]
    )
    status = SelectField(
        "Status",
        default="planned",
        choices=[
            ("planned", "Planned"),
            ("in-progress", "In Progress"),
            ("learning", "Learning"),
            ("practicing", "Practicing"),
            ("complete", "Complete"),
        ],
        validators=[DataRequired()],
    )
    priority = SelectField(
        "Priority",
        default="medium",
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", filters=[clean_text], validators=[Optional()])
    notes = TextAreaField("Notes", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Save topic")
