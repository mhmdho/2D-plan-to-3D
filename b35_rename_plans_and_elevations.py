import os
import shutil


folder_path = 'decomposed'

files = ['22.dxf', '1212.dxf', '1313.dxf', '1414.dxf', '1515.dxf', '2121.dxf', '2222.dxf', '2323.dxf']
new_filenames = ['plan_roof.dxf', 'elevation_1front.dxf', 'elevation_4left.dxf', 'elevation_2back.dxf', 'elevation_3right.dxf', 'plan_2.dxf', 'plan_1.dxf', 'plan_0.dxf']


for i, filename in enumerate(files):

    # Old file path
    old_file = os.path.join(folder_path, filename)

    # New file path
    new_file = os.path.join(folder_path, new_filenames[i])

    # Copying and renaming the file
    shutil.copy(old_file, new_file)
    print(f"Copied and renamed {filename} to {new_filenames[i]}")
