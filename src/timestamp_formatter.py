
from markdown import Markdown
from io import StringIO

# Define a utility function to strip Markdown
def strip_markdown(text):
    """Converts Markdown to plain text."""
    md = Markdown()
    html = md.convert(text)
    return "".join(StringIO(html).read()).strip()

def strip_markdown(text):
    """Converts Markdown to plain text. Requires input to be a string."""
    if not isinstance(text, str):
        # Convert non-string input to a string (e.g., tuples, numbers)
        text = str(text)
    md = Markdown()
    html = md.convert(text)
    return "".join(StringIO(html).read()).strip()

class TimestampFormatter:
    @staticmethod
    def format(gentext):
        # Ensure input is a string before processing
        cp_text: str = strip_markdown(gentext)
        return cp_text