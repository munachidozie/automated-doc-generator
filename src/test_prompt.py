from src.prompt import build_prompt
from src.ingest import from_folder, combine_files
from src.ai_client import generate_docs

def test_full_flow():
    # Use src folder as sample project (small)
    files = from_folder('src', extensions={'.py'})
    combined = combine_files(files)
    prompt = build_prompt(
        language="Python",
        project_name="Automated Documentation Generator",
        author="Your Name",
        version="0.1.0",
        context="A CLI tool that uses DeepSeek to generate documentation."
    )
    doc = generate_docs(prompt, combined)
    if doc:
        print(doc)
    else:
        print("Failed to generate docs.")

if __name__ == "__main__":
    test_full_flow()