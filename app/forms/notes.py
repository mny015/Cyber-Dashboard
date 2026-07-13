from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms.common import optional_int
from utils.helpers import clean_text


class NoteForm(FlaskForm):
    title = StringField(
        "Title", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    topic_id = SelectField("Topic", coerce=optional_int, validators=[Optional()], choices=[])
    body = TextAreaField("Note body", filters=[clean_text], validators=[DataRequired()])
    submit = SubmitField("Save note")
