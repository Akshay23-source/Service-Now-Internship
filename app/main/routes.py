from flask import render_template, redirect, url_for, flash, abort, request, send_file
from flask_login import current_user, login_required
from app import db
from app.main import main_bp
from app.main.forms import NoteForm
from app.models import Note, Quiz
from app.services.ai_service import AIService
from app.services.pdf_service import PDFService
import io

@main_bp.route('/')
def index():
    """
    Root route index handler. 
    Redirects to dashboard if logged in, otherwise redirects to the sign-in portal.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    User workspace dashboard. 
    Loads notes belonging to the logged-in user, aggregates statistics, 
    supports keyword searches, and presents the home console view.
    """
    q = request.args.get('q', '').strip()
    
    # Base query for the current user's notes
    notes_query = current_user.notes
    
    # Apply filters if search string is active
    if q:
        search_filter = db.or_(
            Note.title.ilike(f"%{q}%"),
            Note.content.ilike(f"%{q}%")
        )
        notes_query = notes_query.filter(search_filter)
        
    user_notes = notes_query.order_by(Note.updated_at.desc()).all()
    
    # Calculate statistics based on the full list of user notes (not filtered results)
    all_notes = current_user.notes.all()
    total_notes = len(all_notes)
    
    # Calculate word count safely on all notes
    total_words = sum(len((note.content or '').split()) for note in all_notes)
    
    # Get last modified active date safely from the entire collection
    last_active = "No notes created"
    if all_notes:
        last_modified_note = current_user.notes.order_by(Note.updated_at.desc()).first()
        last_active = last_modified_note.updated_at.strftime('%B %d, %Y')

    # Aggregate AI statuses for dashboard indicators
    ai_summaries_count = sum(1 for note in all_notes if note.summary)
    quizzes_generated_count = sum(1 for note in all_notes if note.quiz is not None)

    return render_template(
        'dashboard.html',
        title='Dashboard',
        notes=user_notes,
        total_notes=total_notes,
        total_words=total_words,
        last_active=last_active,
        ai_summaries=ai_summaries_count,
        quizzes=quizzes_generated_count,
        search_query=q
    )

@main_bp.route('/note/new', methods=['GET', 'POST'])
@login_required
def create_note():
    """
    Renders note editor. If form is valid, creates a new note in the database
    linked to the current logged-in user.
    """
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(
            title=form.title.data.strip(),
            content=form.content.data,
            author=current_user
        )
        db.session.add(note)
        db.session.commit()
        flash('Note created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('note_form.html', title='New Note', form=form, legend='Create Note')

@main_bp.route('/note/<int:note_id>')
@login_required
def view_note(note_id):
    """
    Renders note details view. Prevents IDOR by verifying ownership.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    return render_template('note_detail.html', title=note.title, note=note)

@main_bp.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    """
    Pre-fills note form for editing. Saves updates if valid, preventing IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    form = NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data.strip()
        note.content = form.content.data
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('main.view_note', note_id=note.id))
    elif request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
        
    return render_template('note_form.html', title='Edit Note', form=form, legend='Edit Note', note=note)

@main_bp.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    """
    Deletes the requested note, preventing IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully.', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/note/<int:note_id>/summarize', methods=['POST'])
@login_required
def summarize_note(note_id):
    """
    Invokes AIService to generate a note summary. Prevents IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    # Generate summary using the AIService REST wrapper
    summary = AIService.summarize(note.content)
    
    if summary.startswith("Error") or summary.startswith("Gemini API Error") or summary.startswith("Connection Error"):
        flash(summary, 'danger')
    else:
        note.summary = summary
        db.session.commit()
        flash('AI Summary generated successfully!', 'success')
        
    return redirect(url_for('main.view_note', note_id=note.id))

@main_bp.route('/note/<int:note_id>/generate-title', methods=['POST'])
@login_required
def generate_title(note_id):
    """
    Invokes AIService to generate a short creative title for the note. Prevents IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    # Generate title using the AIService REST wrapper
    title = AIService.generate_title(note.content)
    
    if title.startswith("Error") or title.startswith("Gemini API Error") or title.startswith("Connection Error"):
        flash(title, 'danger')
    else:
        note.title = title
        db.session.commit()
        flash('AI Title generated successfully!', 'success')
        
    return redirect(url_for('main.view_note', note_id=note.id))

@main_bp.route('/note/<int:note_id>/quiz/generate', methods=['POST'])
@login_required
def generate_quiz(note_id):
    """
    Invokes AIService to generate a multiple choice quiz for the note. Prevents IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    # Generate quiz using the AIService REST wrapper
    quiz_data = AIService.generate_quiz(note.content)
    
    if quiz_data.startswith("Error") or quiz_data.startswith("Gemini API Error") or quiz_data.startswith("Connection Error"):
        flash(quiz_data, 'danger')
        return redirect(url_for('main.view_note', note_id=note.id))
    else:
        if note.quiz:
            note.quiz.questions_json = quiz_data
        else:
            quiz = Quiz(questions_json=quiz_data, note=note)
            db.session.add(quiz)
        db.session.commit()
        flash('AI Quiz generated successfully! Good luck!', 'success')
        return redirect(url_for('main.view_quiz', note_id=note.id))

@main_bp.route('/note/<int:note_id>/quiz', methods=['GET'])
@login_required
def view_quiz(note_id):
    """
    Renders quiz workspace for the note. Prevents IDOR.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    if not note.quiz:
        flash('No quiz has been generated for this note yet. Please generate one first!', 'warning')
        return redirect(url_for('main.view_note', note_id=note.id))
        
    import json
    try:
        questions = json.loads(note.quiz.questions_json)
    except Exception:
        questions = []
        flash('Error loading quiz questions. Please try generating the quiz again.', 'danger')
        
    return render_template('quiz.html', title=f"Quiz: {note.title}", note=note, questions=questions)

@main_bp.route('/note/<int:note_id>/export/pdf', methods=['GET'])
@login_required
def export_note_pdf(note_id):
    """
    Generates and downloads a study guide PDF for the requested note.
    Prevents IDOR by verifying note ownership.
    """
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
        
    try:
        # Generate the PDF file bytes
        pdf_data = PDFService.generate_note_pdf(note)
        
        # Wrap bytes in a memory stream
        mem_file = io.BytesIO(pdf_data)
        mem_file.seek(0)
        
        # Clean title for clean filename
        import re
        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', note.title).strip().replace(' ', '_')
        if not safe_title:
            safe_title = f"note_{note.id}"
            
        filename = f"{safe_title}_study_guide.pdf"
        
        return send_file(
            mem_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f"Error exporting PDF: {str(e)}", "danger")
        return redirect(url_for('main.view_note', note_id=note.id))

@main_bp.route('/ai-summarizer', methods=['GET'])
@login_required
def ai_summarizer():
    """
    Renders AI Summarizer console, listing notes with and without summaries.
    """
    notes = current_user.notes.order_by(Note.updated_at.desc()).all()
    notes_with_summary = [n for n in notes if n.summary]
    notes_without_summary = [n for n in notes if not n.summary]
    
    # Calculate counters for dashboard/sidebar metrics
    all_notes = current_user.notes.all()
    ai_summaries_count = sum(1 for note in all_notes if note.summary)
    quizzes_generated_count = sum(1 for note in all_notes if note.quiz is not None)
    
    return render_template(
        'ai_summarizer.html',
        title="AI Summarizer",
        notes_with_summary=notes_with_summary,
        notes_without_summary=notes_without_summary,
        ai_summaries=ai_summaries_count,
        quizzes=quizzes_generated_count
    )

@main_bp.route('/quizzes', methods=['GET'])
@login_required
def quizzes():
    """
    Renders AI Quiz console, listing notes with and without practice quizzes.
    """
    notes = current_user.notes.order_by(Note.updated_at.desc()).all()
    notes_with_quiz = [n for n in notes if n.quiz]
    notes_without_quiz = [n for n in notes if not n.quiz]
    
    all_notes = current_user.notes.all()
    ai_summaries_count = sum(1 for note in all_notes if note.summary)
    quizzes_generated_count = sum(1 for note in all_notes if note.quiz is not None)
    
    return render_template(
        'quizzes.html',
        title="Quiz Generator",
        notes_with_quiz=notes_with_quiz,
        notes_without_quiz=notes_without_quiz,
        ai_summaries=ai_summaries_count,
        quizzes=quizzes_generated_count
    )



