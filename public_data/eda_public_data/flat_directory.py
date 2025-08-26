import os
import shutil
import re

base_dir = "eda_public_data/data/"

# regex for matching folders like "CQ500CT*** CQ500CT***"
pattern = re.compile(r"^CQ500CT(\d+)\s+CQ500CT\1$")
print(os.listdir(base_dir))


def flat_qct_folders():
    for qct_folder in os.listdir(base_dir):
        qct_path = os.path.join(base_dir, qct_folder)
        if not os.path.isdir(qct_path):
            continue
        if not qct_folder.startswith("qct"):
            continue

        # look into each qct folder
        for inner_folder in os.listdir(qct_path):
            inner_path = os.path.join(qct_path, inner_folder)
            if not os.path.isdir(inner_path):
                continue

            m = pattern.match(inner_folder)
            if not m:
                print(f"Skipping unexpected folder: {inner_folder}")
                continue

            num = m.group(1)  # keep as-is, no padding
            new_name = f"CQ500-CT-{num}"
            new_path = os.path.join(base_dir, new_name)

            # move and rename
            print(f"Moving {inner_path} -> {new_path}")
            shutil.move(inner_path, new_path)

        # remove empty qct** folder
        try:
            os.rmdir(qct_path)
        except OSError:
            print(f"Could not remove {qct_path}, not empty?")


def flat_unknown_study_folders():
    for cq_folder in os.listdir(base_dir):
        cq_path = os.path.join(base_dir, cq_folder)
        if not os.path.isdir(cq_path):
            continue
        if not cq_folder.startswith("CQ500-CT-"):
            continue

        unknown_study_path = os.path.join(cq_path, "Unknown Study")
        if not os.path.isdir(unknown_study_path):
            print(f"No 'Unknown Study' in {cq_folder}, skipping.")
            continue

        # move all folders inside "Unknown Study" up one level
        for item in os.listdir(unknown_study_path):
            src_path = os.path.join(unknown_study_path, item)
            dst_path = os.path.join(cq_path, item)

            print(f"Moving {src_path} -> {dst_path}")
            shutil.move(src_path, dst_path)

        # remove the empty "Unknown Study" folder
        try:
            os.rmdir(unknown_study_path)
        except OSError:
            print(f"Could not remove {unknown_study_path}, not empty?")

        print("Done flattening 'Unknown Study' folders.")


def delete_bone_ct_folders():
    for cq_folder in os.listdir(base_dir):
        cq_path = os.path.join(base_dir, cq_folder)
        if not os.path.isdir(cq_path):
            continue
        if not cq_folder.startswith("CQ500-CT-"):
            continue

        for image_set in os.listdir(cq_path):
            image_set_path = os.path.join(cq_path, image_set)
            if not os.path.isdir(image_set_path):
                continue

            if "bone" in image_set.lower():
                print(f"Deleting {image_set_path}")
                shutil.rmtree(image_set_path)

    print("Done deleting 'bone' folders.")


if __name__ == "__main__":
    delete_bone_ct_folders()
