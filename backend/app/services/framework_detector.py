import os


class FrameworkDetector:
    """
    Detects frameworks used in a project by recursively scanning
    configuration files.
    """

    @staticmethod
    def detect(extract_path):

        frameworks = set()

        for root, dirs, files in os.walk(extract_path):

            # -------------------------
            # package.json
            # -------------------------
            if "package.json" in files:

                frameworks.add("Node.js")

                package_json = os.path.join(root, "package.json")

                with open(
                    package_json,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:

                    content = file.read().lower()

                    if '"react"' in content:
                        frameworks.add("React")

            # -------------------------
            # requirements.txt
            # -------------------------
            if "requirements.txt" in files:

                requirements = os.path.join(root, "requirements.txt")

                with open(
                    requirements,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:

                    content = file.read().lower()

                    if "fastapi" in content:
                        frameworks.add("FastAPI")

                    if "flask" in content:
                        frameworks.add("Flask")

            # -------------------------
            # Django
            # -------------------------
            if "manage.py" in files:
                frameworks.add("Django")

            # -------------------------
            # Spring Boot
            # -------------------------
            if "pom.xml" in files:
                frameworks.add("Spring Boot")

        return sorted(frameworks)
