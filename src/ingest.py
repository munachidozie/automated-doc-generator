# src/ingest.py
import os
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional, Set
import git
import logging

logger = logging.getLogger(__name__)

# Supported code file extensions (add more as needed)
CODE_EXTENSIONS: Set[str] = {
    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', 
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', 
    '.cs', '.sh', '.pl', '.pm', '.lua', '.r', '.m', '.groovy',
    '.dart', '.jl', '.ex', '.exs'
}

def from_paste(code: str, filename: str = "paste_code") -> List[Tuple[str, str]]:
    """Return a list with one entry: (filename, code)."""
    return [(filename, code)]

def from_file(filepath: str) -> List[Tuple[str, str]]:
    """Read a single file and return list with (filename, content)."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return [(path.name, content)]

def from_folder(folderpath: str, extensions: Optional[Set[str]] = None) -> List[Tuple[str, str]]:
    """
    Walk a folder, collect all files with extensions in the set.
    Returns list of (relative_path, content).
    """
    if extensions is None:
        extensions = CODE_EXTENSIONS
    root = Path(folderpath)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {folderpath}")
    
    files = []
    for filepath in root.rglob('*'):
        if filepath.is_file() and filepath.suffix in extensions:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                relative = filepath.relative_to(root)
                files.append((str(relative), content))
            except Exception as e:
                logger.warning(f"Skipping file {filepath} (read error): {e}")
    return files

def from_github(url: str, branch: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Clone a GitHub repository to a temporary directory and process its code files.
    Returns list of (relative_path, content).
    """
    temp_dir = tempfile.mkdtemp(prefix="adoc_repo_")
    try:
        logger.info(f"Cloning {url} into {temp_dir}...")
        if branch:
            repo = git.Repo.clone_from(url, temp_dir, branch=branch)
        else:
            repo = git.Repo.clone_from(url, temp_dir)
        # Process the cloned folder
        files = from_folder(temp_dir)
        logger.info(f"Found {len(files)} code files in the repository.")
        return files
    except Exception as e:
        raise RuntimeError(f"Failed to clone or read repository: {e}")

def from_zip(zip_path: str) -> List[Tuple[str, str]]:
    """
    Extract a zip archive to a temporary folder and process its code files.
    """
    temp_dir = tempfile.mkdtemp(prefix="adoc_zip_")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        files = from_folder(temp_dir)
        return files
    except Exception as e:
        raise RuntimeError(f"Failed to extract or read zip: {e}")

def combine_files(files: List[Tuple[str, str]], separator: str = "\n\n") -> str:
    """
    Combine multiple file contents into one string, with file path headers.
    """
    combined = []
    for filename, content in files:
        combined.append(f"# File: {filename}\n{content}")
    return separator.join(combined)

def detect_language_from_extension(filename: str) -> str:
    """Return a human-readable language name from file extension."""
    ext = Path(filename).suffix.lower()
    mapping = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.cs': 'C#',
        '.sh': 'Shell',
        '.pl': 'Perl',
        '.pm': 'Perl Module',
        '.lua': 'Lua',
        '.r': 'R',
        '.m': 'Objective-C',
        '.groovy': 'Groovy',
        '.dart': 'Dart',
        '.jl': 'Julia',
        '.ex': 'Elixir',
        '.exs': 'Elixir Script'
    }
    return mapping.get(ext, 'Unknown')