from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class NoteApprovalForm(FlaskForm):
    note_id = SelectField("Choose note to share", coerce=int, validators=[DataRequired()], choices=[])
    submit = SubmitField("Approve selected note")
