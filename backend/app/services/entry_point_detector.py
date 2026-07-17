import os


class EntryPointDetector:
    """
    Detects the most likely project entry point.
    """

    ENTRY_POINTS = [
        # Python
        "main.py",
        "app.py",
        "run.py",
        # React / Vite / CRA
        os.path.join("src", "main.jsx"),
        os.path.join("src", "main.js"),
        os.path.join("src", "main.tsx"),
        os.path.join("src", "index.js"),
        os.path.join("src", "index.jsx"),
        os.path.join("src", "index.tsx"),
        # Node.js
        "server.js",
        "app.js",
        "index.js",
        # Java
        "Main.java",
    ]

    @staticmethod
    def detect(extract_path):

        for root, dirs, files in os.walk(extract_path):

            for file in files:

                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, extract_path)

                normalized_path = os.path.normpath(relative_path)

                for candidate in EntryPointDetector.ENTRY_POINTS:

                    if normalized_path == os.path.normpath(candidate):
                        return relative_path

                    if file == candidate:
                        return relative_path

        return None
