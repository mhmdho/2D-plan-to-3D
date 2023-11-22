import ezdxf


# doc = ezdxf.readfile("decomposed_1/frontlabeledapp2_22.dxf")
# doc = ezdxf.readfile('decomposed_1/frontlabeledapp2.dxf')
# doc = ezdxf.readfile('decomposed_cr/11.dxf')
doc = ezdxf.readfile('inputDXF/1.dxf')
msp = doc.modelspace()


def entity_range(msp, x=False):
    LinePoints = []
    for entity in msp:
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
    clusters = [points_list[0]]
    for i in range(len(points_list)-1):
        if clusters[-1][0] <= points_list[i+1][0] <= clusters[-1][1]:
            clusters[-1][2].append(points_list[i+1][2][0])
            if clusters[-1][1] < points_list[i+1][1]:
                clusters[-1][1] = points_list[i+1][1]
        elif clusters[-1][1] < points_list[i+1][0]:
            clusters.append(points_list[i+1])

    return clusters


LinePointsY = entity_range(msp)
clustersY = clustering_by_line(LinePointsY)


clustersX = []
for item in clustersY:
    if len(item[2]) > 50:
        LinePointsX = entity_range(item[2], x=True)
        clustersX += clustering_by_line(LinePointsX)


clustersY = []
for item in clustersX:
    if len(item[2]) > 50:
        LinePointsY = entity_range(item[2])
        clustersY += clustering_by_line(LinePointsY)


clustersX = []
for item in clustersY:
    if len(item[2]) > 50:
        LinePointsX = entity_range(item[2], x=True)
        clustersX += clustering_by_line(LinePointsX)


j = 0
for item in clustersX:
    if len(item[2]) > 50:
        j += 1

        doc_new = ezdxf.new()
        msp_new = doc_new.modelspace()
        for e in item[2]:
            msp_new.add_foreign_entity(e)
        doc_new.saveas(f"decomposed_cr/{j}{j}.dxf")
