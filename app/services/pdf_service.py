from fpdf import FPDF

class NotePDF(FPDF):
    """
    Custom FPDF subclass implementing specialized headers and footers 
    representing study guides compiled by SmartNotes Pro.
    """
    def __init__(self, note_title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_title = note_title

    def header(self):
        # Header banner branding
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139) # Slate-500
        # Divide printable width of 180mm into two adjacent 90mm cells to align left/right perfectly
        self.cell(90, 5, "SmartNotes Pro - Revision & Study Guide Export", align="L")
        self.cell(90, 5, "Generated Study Resource", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        
        # Subtle horizontal separator line
        self.set_draw_color(226, 232, 240) # Slate-200
        self.set_line_width(0.2)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(8)

    def footer(self):
        # Bottom page margins
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184) # Slate-400
        
        # Branding footer. Divide printable width of 180mm into two adjacent 90mm cells
        self.cell(90, 10, "SmartNotes Pro © 2026", align="L")
        # Dynamic page numbers (nb replaced at render time by FPDF)
        self.cell(90, 10, f"Page {self.page_no()} of {{nb}}", align="R", new_x="LMARGIN", new_y="NEXT")


class PDFService:
    """
    Service layer providing logic for generating and formatting note PDF exports.
    """
    @staticmethod
    def safe_latin1(text):
        """
        Sanitizes text by replacing common non-Latin-1 Unicode characters (like smart quotes,
        special dashes, bullet points) with their standard Latin-1 equivalents to prevent
        FPDF encoding errors.
        """
        if not text:
            return ""
        
        # Dictionary of common smart punctuation and special characters
        replacements = {
            '\u201c': '"', '\u201d': '"',  # Smart double quotes
            '\u2018': "'", '\u2019': "'",  # Smart single quotes/apostrophes
            '\u2013': '-', '\u2014': '-',  # En/em dashes
            '\u2022': '*',                  # Bullet points
            '\u2212': '-',                  # Minus signs
        }
        
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
            
        # Encode with 'replace' to safely handle any other unmappable characters
        return text.encode('latin-1', 'replace').decode('latin-1')

    @staticmethod
    def generate_note_pdf(note):
        """
        Builds a professionally styled PDF document containing note body text,
        AI key summaries, and multiple choice revision worksheets.
        """
        # Page configuration: Portrait, Millimeters, A4 sheet size
        pdf = NotePDF(note_title=note.title, orientation="P", unit="mm", format="A4")
        pdf.set_margins(15, 20, 15)
        pdf.alias_nb_pages() # Setup dynamic total page count
        pdf.add_page()
        
        # Title Section
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(15, 23, 42) # Slate-900 (primary)
        pdf.multi_cell(0, 8, PDFService.safe_latin1(note.title))
        pdf.ln(2)
        
        # Metadata Section
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139) # Slate-500
        created_str = note.created_at.strftime('%b %d, %Y at %I:%M %p')
        pdf.cell(0, 5, f"Created: {created_str}", new_x="LMARGIN", new_y="NEXT")
        
        # Check if modified
        if note.created_at.strftime('%Y-%m-%d %H:%M') != note.updated_at.strftime('%Y-%m-%d %H:%M'):
            updated_str = note.updated_at.strftime('%b %d, %Y at %I:%M %p')
            pdf.cell(0, 5, f"Last Modified: {updated_str}", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(6)
        
        # Primary divider bar
        pdf.set_draw_color(99, 102, 241) # Branding Indigo
        pdf.set_line_width(0.6)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(8)
        
        # Note Body Section
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "Note Content", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(51, 65, 85) # Slate-700
        
        # Split text into paragraphs and write each cleanly
        paragraphs = note.content.split('\n')
        for p in paragraphs:
            p_text = p.strip()
            if p_text:
                pdf.multi_cell(0, 6, PDFService.safe_latin1(p_text))
                pdf.ln(3)
        
        # AI Summary Section (if generated)
        if note.summary:
            pdf.ln(4)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.3)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(6)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(99, 102, 241) # Indigo
            pdf.cell(0, 6, "AI Key Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(71, 85, 105) # Slate-600
            
            summary_bullets = note.summary.strip().split('\n')
            for bullet in summary_bullets:
                b_text = bullet.strip()
                if b_text:
                    pdf.multi_cell(0, 5.5, PDFService.safe_latin1(b_text))
                    pdf.ln(1)
            pdf.ln(4)
            
        # AI Practice Quiz Section (if generated)
        if note.quiz:
            import json
            try:
                questions = json.loads(note.quiz.questions_json)
            except Exception:
                questions = []
                
            if questions:
                pdf.ln(4)
                pdf.set_draw_color(226, 232, 240)
                pdf.set_line_width(0.3)
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(6)
                
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(99, 102, 241) # Indigo
                pdf.cell(0, 6, "AI Practice Worksheet", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(100, 116, 139) # Slate-500
                pdf.cell(0, 5, "Test your understanding of the concepts covered in this note.", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(4)
                
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 41, 59) # Slate-800
                
                for idx, q in enumerate(questions):
                    # Check if there is enough space on page for the question card (approx 35mm needed)
                    # get_y() + 35 > 280 (page limit height A4) means add a page break
                    if pdf.get_y() + 35 > 280:
                        pdf.add_page()
                        
                    pdf.set_font("Helvetica", "B", 10.5)
                    pdf.multi_cell(0, 5.5, PDFService.safe_latin1(f"Question {idx+1}: {q['question']}"))
                    pdf.ln(2)
                    
                    pdf.set_font("Helvetica", "", 10)
                    for o_idx, opt in enumerate(q['options']):
                        prefix = f"   [   ]  {['A', 'B', 'C', 'D'][o_idx]}.  "
                        pdf.multi_cell(0, 5.5, PDFService.safe_latin1(f"{prefix}{opt}"))
                        pdf.ln(1)
                    pdf.ln(4)
                    
        # Output the PDF compiled file content as bytearray
        return pdf.output()
