from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms.common import optional_int
from utils.helpers import clean_text
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES


def labeled_choices(values):
    return [(value, value.replace("_", " ").title()) for value in values]


class SecurityFindingForm(FlaskForm):
    title = StringField(
        "Title", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    activity_type = SelectField(
        "Activity type",
        choices=labeled_choices(ACTIVITY_TYPE_CHOICES),
        validators=[DataRequired()],
    )
    severity = SelectField(
        "Severity", choices=labeled_choices(SEVERITY_CHOICES), validators=[DataRequired()]
    )
    status = SelectField(
        "Status", choices=labeled_choices(FINDING_STATUS_CHOICES), validators=[DataRequired()]
    )
    vulnerability_id = SelectField(
        "Vulnerability tested or found",
        coerce=optional_int,
        validators=[Optional()],
        choices=[],
    )
    threat_id = SelectField(
        "Threat tactic managed",
        coerce=optional_int,
        validators=[Optional()],
        choices=[],
    )
    target = StringField(
        "Target or scope",
        filters=[clean_text],
        validators=[Optional(), Length(max=255)],
    )
    evidence = TextAreaField("Evidence", filters=[clean_text], validators=[Optional()])
    notes = TextAreaField("Notes", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Save finding")


class VulnerabilitySuggestionForm(FlaskForm):
    name = StringField(
        "Name", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    category = StringField(
        "Category",
        default="User submitted",
        filters=[clean_text],
        validators=[DataRequired(), Length(max=120)],
    )
    default_severity = SelectField(
        "Default severity", choices=labeled_choices(SEVERITY_CHOICES), validators=[DataRequired()]
    )
    description = TextAreaField("Notes", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Submit for review")


class AdminVulnerabilityForm(FlaskForm):
    code = StringField(
        "Code", filters=[clean_text], validators=[Optional(), Length(max=40)]
    )
    name = StringField(
        "Name", filters=[clean_text], validators=[DataRequired(), Length(max=200)]
    )
    category = StringField(
        "Category",
        default="Admin catalog",
        filters=[clean_text],
        validators=[DataRequired(), Length(max=120)],
    )
    default_severity = SelectField(
        "Default severity", choices=labeled_choices(SEVERITY_CHOICES), validators=[DataRequired()]
    )
    description = TextAreaField("Description", filters=[clean_text], validators=[Optional()])
    submit = SubmitField("Save to catalog")
