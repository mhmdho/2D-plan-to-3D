import ezdxf


path = "decomposed_cr/1c/"
file_e = "1313east.dxf"
file_p = "2323plan.dxf"


doc_e = ezdxf.readfile(f'{path}{file_e}')
msp_e = doc_e.modelspace()
doc_p = ezdxf.readfile(f'{path}{file_p}')
msp_p = doc_p.modelspace()


def entity_range_xy(msp, xy):
    LinePoints = []
    for entity in msp:
        if entity.dxftype() == 'LINE':
            list_line = [entity.dxf.start, entity.dxf.end]
            list_line.sort(key= lambda a: a[xy]) # y:1
            if len(list_line[0]) == 2:
                list_line[0].append(0)
            if len(list_line[1]) == 2:
                list_line[1].append(0)
            LinePoints.append([list_line[0], list_line[1], [entity]])
        elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            points = [vertex for vertex in entity.vertices()]
            coord0 = points[0]
            for coord in points[1:]:
                list_coord = [list(coord0), list(coord)]
                list_coord.sort(key= lambda a: a[xy]) # y:1
                if len(list_coord[0]) == 2:
                    list_coord[0].append(0)
                if len(list_coord[1]) == 2:
                    list_coord[1].append(0)
                LinePoints.append([list_coord[0], list_coord[1], [entity]])
                coord0 = coord

    LinePoints.sort(key=lambda e: e[0][1])
    LinePoints.reverse()
    LinePoints.sort(key=lambda e: e[0][0])

    return LinePoints


# def line_equation(line, x):
#     if line[1][2] == line[0][2]:
#         y = line[1][0]
#     else:
#         m = (line[1][1] - line[0][1]) / (line[1][2] - line[0][2])
#         y = m * x - m * line[0][2] + line[0][1]
#     return y

def line_equation(line, y):
    if line[1][0] == line[0][0]:
        x = line[1][0]
    else:
        m = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0])
        x = (y + m * line[0][0] - line[0][1])  / m

    return x


lines_e = entity_range_xy(msp_e, 0)
lines_p = entity_range_xy(msp_p, 1)


min_p_y = min(lines_p, key=lambda a: a[0][1])
max_p_y = max(lines_p, key=lambda a: a[1][1])
min_e = min(lines_e, key=lambda a: a[0][0])
max_e = max(lines_e, key=lambda a: a[1][0])


print('plan min', min_p_y[0][1])
print('plan max', max_p_y[1][1])
print('plan min', min_p_y[0][0])
print('plan max', max_p_y[1][0])
print('elevation min', min_e[0][0])
print('elevation max', max_e[1][0])
print(max_e[1][0] - min_e[0][0])
print(max_p_y[1][1] - min_p_y[0][1])
elev_plan_dif = (abs(max_e[1][0] - min_e[0][0]) - abs(max_p_y[1][1] - min_p_y[0][1])) / 2
print(elev_plan_dif)

right_lines2 = [min_p_y]
while True:
    right_lines = []
    for i in range(len(lines_p)):
                                #ccheck
        if right_lines2[-1][0][1] <= lines_p[i][0][1] <= right_lines2[-1][1][1] and \
        lines_p[i][1][1] > right_lines2[-1][1][1]:
            right_lines.append(lines_p[i])
    if len(right_lines) == 0 or right_lines[-1][1][1] == max_p_y[1][1]:
        break
    min_p_y1 = max(right_lines, key=lambda a: a[0][0])
    min_p_y2 = max(right_lines, key=lambda a: a[1][0])
    min_p_y = max(min_p_y1, min_p_y2)
    right_lines2.append(min_p_y)


# for j in range(len(right_lines2)):
#     first_element = [right_lines2[j][0][1], right_lines2[j][0][0], right_lines2[j][0][2]]
#     second_element = [right_lines2[j][1][1], right_lines2[j][1][0], right_lines2[j][1][2]]
#     right_lines2[j][0] = min(first_element, second_element)
#     right_lines2[j][1] = max(first_element, second_element)


# min_p2 = min(right_lines2, key=lambda a: a[0][0])
# max_p2 = max(right_lines2, key=lambda a: a[1][0])
# print('rotated plan min', min_p2[0][0])
# print('rotated plan max', max_p2[1][0])
# right_lines2.sort(key=lambda a: a[0][0])


doc = ezdxf.new()
msp = doc.modelspace()


for entity in msp_e:
    if entity.dxftype() == 'LWPOLYLINE':
        points = entity.get_points()
        for i in range(len(points)-1):
            msp_e.add_line(start=points[i][:3], end=points[i+1][:3], dxfattribs={"layer": entity.dxf.layer})

doc3 = ezdxf.new()
msp3 = doc3.modelspace()


# translate elevation
min_e_x = min(lines_e, key=lambda a: a[0][0])[0][0] - min(lines_p, key=lambda a: a[0][1])[0][1]

for entity in msp_e:
    if entity.dxftype() == 'LINE':
        entity.dxf.start = (entity.dxf.start.z, entity.dxf.start.y, entity.dxf.start.x - min_e_x - elev_plan_dif)
        entity.dxf.end = (entity.dxf.end.z, entity.dxf.end.y, entity.dxf.end.x - min_e_x - elev_plan_dif)
        msp3.add_line(start=entity.dxf.start, end=entity.dxf.end)

doc3.saveas(f"{path}mapping333_planlines_{file_e}{file_p}")



lines_e = entity_range_xy(msp_e, 0)
lines_p = entity_range_xy(msp_p, 1)

min_p_yn = min(lines_p, key=lambda a: a[0][1])
max_p_yn = max(lines_p, key=lambda a: a[1][1])
min_en = min(lines_e, key=lambda a: a[0][2])
max_en = max(lines_e, key=lambda a: a[1][2])
print(min_p_yn[0][1], max_p_yn[1][1], 'plaaaaaaaaaaaaaaan')
print(min_en[0][2], max_en[1][2], 'eleeeeeeeeevation')

print(right_lines2[0][0][1], 'satrt')
print(right_lines2[-1][1][1], 'eeeeeeeeeend')

for entity in msp_e:
    if entity.dxftype() == 'LINE':
        # entity.dxf.start = (entity.dxf.start.z, entity.dxf.start.y, entity.dxf.start.x)
        # entity.dxf.end = (entity.dxf.end.z, entity.dxf.end.y, entity.dxf.end.x)
        for item_plan in right_lines2:
            if entity.dxf.start.z <= right_lines2[0][0][1]:
                entity.dxf.start = (right_lines2[0][0][0], entity.dxf.start.y, entity.dxf.start.z)
            elif entity.dxf.start.z >= right_lines2[-1][1][1]:
                entity.dxf.start = (right_lines2[-1][1][0], entity.dxf.start.y, entity.dxf.start.z)

            if entity.dxf.end.z <= right_lines2[0][0][1]:
                entity.dxf.end = (right_lines2[0][0][0], entity.dxf.end.y, entity.dxf.end.z)
            elif entity.dxf.end.z >= right_lines2[-1][1][1]:
                entity.dxf.end = (right_lines2[-1][1][0], entity.dxf.end.y, entity.dxf.end.z)

            if item_plan[0][1] <= entity.dxf.start.z <= item_plan[1][1]:
                entity.dxf.start = (line_equation(item_plan, entity.dxf.start.z), entity.dxf.start.y, entity.dxf.start.z)

            if item_plan[0][1] <= entity.dxf.end.z <= item_plan[1][1]:
                entity.dxf.end = (line_equation(item_plan, entity.dxf.end.z), entity.dxf.end.y, entity.dxf.end.z)
            
        msp.add_line(start=entity.dxf.start, end=entity.dxf.end, dxfattribs={"layer": entity.dxf.layer})


doc.saveas(f"{path}mapping_elevation{file_e}{file_p}")




doc4 = ezdxf.new()
msp4 = doc4.modelspace()
for entity in msp_e:
    if entity.dxftype() == 'LINE':
        entity.dxf.start = (entity.dxf.start.x, entity.dxf.start.y, -1 * entity.dxf.start.z)
        entity.dxf.end = (entity.dxf.end.x, entity.dxf.end.y, -1 * entity.dxf.end.z)
        msp4.add_line(start=entity.dxf.start, end=entity.dxf.end)

doc4.saveas(f"{path}mapping444_planlines_{file_e}{file_p}")


doc2 = ezdxf.new()
msp2 = doc2.modelspace()

for item_plan in right_lines2:
    msp2.add_line(start=item_plan[0], end=item_plan[1])
doc2.saveas(f"{path}mapping_planlines_{file_e}{file_p}")
