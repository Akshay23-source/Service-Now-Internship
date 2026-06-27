import unittest
from datetime import datetime
from flask import url_for
from app import create_app, db
from app.models import User, Note, Quiz
from app.services.pdf_service import PDFService
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    GEMINI_MODEL = 'gemini-2.0-flash'

class SmartNotesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_unauthenticated_redirect(self):
        """Verify unauthenticated requests are redirected to login."""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

    def test_custom_error_handlers(self):
        """Verify that custom error pages render properly."""
        # Test 404 handler
        response = self.client.get('/nonexistent-page-url')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'404', response.data)
        self.assertIn(b'Page Not Found', response.data)

        # Test 400 handler
        with self.app.test_request_context():
            from werkzeug.exceptions import BadRequest
            response = self.app.handle_user_exception(BadRequest("Mock Bad Request"))
            self.assertEqual(response[1], 400)
            self.assertIn('400', response[0])
            self.assertIn('Session Expired or Bad Request', response[0])

    def test_pdf_safe_latin1_sanitization(self):
        """Verify safe_latin1 replaces smart quotes and special unicode chars."""
        unicode_str = "Smart quotes: “hello” and ‘world’. Dash: —. Bullet: •. Minus: −."
        sanitized = PDFService.safe_latin1(unicode_str)
        
        # Verify smart double/single quotes are replaced
        self.assertNotIn("“", sanitized)
        self.assertNotIn("”", sanitized)
        self.assertNotIn("‘", sanitized)
        self.assertNotIn("’", sanitized)
        self.assertIn('"hello"', sanitized)
        self.assertIn("'world'", sanitized)
        
        # Verify dash and bullet are replaced
        self.assertNotIn("—", sanitized)
        self.assertNotIn("•", sanitized)
        self.assertNotIn("−", sanitized)
        self.assertIn("-", sanitized)
        self.assertIn("*", sanitized)

    def test_pdf_generation_no_crash(self):
        """Verify that generate_note_pdf compiles note with unicode chars without crashing."""
        user = User(email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # Create a note containing smart quotes, em dashes, and complex characters
        note = Note(
            title="Unicode Smart Note “Chemistry”",
            content="Photosynthesis is a process used by plants—such as trees—to convert light energy.\nSmart quotes: “yes” and ‘no’.",
            summary="* Point 1: Uses light energy.\n* Point 2: Generates carbohydrates.",
            author=user
        )
        db.session.add(note)
        db.session.commit()

        # Add a practice quiz
        quiz_json = '[{"question": "What is the product of photosynthesis?", "options": ["Sugar", "Salt", "Iron", "Gold"], "correct": 0}]'
        quiz = Quiz(questions_json=quiz_json, note=note)
        db.session.add(quiz)
        db.session.commit()

        # Try exporting to PDF. This should NOT throw any UnicodeEncodeError.
        try:
            pdf_bytes = PDFService.generate_note_pdf(note)
            self.assertTrue(len(pdf_bytes) > 0)
            self.assertIsInstance(pdf_bytes, (bytes, bytearray))
        except UnicodeEncodeError as e:
            self.fail(f"PDF generation crashed due to encoding: {e}")
        except Exception as e:
            self.fail(f"PDF generation failed: {e}")

    def test_xss_protection_in_views(self):
        """Verify that user note content and summaries are escaped inside note detail view."""
        user = User(email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        note = Note(
            title="XSS Test Note",
            content="<script>alert('xss_content')</script>",
            summary="<script>alert('xss_summary')</script>",
            author=user
        )
        db.session.add(note)
        db.session.commit()

        # Log in the user
        with self.client:
            self.client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'password'
            })
            
            # View the note
            response = self.client.get(f'/note/{note.id}')
            self.assertEqual(response.status_code, 200)
            
            # The script tags MUST be escaped. E.g., &lt;script&gt; instead of <script>
            self.assertNotIn(b"<script>alert('xss_content')</script>", response.data)
            self.assertNotIn(b"<script>alert('xss_summary')</script>", response.data)
            self.assertIn(b"&lt;script&gt;alert(&#39;xss_content&#39;)&lt;/script&gt;", response.data)
            self.assertIn(b"&lt;script&gt;alert(&#39;xss_summary&#39;)&lt;/script&gt;", response.data)

    def test_mock_ai_fallback(self):
        """Verify that Mock AI fallback generates proper mock data when key is mock/empty."""
        from app.services.ai_service import AIService
        
        # Override config to use a mock key
        self.app.config['GEMINI_API_KEY'] = 'AQ.mockkey123'
        
        # We need a request context for flash() to access session
        with self.app.test_request_context():
            # Test mock summary
            summary = AIService.summarize("This is paragraph one.\nThis is paragraph two.")
            self.assertIn("- This is paragraph one.", summary)
            
            # Test mock title
            title = AIService.generate_title("lorem ipsum dolor sit amet")
            self.assertEqual(title, "Lorem Ipsum Dolor Sit")
            
            # Test mock quiz
            quiz_json = AIService.generate_quiz("Photosynthesis process carbohydrate molecule.")
            import json
            quiz_data = json.loads(quiz_json)
            self.assertEqual(len(quiz_data), 3)
            self.assertIn("question", quiz_data[0])
            self.assertIn("options", quiz_data[0])
            self.assertIn("correct", quiz_data[0])

if __name__ == '__main__':
    unittest.main()
