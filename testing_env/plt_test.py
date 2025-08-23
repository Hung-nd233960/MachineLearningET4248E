import pydicom
import matplotlib.pyplot as plt

import os

print(os.getcwd())

# Load a DICOM file
ds = pydicom.dcmread(f"{os.getcwd()}/testing_env/sample.dcm")

# Print metadata
print(ds)
# Access pixel array
image = ds.pixel_array
print(ds.pixel_array.shape)
# Display the image
plt.imshow(image, cmap=plt.cm.gray)
plt.axis("off")
plt.savefig("output.png")  # saves the figure
