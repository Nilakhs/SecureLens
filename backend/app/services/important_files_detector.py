import os


class ImportantFilesDetector:
    """
    Detects important project files.
    """

    IMPORTANT_FILES = [
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
        ".env.example",
        "LICENSE",
        "requirements.txt",
        "package.json",
        "pom.xml",
        "setup.py",
        "pyproject.toml",
        "Makefile",
    ]

    @staticmethod
    def detect(extract_path):

        found_files = {}

        # Initialize all files as not found
        for filename in ImportantFilesDetector.IMPORTANT_FILES:
            found_files[filename] = False

        # Walk through the entire project
        for root, dirs, files in os.walk(extract_path):

            for file in files:

                if file in found_files:
                    found_files[file] = True

        return found_files
