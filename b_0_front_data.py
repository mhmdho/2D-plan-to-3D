import ezdxf
import json
from utils import transform_point, radius_scale


def front_data(data, msp):
    for label, cord in data.items():
        if cord['entity']['type'] == 'POLYLINE':
            mtxt = msp.add_mtext(label, dxfattribs={"insert": 
                (cord['entity']['vertices'][0]['x'], cord['entity']['vertices'][0]['y']),
                "style": "OpenSans",
                "layer": 'label',
                "rotation": 45,
                "color": 30,
                "bg_fill": 1,
                "bg_fill_color": 10,
                "char_height": 35
                                            })
            # mtxt.dxf.char_height = 15
            # mtxt.set_bg_color(2, scale=5)
            print(label, (cord['entity']['vertices'][0]['x'], cord['entity']['vertices'][0]['y']))

        elif cord['entity']['type'] == 'LINE':
            mtxt = msp.add_mtext(label, dxfattribs={"insert": 
                (cord['entity']['start']['x'], cord['entity']['start']['y']),
                "style": "OpenSans",
                "layer": 'label',
                "rotation": 45,
                "color": 30,
                "bg_fill": 1,
                "bg_fill_color": 10,
                "char_height": 35
                                            })
            # mtxt.dxf.char_height = 30
            # mtxt.set_bg_color(10)
            print(label, (cord['entity']['start']['x'], cord['entity']['start']['y']))


file_names = ['underground', 'groundfloor', 'firstfloor', 'frontview',
                'roof', 'leftview', 'backview', 'rightview']


file = '1.dxf'
doc = ezdxf.readfile(f'inputDXF/{file}')
msp = doc.modelspace()


doc_new = ezdxf.new()
msp_new = doc_new.modelspace()


front_file = 'app.json'
my_file = open(front_file)
data = json.load(my_file)
front_data(data, msp_new)


for entity in msp:
    if entity.dxftype() in ['MTEXT']:
        if entity.text in file_names:
            filename = entity.text
            print('-------------', filename)

    elif entity.dxftype() == 'INSERT':
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
                    radius_x=e.dxf.radius*entity.dxf.xscale
                    radius_y=e.dxf.radius*entity.dxf.yscale
                    msp_new.add_circle(center=center, radius=max(radius_y, radius_x), dxfattribs={"layer": layer})
                elif e.dxftype() == 'ARC':
                    center = transform_point(e.dxf.center, entity)
                    radius_x=e.dxf.radius*entity.dxf.xscale
                    radius_y=e.dxf.radius*entity.dxf.yscale
                    msp_new.add_arc(center=center, radius=radius_scale(e, entity), 
                                    start_angle=e.dxf.start_angle+entity.dxf.rotation, 
                                    end_angle=e.dxf.start_angle+entity.dxf.rotation,
                                    dxfattribs={"layer": layer})
    elif entity.dxftype() not in ['MTEXT', 'TEXT', 'DIMENSION', 'WIPEOUT']:
        try:
            msp_new.add_foreign_entity(entity)
        except:
            pass


doc_new.saveas(f"decomposed_1/{front_file}On{file}")
