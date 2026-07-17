import os


class PackageManagerDetector:
    """
    Detects package managers used in a project.
    """

    @staticmethod
    def detect(extract_path):

        package_managers = set()

        for root, dirs, files in os.walk(extract_path):

            if "requirements.txt" in files:
                package_managers.add("pip")

            if "package-lock.json" in files:
                package_managers.add("npm")

            if "yarn.lock" in files:
                package_managers.add("Yarn")

            if "pnpm-lock.yaml" in files:
                package_managers.add("pnpm")

            if "pom.xml" in files:
                package_managers.add("Maven")

            if "build.gradle" in files or "build.gradle.kts" in files:
                package_managers.add("Gradle")

        return sorted(package_managers)
