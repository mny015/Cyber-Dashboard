from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.forms.common import optional_int
from app.utils.validation import clean_text


def valid_http_url(_form, field):
    parsed = urlparse(field.data or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Enter a valid HTTP or HTTPS lab URL.")


class LabForm(FlaskForm):
    name = StringField(
        "Lab name", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    platform_id = SelectField(
        "Platform", coerce=int, validators=[DataRequired()], choices=[]
    )
    url = StringField(
        "Lab URL",
        filters=[clean_text],
        validators=[DataRequired(), Length(max=255), valid_http_url],
    )
    topic_id = SelectField(
        "Related topic (optional)", coerce=optional_int, validators=[Optional()], choices=[]
    )
    visibility = SelectField(
        "Visibility", default="personal", validators=[DataRequired()], choices=[]
    )
    notes = TextAreaField("Notes", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Save lab")
