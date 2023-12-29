import pyvista as pv
import math
import ezdxf


def dxf_to_pyvista_line(line):
    """Convert a DXF LINE entity to a pyvista Line."""
    p1 = [line.dxf.start.x, line.dxf.start.y, 0]
    p2 = [line.dxf.end.x, line.dxf.end.y, 0]
    return pv.Line(p1, p2)
    

def dxf_to_pyvista_polyline(polyline):
    """Convert DXF POLYLINE or LWPOLYLINE to pyvista PolyData."""
    vertices = [vertex[:2] + (0,) for vertex in polyline.vertices()]
    lines = []
    for i in range(len(vertices) - 1):
        line = pv.Line(vertices[i], vertices[i+1])
        lines.append(line)

    # If the polyline is closed, add the last segment
    if polyline.is_closed:
        line = pv.Line(vertices[-1], vertices[0])
        lines.append(line)

    return lines


def dxf_to_pyvista_polyline2(polyline):
    """Convert DXF POLYLINE or LWPOLYLINE to pyvista PolyData."""
    vertices = [vertex+(0,) for vertex in polyline.vertices()]
    if polyline.is_closed:
        vertices = vertices + [vertices[0]]
    polyline_data = pv.PolyData(vertices)
    polyline_data.lines = [len(vertices)] + list(range(len(vertices)))
    return polyline_data


def dxf_to_pyvista_hatch(hatch):
    """Convert DXF HATCH to a list of pyvista PolyData."""
    all_hatch_data = []

    for path in hatch.paths:
        vertices = []
        vertices_faces = []

        if isinstance(path, ezdxf.entities.EdgePath):
            for edge in path.edges:
                if edge.EDGE_TYPE == 'LineEdge':
                    vertices.append((edge.start.x, edge.start.y, 0))
                    vertices.append((edge.end.x, edge.end.y, 0))
                elif edge.EDGE_TYPE == 'ArcEdge':
                    start_x = edge.center.x + edge.radius * math.cos(math.radians(edge.start_angle))
                    start_y = edge.center.y + edge.radius * math.sin(math.radians(edge.start_angle))
                    end_x = edge.center.x + edge.radius * math.cos(math.radians(edge.end_angle))
                    end_y = edge.center.y + edge.radius * math.sin(math.radians(edge.end_angle))
                    vertices.append((start_x, start_y, 0))
                    vertices.append((end_x, end_y, 0))
                # Additional edge types can be handled similarly.

        elif isinstance(path, ezdxf.entities.PolylinePath):
            for vertex in path.vertices:
                if len(vertex) == 2:
                    x, y = vertex
                    z = 0
                else:
                    x, y, z = vertex
                    z = 0
                vertices.append((x, y, z))

            if path.is_closed:
                vertices = vertices + [vertices[0]]
                vertices_faces = vertices

        hatch_data = pv.PolyData(vertices)
        hatch_data.lines = [len(vertices)] + list(range(len(vertices)))
        hatch_data.faces = [len(vertices_faces)] + list(range(len(vertices_faces)))
        all_hatch_data.append(hatch_data)

    return all_hatch_data
