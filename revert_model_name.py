import os


def replace_in_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if "gpt-4o-mini" in content:
            new_content = content.replace("gpt-4o-mini", "gpt-4.1-mini")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Replaced in {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")


for root, dirs, files in os.walk("."):
    # skip hidden/unwanted dirs
    dirs[:] = [
        d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules")
    ]
    for file in files:
        if file.endswith((".py", ".md")):
            replace_in_file(os.path.join(root, file))
