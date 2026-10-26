# tests/test_ingest.py
import pytest

from src.ingest import (
    CODE_EXTENSIONS,
    IGNORED_DIRS,
    MAX_FILE_BYTES,
    combine_files,
    detect_language_from_extension,
    from_folder,
    from_paste,
)


def _collect(root):
    return [p.replace('\\', '/') for p, _ in from_folder(str(root))]


def test_from_paste_returns_single_entry():
    assert from_paste("print('hi')") == [("paste_code", "print('hi')")]


def test_from_paste_accepts_custom_filename():
    assert from_paste("x = 1", filename="snippet.py") == [("snippet.py", "x = 1")]


def test_from_folder_collects_code_files_only(tmp_path):
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg' / 'core.py').write_text("print('hi')", encoding='utf-8')
    (tmp_path / 'notes.txt').write_text("not code", encoding='utf-8')
    assert _collect(tmp_path) == ['pkg/core.py']


def test_from_folder_skips_vendored_directories(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'app.py').write_text("x = 1", encoding='utf-8')
    for directory in ('venv', '__pycache__', '.git', 'node_modules', 'build'):
        path = tmp_path / directory
        path.mkdir()
        (path / 'junk.py').write_text("x = 1", encoding='utf-8')
    assert _collect(tmp_path) == ['src/app.py']


def test_from_folder_skips_oversized_files(tmp_path):
    (tmp_path / 'big.py').write_text('#' * (MAX_FILE_BYTES + 10), encoding='utf-8')
    (tmp_path / 'small.py').write_text('x = 1', encoding='utf-8')
    assert _collect(tmp_path) == ['small.py']


def test_from_folder_missing_directory_raises():
    with pytest.raises(FileNotFoundError):
        from_folder('definitely-not-a-real-folder')


def test_ignored_dirs_cover_common_vendored_paths():
    assert {'venv', '.venv', '__pycache__', 'node_modules'} <= IGNORED_DIRS


def test_combine_files_adds_path_headers():
    combined = combine_files([('a.py', 'x = 1'), ('b.py', 'y = 2')])
    assert '# File: a.py' in combined
    assert '# File: b.py' in combined


def test_detect_language_from_extension():
    assert detect_language_from_extension('main.py') == 'Python'
    assert detect_language_from_extension('weird.zzz') == 'Unknown'


def test_code_extensions_include_c_headers():
    assert {'.h', '.hpp'} <= CODE_EXTENSIONS
