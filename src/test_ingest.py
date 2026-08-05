import sys
from pathlib import Path
from src.ingest import from_file, from_folder, from_github, combine_files, detect_language_from_extension

def test_single_file():
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def hello(): return 'world'")
        f.flush()
        files = from_file(f.name)
        print("Single file:", files)
        combined = combine_files(files)
        print("Combined:\n", combined)
    # File is now closed; safe to delete
    Path(f.name).unlink()

def test_folder():
    files = from_folder('.', extensions={'.py'})
    print(f"Found {len(files)} Python files in current folder.")
    if files:
        print("First file:", files[0])

def test_github():
    try:
        files = from_github("https://github.com/octocat/Hello-World.git")
        print(f"Cloned repo: {len(files)} files.")
        if files:
            print("First file:", files[0])
            lang = detect_language_from_extension(files[0][0])
            print("Detected language:", lang)
    except Exception as e:
        print("GitHub test failed (maybe network or rate limit):", e)

if __name__ == "__main__":
    print("=== Testing single file ===")
    test_single_file()
    print("\n=== Testing folder ===")
    test_folder()
    print("\n=== Testing GitHub ===")
    test_github()