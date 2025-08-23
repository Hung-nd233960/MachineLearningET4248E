import os
import cv2
import numpy as np
import pandas as pd


def calculate_image_statistics(image_path):
    # Load the image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # If the image is not valid, skip it
    if img is None:
        return None

    # Calculate pixel statistics
    mean = np.mean(img)
    std = np.std(img)
    min_val = np.min(img)
    max_val = np.max(img)

    return {"mean": mean, "std": std, "min": min_val, "max": max_val}


def process_images_in_folder(folder_path):
    # Prepare a list to store the results
    results = []

    # Recursively search for all PNG files in the folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".png"):
                image_path = os.path.join(root, file)

                # Calculate statistics for each image
                stats = calculate_image_statistics(image_path)

                if stats:
                    # Store the results along with the image file path
                    results.append(
                        {
                            "image_path": image_path,
                            "mean": stats["mean"],
                            "std": stats["std"],
                            "min": stats["min"],
                            "max": stats["max"],
                        }
                    )

    # Create a DataFrame from the results
    df = pd.DataFrame(results)

    # Save the DataFrame to a CSV file
    output_csv = os.path.join(folder_path, "image_statistics.csv")
    df.to_csv(output_csv, index=False)

    print(f"Statistics saved to {output_csv}")


# Input folder path (change this to the folder you want to process)
folder_path = "archive"

# Process the images in the folder and save statistics to a CSV
process_images_in_folder(folder_path)
