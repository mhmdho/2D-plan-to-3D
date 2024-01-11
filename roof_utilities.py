import pyvista as pv
import sys
from pyvista import wrap
import numpy as np
import vtkmodules.all as vtk
from concave_hull import concave_hull, concave_hull_indexes
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_polyline, dxf_to_pyvista_hatch


def entity_to_mesh(entity):

    mesh = pv.MultiBlock()
        
    if entity.dxftype() == 'LINE':
        mesh = dxf_to_pyvista_line(entity)
        
    elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
        lines = dxf_to_pyvista_polyline(entity)
        for line in lines:
            mesh.append(line)
                    
    elif entity.dxftype() == 'HATCH':
        all_hatch = dxf_to_pyvista_hatch(entity)
        for hatch in all_hatch:
            mesh.append(hatch)
            
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()
    
    return mesh


def get_all_lines(msp, translation_vector, layer_names):
    all_lines = None

    # Function to process a line entity
    for entity in msp:
        entity_layer = entity.dxf.layer.lower()

        # Check if entity layer matches any of the provided layer names
        if any(layer_name.lower() in entity_layer for layer_name in layer_names):
            line = entity_to_mesh(entity)
            line.translate(translation_vector, inplace=True)
            all_lines = line if all_lines is None else all_lines + line

    return all_lines


def create_PolyData_Line(vertices):
    outline_lines = pv.PolyData()
    for i in range(len(vertices) - 1):
        line = pv.Line(vertices[i], vertices[i+1])
        outline_lines += line

    line = pv.Line(vertices[-1], vertices[0])
    outline_lines += line
    return outline_lines


def interpolate_AllLines(all_lines,PPU=30):

    def interpolate_line_points(start, end, points_per_unit=PPU):
        # Calculate the distance between the start and end points
        distance = np.linalg.norm(np.array(end) - np.array(start))
        
        # Determine the total number of points needed based on the distance
        total_points = int(distance * points_per_unit/100)
        
        # Avoid division by zero by ensuring there is at least one point
        total_points = max(total_points, 1)
        
        # Combine x, y, and z points into a single array of coordinates
        return np.linspace(start, end, total_points)

    densified_points = []

    # Extract line indices, reshape, and exclude the first column (which just contains the value 2)
    line_indices = all_lines.lines.reshape(-1, 3)[:, 1:]

    for idx_pair in line_indices:
        start_point = all_lines.points[idx_pair[0]]
        end_point = all_lines.points[idx_pair[1]]
        
        interpolated_points = interpolate_line_points(start_point, end_point, PPU)
        
        # Append to the densified_points list
        densified_points.extend(interpolated_points)

    densified_points = np.array(densified_points)
    return densified_points


def get_outline(points, L_threshold=5, con=1):

    idxes = concave_hull_indexes(
        points[:, :2],
        concavity=con,
        length_threshold=L_threshold
    )
    # you can get coordinates by `points[idxes]`
    assert np.all(points[idxes] == concave_hull(points, concavity=con, length_threshold=L_threshold))

    outline_points = []
    for f, t in zip(idxes[:-1], idxes[1:]):  # noqa 
        outline_points.extend(points[[f, t]])

    return outline_points


def find_max_z_indices(outline_points3D):
    # Step 1: Find the index of the maximum z-value
    max_z_index = np.argmax(outline_points3D[:, 2])

    # Step 2: Sort the points by z-value in descending order, getting their indices
    sorted_indices = np.argsort(-outline_points3D[:, 2])

    # Initialize the second maximum index as None
    second_max_z_index = None

    # Step 3: Find the next highest point that is not adjacent to the previous points in the sequence
    temp_index = max_z_index
    for index in sorted_indices:
        # if abs(index - temp_index) > 1:  # Check if the point is not adjacent in the sequence
        if np.sqrt(np.sum((outline_points3D[index,:] - outline_points3D[temp_index,:]) ** 2)) > 20:  # Check if the point is not adjacent in the sequence
            second_max_z_index = index
            break
        temp_index = index  # Update temp_index to the current index

    # Handle the case where no non-adjacent second maximum is found
    if second_max_z_index is None:
        raise ValueError("A second non-sequential maximum z-value could not be found.")

    # Prepare the final array of indices
    max_z_indices = np.array([max_z_index, second_max_z_index])

    # Sort these two indices in descending order
    max_z_indices = np.sort(max_z_indices)[::-1]

    # Return the indices of the two non-adjacent maximum z-values
    return max_z_indices


def sort_points_by_distance(points):
    # Create a copy of the points to avoid modifying the original array
    remaining_points = points.copy()
    # This will hold the sorted points
    sorted_points = [remaining_points[0]]
    # Remove the first point from the remaining_points
    remaining_points = np.delete(remaining_points, 0, axis=0)
    
    old_distances = []
    unsorted_points = []
    # Iterate until we've gone through all points
    while len(remaining_points) > 0:
        last_point = sorted_points[-1]
        # Calculate distances from the last point to all remaining points
        distances = np.linalg.norm(remaining_points - last_point, axis=1)
        # Find the index of the closest point
        closest_point_idx = np.argmin(distances)
        # Add the closest point to the sorted list
        # print(np.mean(old_distances, axis=0))
        if len(old_distances) < 2 or distances[closest_point_idx] < 40 * np.mean(old_distances, axis=0):
            sorted_points.append(remaining_points[closest_point_idx])
            old_distances.append(distances[closest_point_idx])
        else:
            unsorted_points.append(remaining_points[closest_point_idx])
                           
        # Remove the closest point from the list of points to visit
        remaining_points = np.delete(remaining_points, closest_point_idx, axis=0)
    
    # Adding unsorted points instead of removing them
    for point in unsorted_points:
        distances = np.linalg.norm(sorted_points - point, axis=1)
        closest_points_idx = np.argsort(distances)[:2]  # Get indices of two nearest points

        # Determine the correct index to insert the unsorted point
        if abs(closest_points_idx[0] - closest_points_idx[1]) == 1:
            # If the closest points are adjacent, insert after the first closest point
            insert_idx = max(closest_points_idx) 
        else:
            # If not adjacent, insert after the closest point
            insert_idx = closest_points_idx[0]

        # Insert the point. Note: insert_idx + 1 because we want to insert after the closest point
        sorted_points = np.insert(sorted_points, insert_idx + 1, point, axis=0)

    return np.array(sorted_points)


def sort_points_by_polar_angle(points):
    # Calculate the centroid of the x and y coordinates only
    centroid = np.mean(points[:, :2], axis=0)

    # Function to calculate the angle between each point's x and y coordinates and the centroid
    def angle_with_centroid(point):
        return np.arctan2(point[1] - centroid[1], point[0] - centroid[0])

    # Sort the points by angle with centroid using only their x and y coordinates
    sorted_points = sorted(points, key=angle_with_centroid)

    return np.array(sorted_points)


def group_neighbors(points, gap_threshold=1):
    groups = []
    current_group = [points[0]]

    for i in range(1, len(points)):
        if points[i] - points[i-1] <= gap_threshold:
            current_group.append(points[i])
        else:
            groups.append(current_group)
            current_group = [points[i]]

    groups.append(current_group)  # Add the last group
    return groups


def find_sharp_edges(points, sharp_angle_threshold=10):
    
    def calculate_angle(p1, p2, p3):
        """
        Calculate the angle in degrees between the vectors (p2 - p1) and (p3 - p2).
        """
        v1 = p2 - p1
        v2 = p3 - p2
        dot_product = np.dot(v1, v2)
        norms_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        # Ensure the division is safe from floating-point errors.
        cos_theta = np.clip(dot_product / norms_product, -1, 1)
        angle_rad = np.arccos(cos_theta)
        angle_deg = np.degrees(angle_rad)
        return angle_deg

    # Calculate angles and detect sharp edges using modular arithmetic 
    sharp_points = []
    num_points = len(points)

    for i in range(num_points):
        prev_idx = (i - 1) % num_points  # Wraps to last point if i is 0
        next_idx = (i + 1) % num_points  # Wraps to first point if i is at the last index

        angle = calculate_angle(points[prev_idx], points[i], points[next_idx])

        if angle > 180 - sharp_angle_threshold:
            sharp_points.append(i)
    
    return sharp_points


def produce_gable_height(points, max_height):
    # Determine the center and width of the gable
    min_x = min(points, key=lambda p: p[0])[0]
    max_x = max(points, key=lambda p: p[0])[0]
    center_x = (min_x + max_x) / 2
    width = max_x - min_x

    # Calculate the angle required to achieve the maximum height
    angle = np.degrees(np.arctan(max_height / (width / 2)))

    # Copy points to avoid modifying the original data
    outline_points3D = points.copy()

    for point in outline_points3D:
        # Calculate the distance from the center
        distance_from_center = abs(point[0] - center_x)

        # Calculate the height adjustment based on the distance
        height_offset = np.tan(np.radians(angle)) * (width / 2) - np.tan(np.radians(angle)) * distance_from_center

        # Apply the height adjustment
        point[2] += height_offset

    return outline_points3D


def find_corner_points(points, angle_threshold=10):
    # Placeholder function to calculate the angle between three points
    def angle_between(p1, p2, p3):
        vec_p1p2 = p2 - p1
        vec_p2p3 = p3 - p2
        unit_vec_p1p2 = vec_p1p2 / np.linalg.norm(vec_p1p2)
        unit_vec_p2p3 = vec_p2p3 / np.linalg.norm(vec_p2p3)
        dot_product = np.dot(unit_vec_p1p2, unit_vec_p2p3)
        dot_product = np.clip(dot_product, -1.0, 1.0)  # Clip to prevent numerical errors
        angle = np.arccos(dot_product)
        return np.degrees(angle)

    # Initialize an empty list to hold the indices of corner points
    corner_indices = []

    # Loop over the points to calculate angles between consecutive triples
    for i in range(len(points)):
        # Consider points in a circular manner
        p1 = points[i - 1]  # Previous point
        p2 = points[i]      # Current point
        p3 = points[(i + 1) % len(points)]  # Next point

        # Calculate the angle at the current point
        angle = angle_between(p1, p2, p3)
        if  angle > angle_threshold:
            corner_indices.append(i)

    # Extract the corner points using the found indices
    corner_points = points[corner_indices]
    return corner_points


def produce_2Dsurface(Lines, height=None):
    # Create a new VTK PolyData object
    vtk_polydata = vtk.vtkPolyData()

    # Set the points
    vtk_points = vtk.vtkPoints()
    for point in Lines.points:
        vtk_points.InsertNextPoint(point)
    vtk_polydata.SetPoints(vtk_points)

    # Set the lines
    vtk_lines = vtk.vtkCellArray()
    # Assuming corner_lines.lines is a one-dimensional numpy array representing line connectivity
    cells = Lines.lines
    # The line connectivity is stored in the format: [n, p0, p1, n, p2, p3, ..., n, pk-1, pk]
    # where n is the number of points in the line segment (always 2 for a line) and p are the point indices
    i = 0
    while i < len(cells):
        n_points = cells[i]
        ids = cells[i + 1:i + 1 + n_points]
        vtk_line = vtk.vtkLine()
        for j in range(n_points):
            vtk_line.GetPointIds().SetId(j, ids[j])
        vtk_lines.InsertNextCell(vtk_line)
        i += 1 + n_points
    vtk_polydata.SetLines(vtk_lines)

    # Use vtkContourTriangulator to triangulate the line data
    triangulator = vtk.vtkContourTriangulator()
    triangulator.SetInputData(vtk_polydata)
    triangulator.Update()

    # Create a 3D volume
    if height is not None:
        # Create a vtkLinearExtrusionFilter to extrude the 2D profile
        extrude = vtk.vtkLinearExtrusionFilter()
        extrude.SetInputData(triangulator.GetOutput())
        extrude.SetExtrusionTypeToNormalExtrusion()
        extrude.SetVector(0, 0, height)  # Set the direction and length of extrusion
        extrude.Update()

        # Wrap the output VTK PolyData in a PyVista mesh
        volume = wrap(extrude.GetOutput())
        return volume
    else:
        # If no height is provided, just return the 2D surface
        surface = wrap(triangulator.GetOutput())
        return surface


def sort_outline(outline_points, sorting_algorithm='by_distance', resort_sharpness=False, remove_sharpness=True, sharp_angle_thr=25, extend_idx=30):
    
    if sorting_algorithm == 'by_distance':
        outline_points = sort_points_by_distance(outline_points)
    elif sorting_algorithm == 'by_angle':
        outline_points = sort_points_by_polar_angle(outline_points)
        
    sharp_points = find_sharp_edges(outline_points, sharp_angle_threshold = sharp_angle_thr)

    
    if resort_sharpness and len(sharp_points) > 0:
        
        sharp_groups= group_neighbors(sharp_points, gap_threshold=1)
    
        for group in sharp_groups:

            start_idx = max(group[0] - extend_idx, 0)  # Ensure start index is not less than 0
            end_idx = min(group[-1] + extend_idx, len(outline_points) - 1)  # Ensure end index is not more than the last index

            # Create an extended group of indices
            extended_group = list(range(start_idx, group[0])) + list(group) + list(range(group[-1] + 1, end_idx + 1))
            # Select and sort the points in the extended group
            extended_group_points = outline_points[extended_group]
            sorted_extended_group_points = sort_points_by_distance(extended_group_points)
            
            # Update the outline_points with the sorted extended group
            outline_points[extended_group] = sorted_extended_group_points

    all_sharp_points = list(sharp_points.copy())
    while remove_sharpness and len(sharp_points) > 0:
        outline_points = np.delete(outline_points, sharp_points, axis=0)
        sharp_points = find_sharp_edges(outline_points, sharp_angle_threshold = sharp_angle_thr)
        all_sharp_points.append(sharp_points)

    # print(f'number of total sharp points (more than {sharp_angle_thr} degrees): {len(all_sharp_points)}')
        
    return outline_points


def create_floor_surface(All_lines):
    
    if All_lines is None:
        sys.exit("Error: No lines to work on. Please modify Layer names")
    densified_points = interpolate_AllLines(All_lines,PPU=40)
    outline_points = get_outline(densified_points)
    outline_points = np.array(outline_points)
    outline_points = np.unique(outline_points, axis=0)
    outline_points = sort_outline(outline_points, sorting_algorithm='by_distance', resort_sharpness=False, remove_sharpness=True, sharp_angle_thr=10, extend_idx=30)
    outline_lines = create_PolyData_Line(outline_points)
    surface2D = produce_2Dsurface(outline_lines)
    
    return surface2D


def extrude_as_gable(msp, max_height, Translation_Vector):

    layer_names = ['roof', 'gable', 'شیروانی', 'سقف', 'wal', 'دیوار', 'stair', 'پله', 'balcon', 'بالکن', 'door', 'در', 'win', 'پنجره']
    all_lines = get_all_lines(msp, Translation_Vector, layer_names)

    if all_lines is None:
        sys.exit("Error: No lines to work on. Please modify Layer names")
        
    densified_points = interpolate_AllLines(all_lines,PPU=30)
    outline_points = get_outline(densified_points)
    outline_points = np.array(outline_points)
    outline_points = np.unique(outline_points, axis=0)
    outline_points = sort_outline(outline_points, sorting_algorithm='by_distance', resort_sharpness=False, remove_sharpness=True, sharp_angle_thr=10, extend_idx=30)
    outline_points3D = produce_gable_height(outline_points, max_height)

    ###################################################################
    # Find the indices of the two points with the maximum z-values and Sort
    max_z_indices = find_max_z_indices(outline_points3D)

    outline_points3D = np.roll(outline_points3D, -max_z_indices[1], axis=0)
    outline_points = np.roll(outline_points, -max_z_indices[1], axis=0)

    max_z_indices = find_max_z_indices(outline_points3D)

    # Split the list of points into two parts
    outline_points3D_1 = outline_points3D[max_z_indices[1] + 1 : max_z_indices[0]]
    outline_points3D_2 = outline_points3D[max_z_indices[0] + 1:]

    #####################################################################
    outline_lines = create_PolyData_Line(outline_points)
    outline_lines3D = create_PolyData_Line(outline_points3D)
    outline_lines3D_1 = create_PolyData_Line(outline_points3D_1)
    outline_lines3D_2 = create_PolyData_Line(outline_points3D_2)

    # Creating Outline Lines with corner_points instead of all outline_points
    corner_points = find_corner_points(outline_points, angle_threshold=10)  # Threshold angle in degrees
    corner_points3D = produce_gable_height(corner_points, max_height)

    corner_lines = create_PolyData_Line(corner_points)
    corner_lines3D = create_PolyData_Line(corner_points3D)

    ##################################################################
    surface2D = produce_2Dsurface(outline_lines)

    surface3D_1 = produce_2Dsurface(outline_lines3D_1)
    surface3D_2 = produce_2Dsurface(outline_lines3D_2)

    faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3

    temp_points = np.array([outline_points3D[max_z_indices[1]], outline_points3D[max_z_indices[1]+1], 
                    outline_points3D[max_z_indices[0]-1], outline_points3D[max_z_indices[0]]])
    surface3D_3 = pv.PolyData(temp_points, faces)

    temp_points = np.array([outline_points3D[max_z_indices[0]], outline_points3D[max_z_indices[0]+1], 
                    outline_points3D[max_z_indices[1]-1], outline_points3D[max_z_indices[1]]])
    surface3D_4 = pv.PolyData(temp_points, faces)

    surface3D = surface3D_1 + surface3D_2 + surface3D_3 + surface3D_4

    ##################################################################
    # plotting side surfaces of the gable

    side_surface = pv.MultiBlock()

    for i in range(len(outline_points) - 1):
        p1, p2, p3, p4 = outline_points[i], outline_points[i + 1], outline_points3D[i + 1], outline_points3D[i]
        points = np.array((p1, p2, p3, p4)).astype(np.float32)  # Explicitly cast to float32
        faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
        plane = pv.PolyData(points, faces)
        side_surface.append(plane)

    #plotting the last plane:
    p1, p2, p3, p4 = outline_points[-1], outline_points[0], outline_points3D[0], outline_points3D[-1]
    points = np.array((p1, p2, p3, p4)).astype(np.float32)  # Explicitly cast to float32
    faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
    plane = pv.PolyData(points, faces)
    side_surface.append(plane)

    Gable = pv.MultiBlock()
    Gable_Surface = [surface2D, surface3D, side_surface]
    for poly in Gable_Surface:
        Gable.append(poly)
    
    return Gable        
