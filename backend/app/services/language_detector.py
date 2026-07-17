import os


class LanguageDetector:
    """
    Detects programming languages based on file extensions.
    """

    EXTENSION_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".cs": "C#",
        ".go": "Go",
        ".php": "PHP",
        ".rb": "Ruby",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sql": "SQL",
        ".json": "JSON",
        ".xml": "XML",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".md": "Markdown",
        ".sh": "Shell",
        ".bat": "Batch",
        ".ps1": "PowerShell",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".rs": "Rust",
    }

    @staticmethod
    def detect(files):
        """
        Detect programming languages from a list of file paths.

        Args:
            files (list): List of project file paths.

        Returns:
            dict: Language counts.
        """

        languages = {}

        for file in files:
            _, extension = os.path.splitext(file)
            extension = extension.lower()

            if extension in LanguageDetector.EXTENSION_MAP:
                language = LanguageDetector.EXTENSION_MAP[extension]

                languages[language] = languages.get(language, 0) + 1

        return languages
