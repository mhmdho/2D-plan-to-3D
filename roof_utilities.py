import pyvista as pv
from pyvista import wrap
import numpy as np
from concave_hull import concave_hull, concave_hull_indexes
import vtkmodules.all as vtk
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_polyline


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


def get_outline(points, L_threshold=.5):

    idxes = concave_hull_indexes(
        points[:, :2],
        length_threshold=L_threshold
    )
    # you can get coordinates by `points[idxes]`
    assert np.all(points[idxes] == concave_hull(points, length_threshold=L_threshold))

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
        if abs(index - temp_index) > 1:  # Check if the point is not adjacent in the sequence
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
    
    # Iterate until we've gone through all points
    while len(remaining_points) > 0:
        last_point = sorted_points[-1]
        # Calculate distances from the last point to all remaining points
        distances = np.linalg.norm(remaining_points - last_point, axis=1)
        # Find the index of the closest point
        closest_point_idx = np.argmin(distances)
        # Add the closest point to the sorted list
        sorted_points.append(remaining_points[closest_point_idx])
        # Remove the closest point from the list of points to visit
        remaining_points = np.delete(remaining_points, closest_point_idx, axis=0)
    
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


def sort_neighbor_points_by_distance(points, num_neighbors=30):
    sorted_points = points.copy()

    def distance(point1, point2):
        return np.linalg.norm(np.array(point1) - np.array(point2))

    for i in range(len(sorted_points)):
        start = max(0, i - num_neighbors // 2)
        end = min(len(sorted_points), i + num_neighbors // 2)
        neighbors = sorted_points[start:end].tolist()

        sorted_neighbors = []
        current_origin = neighbors[0]
        while neighbors:
            nearest_point = min(neighbors, key=lambda p: distance(p, current_origin))
            sorted_neighbors.append(nearest_point)
            neighbors.remove(nearest_point)
            current_origin = nearest_point

        sorted_points[start:end] = sorted_neighbors

    return sorted_points


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
        dot_product = np.clip(dot_product, -1.0, 1.0)
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

        # If the angle is below the threshold, it is considered a corner
        if angle > angle_threshold:
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


def triangulate_volume_new(points):
    # Determine if the points lie in a plane or a cloud
    is_2d_surface = np.allclose(np.std(points[..., 2]), 0.0)

    # Convert the NumPy array to a VTK Points object
    vtk_points = vtk.vtkPoints()
    for pt in points.reshape(-1, 3):
        vtk_points.InsertNextPoint(pt)

    # Create a VTK PolyData object and set the points
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)

    # Triangulate the points using Delaunay triangulation
    delaunay = vtk.vtkDelaunay3D() if not is_2d_surface else vtk.vtkDelaunay2D()
    delaunay.SetInputData(polydata)
    delaunay.Update()

    # Get the output PolyData with triangulated polygons
    triangulated_result = delaunay.GetOutput()

    # Convert the VTK PolyData to a PyVista mesh
    mesh = pv.wrap(triangulated_result)
    return mesh


def get_all_lines(msp, Translation_Vector):

    all_lines = None

    # Function to process a line entity
    def add_lines(line, Translation_Vector):
        nonlocal all_lines
        line.translate(Translation_Vector, inplace=True)
        all_lines = line if all_lines is None else all_lines + line

    for entity in msp:

        if ('roof' in entity.dxf.layer.lower() or
            'gable' in entity.dxf.layer.lower() or
            'شیروانی' in entity.dxf.layer or
            'سقف' in entity.dxf.layer or 
            'wal' in entity.dxf.layer.lower() or
            'دیوار' in entity.dxf.layer or 
            'stair' in entity.dxf.layer.lower() or
            'پله' in entity.dxf.layer or
            'win' in entity.dxf.layer.lower() or
            'پنجره' in entity.dxf.layer):
                
            if entity.dxftype() == 'LINE':
                line = dxf_to_pyvista_line(entity)
                add_lines(line, Translation_Vector)

            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                lines = dxf_to_pyvista_polyline(entity)
                for line in lines:
                    add_lines(line, Translation_Vector)

    return all_lines


def extrude_as_gable(msp, max_height, Translation_Vector):

    all_lines = get_all_lines(msp, Translation_Vector)
    densified_points = interpolate_AllLines(all_lines,PPU=30)
    outline_points = get_outline(densified_points)
    outline_points = np.array(outline_points)
    outline_points = np.unique(outline_points, axis=0)
    outline_points = sort_points_by_distance(outline_points)
    outline_points3D = produce_gable_height(outline_points, max_height)

    ###################################################################
    # Find the indices of the two points with the maximum z-values and Sort
    max_z_indices = find_max_z_indices(outline_points3D)

    outline_points3D = np.roll(outline_points3D, -max_z_indices[1], axis=0)
    outline_points = np.roll(outline_points, -max_z_indices[1], axis=0)

    max_z_indices = find_max_z_indices(outline_points3D)

    # Split the list of points into two parts
    outline_points3D_1 = outline_points3D[:max_z_indices[0] + 1]
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

    points = np.array([outline_points3D[max_z_indices[0]], outline_points3D[max_z_indices[0]+1], 
                    outline_points3D[max_z_indices[1]-1], outline_points3D[max_z_indices[1]]])

    faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
    surface3D_3 = pv.PolyData(points, faces)

    surface3D = surface3D_1 + surface3D_2 + surface3D_3

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
