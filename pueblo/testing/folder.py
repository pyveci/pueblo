from pathlib import Path


def list_files(path: Path, pattern: str):
    """
    Enumerate all files in given directory.
    """
    files = path.glob(pattern)
    return [item.relative_to(path) for item in files]


def list_notebooks(path: Path, pattern: str = "*.ipynb"):
    """
    Enumerate all Jupyter Notebook files found in given directory.
    """
    return list_files(path, pattern)


def list_python_files(path: Path, pattern: str = "*.py"):
    """
    Enumerate all regular Python files found in given directory.
    """
    pyfiles = []
    for item in list_files(path, pattern):
        if item.name in ["conftest.py"] or item.name.startswith("test"):
            continue
        pyfiles.append(item)
    return pyfiles


def str_list(things):
    """
    Converge list to list of strings.
    """
    return list(map(str, things))
