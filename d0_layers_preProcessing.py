import os
import ezdxf
from b2_DXF_decomposition_newAlgorithm import dxf2svg


def entity_range(msp, x=False, keyword=''):
    LinePoints = []
    for entity in msp:
        if keyword in entity.dxf.layer.lower():
            if entity.dxftype() == 'LINE':
                if x:
                    line = (entity.dxf.start.x, entity.dxf.end.x)
                else:
                    line = (entity.dxf.start.y, entity.dxf.end.y)
                LinePoints.append([min(line), max(line), [entity]])
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                try:
                    if x:
                        points = [vertex[0] for vertex in entity.vertices()]
                    else:
                        points = [vertex[1] for vertex in entity.vertices()]
                    LinePoints.append([min(points), max(points), [entity]])
                except:
                    pass
    LinePoints.sort(key=lambda e: e[0])

    return LinePoints


def clustering_by_line(points_list):
    
    if len(points_list) > 0:
        
        clusters = [points_list[0]]
        for i in range(len(points_list)-1):
            if clusters[-1][0] <= points_list[i+1][0] <= clusters[-1][1]:
                clusters[-1][2].append(points_list[i+1][2][0])
                if clusters[-1][1] < points_list[i+1][1]:
                    clusters[-1][1] = points_list[i+1][1]
            elif clusters[-1][1] < points_list[i+1][0]:
                clusters.append(points_list[i+1])

        return clusters
    
    else:
        return []


def clustering_global(input_path, output_path, keyword='', thr = 1):
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()

    LinePointsY = entity_range(msp, keyword=keyword)
    clustersY = clustering_by_line(LinePointsY)

    clustersX = []
    for item in clustersY:
        if len(item[2]) > thr:
            LinePointsX = entity_range(item[2], x=True, keyword=keyword)
            clustersX += clustering_by_line(LinePointsX)

    clustersY = []
    for item in clustersX:
        if len(item[2]) > thr:
            LinePointsY = entity_range(item[2], keyword=keyword)
            clustersY += clustering_by_line(LinePointsY)

    clustersX = []
    for item in clustersY:
        if len(item[2]) > thr:
            LinePointsX = entity_range(item[2], x=True, keyword=keyword)
            clustersX += clustering_by_line(LinePointsX)

    n = 1
    j = 0
    for item in clustersX:
        if len(item[2]) > thr:
            j += 1

            doc_new = ezdxf.new()
            msp_new = doc_new.modelspace()
            for e in item[2]:
                msp_new.add_foreign_entity(e)
            
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            doc_new.saveas(f'{output_path}/{layer}_{n}.dxf')
            
            n = n + 1


path = "decomposed"
files = os.listdir(path)
layers = ['balcony', 'roof', 'stair']


for file in files:
    
    if file.lower().endswith('.dxf') and file.lower().startswith('plan'):
        file = os.path.splitext(file)[0]
        
        for layer in layers:
            input_path = f"{path}/{file}.dxf"
            output_path = f"{path}/{file}/{layer}"
            clustering_global(input_path, output_path, keyword=layer, thr=1)
            dxf2svg(path=output_path)
