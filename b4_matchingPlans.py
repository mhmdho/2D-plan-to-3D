import ezdxf
from b2_DXF_decomposition_newAlgorithm import entity_range
from collections import Counter
import os


def entity_distance(msp, x=False):
    LinePoints = []
    for entity in msp:
        if entity.dxftype() == 'LINE':
            if x:
                line = (abs(entity.dxf.start.x - entity.dxf.end.x), min(entity.dxf.start.x, entity.dxf.end.x), max(entity.dxf.start.x, entity.dxf.end.x)) 
            else:
                line = (abs(entity.dxf.start.y - entity.dxf.end.y), min(entity.dxf.start.y, entity.dxf.end.y), max(entity.dxf.start.y, entity.dxf.end.y))
            LinePoints.append(line)
        elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            try:
                if x:
                    points = [vertex[0] for vertex in entity.vertices()]
                else:
                    points = [vertex[1] for vertex in entity.vertices()]
                for i in range(len(points)):
                    line = (abs(points[i] - points[i+1]), min(points[i], points[i+1]), max(points[i], points[i+1]))
                    LinePoints.append(line)
                    if i+1 == len(points):
                        break
            except:
                pass
    LinePoints.sort(key=lambda e: e[0])

    return LinePoints


path = "decomposed/"


files = [item for item in os.listdir(path) if 'plan' in item]
file2 = files[0]
for file in files[1:]:
    file1 = file


    doc1 = ezdxf.readfile(f'{path}{file1}')
    msp1 = doc1.modelspace()
    doc2 = ezdxf.readfile(f'{path}{file2}')
    msp2 = doc2.modelspace()


    listx1 = entity_range(msp1, x=True)
    listy1 = entity_range(msp1, x=False)

    listx2 = entity_range(msp2, x=True)
    listy2 = entity_range(msp2, x=False)

    max_x1 = max(listx1, key=lambda a: a[1])[1]
    max_y1 = max(listy1, key=lambda a: a[1])[1]

    max_x2 = max(listx2, key=lambda a: a[1])[1]
    max_y2 = max(listy2, key=lambda a: a[1])[1]


    x_scope = abs(max_x1 - max_x2)
    y_scope = abs(max_y1 - max_y2)


    listx1 = entity_distance(msp1, x=True)
    listy1 = entity_distance(msp1, x=False)
    
    listx2 = entity_distance(msp2, x=True)
    listy2 = entity_distance(msp2, x=False)

    x_coordinate = 0
    x_cord = []
    for item1 in listx1:
        for item2 in listx2:
            if item1[0] == item2[0]:
                x_cord.append(item1[1]-item2[1])

    counter = Counter(x_cord)

    newx = []
    for item, count in counter.items():
        newx.append((item, count))

    newx.sort(reverse=True, key=lambda a : a[1])

    for element in newx:
        if abs(element[0]) < x_scope:
            x_coordinate = element[0]
            break

    y_coordinate = 0
    y_cord = []
    for item1 in listy1:
        for item2 in listy2:
            if item1[0] == item2[0]:
                y_cord.append(item1[1]-item2[1])

    counter = Counter(y_cord)

    newy = []
    for item, count in counter.items():
        newy.append((item, count))

    newy.sort(reverse=True, key=lambda a : a[1])

    for element in newy:
        if abs(element[0]) < y_scope:
            y_coordinate = element[0]
            break


    print(x_coordinate)
    print(y_coordinate)


    doc = ezdxf.new()
    msp = doc.modelspace()

    for entity in msp2:
        msp.add_foreign_entity(entity)
    for entity in msp1:
        if entity.dxftype() == 'LINE':
            entity.dxf.start = (entity.dxf.start.x - x_coordinate, entity.dxf.start.y - y_coordinate, entity.dxf.start.z)
            entity.dxf.end = (entity.dxf.end.x - x_coordinate, entity.dxf.end.y - y_coordinate, entity.dxf.end.z)
        elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            try:
                points = entity.get_points()
                new_points = [(point[0] - x_coordinate, point[1] - y_coordinate, point[2]) for point in points]
                entity.set_points(new_points)
            except:
                pass
        msp.add_foreign_entity(entity)

    doc1.saveas(f"{path}{file1}")
