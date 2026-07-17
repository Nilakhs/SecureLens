import os


class ProjectStatsDetector:
    """
    Counts files and folders in the project.
    """

    @staticmethod
    def detect(extract_path):

        file_count = 0
        folder_count = 0

        for root, dirs, files in os.walk(extract_path):
            folder_count += len(dirs)
            file_count += len(files)

        return {"file_count": file_count, "folder_count": folder_count}
