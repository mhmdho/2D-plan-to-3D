import ezdxf
from utils import transform_point, radius_scale


doc = ezdxf.readfile('inputDXF/1.dxf')
msp = doc.modelspace()


doc_new = ezdxf.new()
msp_new = doc_new.modelspace()


for entity in msp:
    if entity.dxftype() == 'INSERT':
        layer = entity.dxf.layer
        block = entity.doc.blocks[entity.dxf.name]
        for e in block:
            if e.dxf.invisible == 0:
                if e.dxftype() == 'LINE':
                    start = transform_point(e.dxf.start, entity)
                    end = transform_point(e.dxf.end, entity)
                    msp_new.add_line(start=start, end=end, dxfattribs={"layer": layer})
                elif e.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    try:                     
                        points = [transform_point(vertex, entity) for vertex in e.vertices()]
                        msp_new.add_lwpolyline(points, dxfattribs={"layer": layer})
                    except:
                        pass
                elif e.dxftype() == 'CIRCLE':
                    center = transform_point(e.dxf.center, entity)
                    radius_x = e.dxf.radius * entity.dxf.xscale
                    radius_y = e.dxf.radius * entity.dxf.yscale
                    msp_new.add_circle(center=center, radius=max(radius_y, radius_x), dxfattribs={"layer": layer})
                elif e.dxftype() == 'ARC':
                    center = transform_point(e.dxf.center, entity)
                    start_angle = e.dxf.start_angle
                    end_angle = e.dxf.end_angle
                    if entity.dxf.xscale < 0:
                        start_angle = 360 + (- 180 - e.dxf.end_angle)
                        end_angle = 360 + (- 180 - e.dxf.start_angle)
                    if entity.dxf.yscale < 0:
                        start_angle = end_angle * -1
                        end_angle = start_angle * -1
                    msp_new.add_arc(center=center, radius=radius_scale(e, entity), 
                                    start_angle = start_angle + entity.dxf.rotation,
                                    end_angle = end_angle + entity.dxf.rotation,
                                    dxfattribs={"layer": layer}
                                    )
    elif entity.dxftype() not in ['MTEXT', 'TEXT', 'DIMENSION', 'WIPEOUT']:
        try:
            msp_new.add_foreign_entity(entity)
        except:
            pass


doc_new.saveas('inputDXF/1.dxf')
