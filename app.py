import re
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import requests
from bs4 import BeautifulSoup
from docx import Document

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# DFA class for searching the pattern
class DFA:
    def __init__(self, pattern):
        self.pattern = self.preprocess_text(pattern)  # Preprocess pattern
        self.m = len(self.pattern)
        self.dfa = {}
        self.build_dfa()

    @staticmethod
    def preprocess_text(text):
        """Normalize text for better sentence and pattern matching."""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces into one
        return text

    def build_dfa(self):
        self.dfa[0] = {}
        self.dfa[0][self.pattern[0]] = 1
        x = 0

        for j in range(1, self.m):
            if j not in self.dfa:
                self.dfa[j] = {}
            for char in self.dfa[x]:
                self.dfa[j][char] = self.dfa[x][char]
            self.dfa[j][self.pattern[j]] = j + 1
            x = self.dfa[x].get(self.pattern[j], 0)

    def search(self, text):
        text = self.preprocess_text(text)  # Preprocess text
        n = len(text)
        j = 0
        for i in range(n):
            j = self.dfa.get(j, {}).get(text[i], 0)
            if j == self.m:
                return i - self.m + 1
        return -1

def read_text_from_file(file_path):
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    else:
        raise ValueError("Unsupported file type")

def get_context(text, index, pattern):
    # Get a window of text around the match
    window_size = 100  # characters before and after
    start = max(0, index - window_size)
    end = min(len(text), index + len(pattern) + window_size)
    
    # Get the text snippet
    context = text[start:end]
    
    # Add ellipsis if we're not at the start/end
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
    
    # Highlight the matched pattern
    match_start = index - start if start > 0 else index
    context = (
        context[:match_start] +
        f"<mark>{context[match_start:match_start+len(pattern)]}</mark>" +
        context[match_start+len(pattern):]
    )
    
    return context

def highlight_pattern(text, pattern):
    escaped_pattern = re.escape(pattern)
    return re.sub(escaped_pattern, lambda match: f"<mark>{match.group(0)}</mark>", text, flags=re.IGNORECASE)

def fetch_text_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['nav', 'header', 'footer', 'sidebar', 'aside']):
            element.decompose()
            
        # Try to find main content area
        main_content = None
        content_priorities = [
            soup.find('main'),
            soup.find('article'),
            soup.find(id=['content', 'main-content', 'main', 'article']),
            soup.find(class_=['content', 'main-content', 'article-content', 'post-content']),
            soup.find('div', {'role': 'main'}),
        ]
        
        # Use the first found content area
        for content in content_priorities:
            if content:
                main_content = content
                break
        
        # If no specific content area found, fall back to body
        if not main_content:
            main_content = soup.find('body')
            
        if main_content:
            # Clean the text
            text = main_content.get_text(separator=' ', strip=True)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        return ""
    else:
        raise ValueError(f"Failed to fetch the URL: {url}. Status code: {response.status_code}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        url = request.form.get('url')
        text_area = request.form.get('textarea')
        pattern = request.form['pattern']
        document_text = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            document_text = read_text_from_file(file_path)

        elif url:
            document_text = fetch_text_from_url(url)

        elif text_area:
            document_text = text_area

        if not document_text:
            return redirect(request.url)

        document_text = DFA.preprocess_text(document_text)  # Normalize text
        dfa = DFA(pattern)
        result = dfa.search(document_text)

        if result != -1:
            context = get_context(document_text, result, pattern)
            highlighted_text = highlight_pattern(document_text, pattern)
            return render_template('result.html', highlighted_text=highlighted_text, context=context, found=True, document_text=document_text, url=url)
        else:
            return render_template('result.html', context=None, found=False, document_text=document_text, url=url)

    return render_template('upload.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)