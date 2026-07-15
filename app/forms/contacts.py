from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from app.utils.validation import clean_text, is_valid_phone


def valid_phone(_form, field):
    if not is_valid_phone(field.data):
        raise ValidationError("Enter a valid phone number.")


class ContactForm(FlaskForm):
    name = StringField(
        "Contact name", filters=[clean_text], validators=[DataRequired(), Length(max=120)]
    )
    email = EmailField(
        "Email address",
        filters=[clean_text],
        validators=[DataRequired(), Email(message="Enter a valid email address."), Length(max=255)],
    )
    phone = StringField(
        "Phone number", filters=[clean_text], validators=[DataRequired(), Length(max=40), valid_phone]
    )
    notes = TextAreaField("Contact notes", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Save contact")
