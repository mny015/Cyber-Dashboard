from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import EmailField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.utils.uploads import ProfileImageUploadValidator


class ProfileForm(FlaskForm):
    display_name = StringField("Display name", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    profile_bio = TextAreaField("Profile details", validators=[Optional(), Length(max=1000)])
    profile_image = FileField(
        "Profile picture",
        validators=[ProfileImageUploadValidator()],
    )
    submit = SubmitField("Update profile")
