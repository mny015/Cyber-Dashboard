from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms.common import optional_int
from app.utils.validation import clean_text


class NoteForm(FlaskForm):
    title = StringField(
        "Note title", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    topic_id = SelectField("Related topic (optional)", coerce=optional_int, validators=[Optional()], choices=[])
    body = TextAreaField("Note content", filters=[clean_text], validators=[DataRequired()])
    submit = SubmitField("Save note")
