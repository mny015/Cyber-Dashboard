from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from app.utils.validation import clean_text


class CategoryForm(FlaskForm):
    name = StringField(
        "Category name", filters=[clean_text], validators=[DataRequired(), Length(max=120)]
    )
    description = TextAreaField("Description", filters=[clean_text], validators=[Optional()])
    color = StringField(
        "Category color",
        default="#2563eb",
        filters=[clean_text],
        validators=[
            DataRequired(),
            Length(max=32),
            Regexp(r"^#[0-9a-fA-F]{6}$", message="Enter a six-digit hexadecimal color."),
        ],
    )
    submit = SubmitField("Save category")
