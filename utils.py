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


def rotate_slice(arc, insert):
    # Step 1: Determine the center of the circle
    center = arc.dxf.center
    rotate_point = insert.dxf.insert

    # Step 2: Calculate the distance between the center and the rotation point
    distance = math.sqrt((rotate_point.x - center.x) ** 2 + (rotate_point.y - center.y) ** 2)

    # Step 3: Convert distance and angle to Cartesian coordinates
    rotate_cartesian_x = distance * math.cos(math.radians(insert.dxf.rotation))
    rotate_cartesian_y = distance * math.sin(math.radians(insert.dxf.rotation))

    # Step 4: Apply rotation to the Cartesian coordinates
    rotated_x = rotate_point.x + rotate_cartesian_x
    rotated_y = rotate_point.y + rotate_cartesian_y

    # Step 5: Convert the rotated coordinates back to polar coordinates
    rotated_angle = math.degrees(math.atan2(rotated_y - center.y, rotated_x - center.x))

    return rotated_angle


def rotate_arc(arc, insert):
    rotate_point = insert.dxf.insert
    center = arc.dxf.center
    angle_points = math.degrees(math.atan2(center.y - rotate_point.y, center.x - rotate_point.x))
    # start_angle = angle_points + arc.dxf.start_angle*math.cos(math.radians(arc.dxf.start_angle)) + arc.dxf.start_angle*math.sin(math.radians(arc.dxf.start_angle))
    # end_angle = angle_points + arc.dxf.end_angle*math.cos(math.radians(arc.dxf.end_angle)) + arc.dxf.end_angle*math.sin(math.radians(arc.dxf.end_angle))
    start_angle = angle_points + arc.dxf.start_angle + insert.dxf.rotation
    end_angle = angle_points + arc.dxf.end_angle + insert.dxf.rotation

    return start_angle, end_angle
