import ezdxf
import os
from b2_DXF_decomposition_newAlgorithm import entity_range


path = "decomposed/"

for file in os.listdir(path):
    if file.split('.')[-1] == 'dxf':

        doc = ezdxf.readfile(f'{path}{file}')
        msp = doc.modelspace()

        listx = entity_range(msp, x=True)
        listy = entity_range(msp, x=False)

        max_x = max(listx, key=lambda a: a[1])[1]
        min_x = min(listx, key=lambda a: a[0])[0]
        max_y = max(listy, key=lambda a: a[1])[1]
        min_y = min(listy, key=lambda a: a[0])[0]

        for entity in msp:
            if entity.dxftype() == 'LINE':
                entity.dxf.start = (entity.dxf.start.x-min_x, entity.dxf.start.y-min_y, entity.dxf.start.z)
                entity.dxf.end = (entity.dxf.end.x-min_x, entity.dxf.end.y-min_y, entity.dxf.end.z)
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                try:
                    points = entity.get_points()
                    new_points = [(point[0] - min_x, point[1] - min_y, point[2]) for point in points]
                    entity.set_points(new_points)
                except:
                    pass

        doc.saveas(f"{path}{file}")
