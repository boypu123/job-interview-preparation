import PyPDF2
import docx

def extract_text(file_path):
    """
    Extracts text from PDF or Word (.docx) files.
    Returns a single string with all the text.
    """
    text = ""
    
    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX allowed.")
    
    return text