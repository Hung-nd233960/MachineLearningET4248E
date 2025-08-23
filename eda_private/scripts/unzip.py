import os
import zipfile


def unzip_and_clean(folder_path: str):
    """
    Unzip all .zip files in a folder, then delete the zips.

    Args:
        folder_path (str): Path to the folder containing .zip files.
    """
    for filename in os.listdir(folder_path):
        if filename.endswith(".zip"):
            zip_path = os.path.join(folder_path, filename)
            extract_folder = os.path.join(folder_path, filename[:-4])  # remove .zip

            # Create folder for extraction
            os.makedirs(extract_folder, exist_ok=True)

            # Extract contents
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_folder)
                print(f"✅ Extracted: {filename} → {extract_folder}")

            # Delete zip file
            os.remove(zip_path)
            print(f"🗑️ Deleted: {filename}")


if __name__ == "__main__":
    folder = "ct_data/"
    unzip_and_clean(folder)
