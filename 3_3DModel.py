import ezdxf
import numpy as np
import pyvista as pv

def read_and_extract_lines_from_doc(filepath):
    """Read file and extract lines from it."""
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    return [e for e in msp if e.dxftype() == 'LINE']

def convert_walls_to_points_and_lines(walls):
    """Convert wall data to points and lines."""
    points = []
    lines = []
    for wall in walls:
        start = [wall.dxf.start.x, wall.dxf.start.y, 0]
        end = [wall.dxf.end.x, wall.dxf.end.y, 0]
        points.extend([start, end])
        lines.append([2, len(points)-2, len(points)-1])
    return np.array(points), np.array(lines)

def adjust_coordinates(points, center_x1, center_y1, height_adjustment=0):
    """Adjust coordinates of points."""
    points[:, 0] -= np.mean(points[:, 0]) - center_x1
    points[:, 1] -= np.mean(points[:, 1]) - center_y1
    points[:, 2] += height_adjustment

def plot_2D(points, lines, plotter, color='blue', line_width=5):
    """Plot points and lines in 2D."""
    grid = pv.PolyData(points, lines=lines)
    plotter.add_mesh(grid, color=color, line_width=line_width)

def extrude_lines(polydata, height, points):
    """Extrude the 2D lines to make them 3D."""
    faces = np.hstack([[2, i, i+1] for i in range(0, len(points), 2)])
    mesh_2d = pv.PolyData(points, faces)
    return mesh_2d.extrude([0, 0, height])

def add_floor_and_ceiling_from_points(plotter, points, height):
    """Add floor and ceiling planes based on wall points to the plotter."""
    hull = pv.PolyData(points).delaunay_2d()
    ceiling = hull.copy()
    ceiling.points[:, 2] += height
    plotter.add_mesh(hull, color='lightgray', opacity=0.9)

WallHeight = 400
walls1 = read_and_extract_lines_from_doc("decomposed/cluster_3.dxf")
walls2 = read_and_extract_lines_from_doc("decomposed/cluster_9.dxf")
walls3 = read_and_extract_lines_from_doc("decomposed/cluster_8.dxf")

points1, lines1 = convert_walls_to_points_and_lines(walls1)
points2, lines2 = convert_walls_to_points_and_lines(walls2)
points3, lines3 = convert_walls_to_points_and_lines(walls3)

center_x1 = np.mean(points1[:, 0])
center_y1 = np.mean(points1[:, 1])
adjust_coordinates(points2, center_x1, center_y1, WallHeight)
adjust_coordinates(points3, center_x1, center_y1, 2*WallHeight)

plotter_2d = pv.Plotter()
plot_2D(points1, lines1, plotter_2d)
plot_2D(points2, lines2, plotter_2d)
plotter_2d.show_grid()
plotter_2d.show()

walls1_3d = extrude_lines(points1, WallHeight, points1)
walls2_3d = extrude_lines(points2, WallHeight, points2)
walls3_3d = extrude_lines(points3, WallHeight/2, points3)

plotter_3d = pv.Plotter()
plotter_3d.add_mesh(walls1_3d, color='lightgray', opacity=1)
plotter_3d.add_mesh(walls2_3d, color='darkgray', opacity=1)
plotter_3d.add_mesh(walls3_3d, color='darkgray', opacity=1)
add_floor_and_ceiling_from_points(plotter_3d, points1, WallHeight)
add_floor_and_ceiling_from_points(plotter_3d, points2, WallHeight)
add_floor_and_ceiling_from_points(plotter_3d, points3, WallHeight/2)
plotter_3d.show_grid()
plotter_3d.show()
