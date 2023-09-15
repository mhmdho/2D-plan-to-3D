import math

def transform_point(point, insert, scale=True):
    """Transforms a point based on the properties of an INSERT entity."""
    if len(point) == 2:
        x, y = point
        z = 0
    else:
        x, y, z = point

    # Step 1: Scaling
    if scale == True:
        x *= insert.dxf.xscale
        y *= insert.dxf.yscale
        # z *= insert.dxf.zscale  # Assuming you also want z-scaling, otherwise leave it out

    # Step 2: Rotation (about the Z-axis)
    angle = math.radians(insert.dxf.rotation)
    x_rot = x * math.cos(angle) - y * math.sin(angle)
    y_rot = x * math.sin(angle) + y * math.cos(angle)
    
    # Step 3: transporting
    x0, y0, z0 = insert.dxf.insert
    x_rot += x0
    y_rot += y0

    return x_rot, y_rot, z


def radius_scale(arc, insert):
    """Scale radius of circle based on the properties of an INSERT entity."""
    radius = arc.dxf.radius
    angle = math.radians(arc.dxf.end_angle)
    return math.sqrt((radius*math.cos(angle)*insert.dxf.xscale)**2 +
        (radius*math.sin(angle)*insert.dxf.yscale)**2)
