# src/manual_test.py
from src.prompt import SYSTEM_PROMPT
from src.ai_client import generate_docs

sample_code = """
def multiply(a, b):
    \"\"\"Return the product of a and b.\"\"\"
    return a * b

class Calculator:
    def add(self, a, b):
        return a + b
"""

# Fill in the prompt placeholders (we'll build a proper formatter later)
prompt = SYSTEM_PROMPT.format(
    language="Python",
    project_name="MyCalculator",
    author="Unknown",
    version="1.0"
)

doc = generate_docs(prompt, sample_code)
print(doc)