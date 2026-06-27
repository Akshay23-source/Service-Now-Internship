from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class NoteForm(FlaskForm):
    """
    Form model used to create and edit smart notes.
    Includes built-in validation rules for titles and content.
    """
    title = StringField(
        'Note Title', 
        validators=[
            DataRequired(message='Please enter a title for your note.'),
            Length(max=150, message='Title cannot exceed 150 characters.')
        ]
    )
    
    content = TextAreaField(
        'Note Content',
        validators=[
            DataRequired(message='Note content cannot be empty.')
        ]
    )
    
    submit = SubmitField('Save Note')
