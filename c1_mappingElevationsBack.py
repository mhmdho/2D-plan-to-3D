from utils import entity_range_xy, line_equation
import ezdxf


path = "decomposed_cr/1c/"
file_e = "1414back.dxf"
file_p = "2323plan.dxf"


doc_e = ezdxf.readfile(f'{path}{file_e}')
msp_e = doc_e.modelspace()
doc_p = ezdxf.readfile(f'{path}{file_p}')
msp_p = doc_p.modelspace()


lines_e = entity_range_xy(msp_e, 0, reverse=True)
lines_p = entity_range_xy(msp_p, 0, reverse=True)


min_p = min(lines_p, key=lambda a: a[0][0])
max_p = max(lines_p, key=lambda a: a[1][0])
min_e = min(lines_e, key=lambda a: a[0][0])
max_e = max(lines_e, key=lambda a: a[1][0])


front_lines2 = [min_p]
while True:
    front_lines = []
    for i in range(len(lines_p)):

        if front_lines2[-1][0][0] <= lines_p[i][0][0] <= front_lines2[-1][1][0] and \
        lines_p[i][1][0] > front_lines2[-1][1][0]:
            front_lines.append(lines_p[i])
        elif front_lines2[-1][0][0] <= lines_p[i][0][0] <= front_lines2[-1][1][0] and \
        front_lines2[-1][0][0] <= lines_p[i][1][0] <= front_lines2[-1][1][0] and \
        lines_p[i][0][1] > front_lines2[-1][0][1] and \
        lines_p[i][1][1] > front_lines2[-1][1][1]:
            split_line = front_lines2[-1][:]
            print('before:', front_lines2[-1])
            front_lines2[-1][1] = (lines_p[i][0][0], front_lines2[-1][1][1], front_lines2[-1][1][2])
            print('after:', front_lines2[-1])
            print('middle:', lines_p[i])
            print('split:', split_line)
            split_line[0] = (lines_p[i][1][0], front_lines2[-1][0][1], front_lines2[-1][0][2])
            new_lines = [lines_p[i], split_line]
            front_lines2.extend(new_lines)
    if len(front_lines) == 0 or front_lines[-1][1][0] == max_p[1][0]:
        break
    min_p1 = max(front_lines, key=lambda a: a[0][1])
    min_p2 = max(front_lines, key=lambda a: a[1][1])
    if min_p1[0][1] > min_p2[1][1]:
        front_lines2.append(min_p1)
    else:
        front_lines2.append(min_p2)


# for j in range(len(front_lines2)):
#     first_element = [front_lines2[j][0][0], front_lines2[j][0][1] * -1, front_lines2[j][0][2]]
#     second_element = [front_lines2[j][1][0], front_lines2[j][1][1] * -1, front_lines2[j][1][2]]
#     front_lines2[j][0] = min(first_element, second_element)
#     front_lines2[j][1] = max(first_element, second_element)


doc = ezdxf.new()
msp = doc.modelspace()


for entity in msp_e:
    if entity.dxftype() == 'LWPOLYLINE':
        points = entity.get_points()
        for i in range(len(points)-1):
            msp_e.add_line(start=points[i][:3], end=points[i+1][:3], dxfattribs={"layer": entity.dxf.layer})


for entity in msp_e:
    if entity.dxftype() == 'LINE':
        entity.dxf.start = (entity.dxf.start.x * -1, entity.dxf.start.y, entity.dxf.start.z)
        entity.dxf.end = (entity.dxf.end.x * -1, entity.dxf.end.y, entity.dxf.end.z)
        for item_plan in front_lines2:
            if entity.dxf.start.x <= front_lines2[0][0][0]:
                entity.dxf.start = (entity.dxf.start.x, entity.dxf.start.y, front_lines2[0][0][1] * -1)
            elif entity.dxf.start.x >= front_lines2[-1][1][0]:
                entity.dxf.start = (entity.dxf.start.x, entity.dxf.start.y, front_lines2[-1][1][1] * -1)

            if entity.dxf.end.x <= front_lines2[0][0][0]:
                entity.dxf.end = (entity.dxf.end.x, entity.dxf.end.y, front_lines2[0][0][1] * -1)
            elif entity.dxf.end.x >= front_lines2[-1][1][0]:
                entity.dxf.end = (entity.dxf.end.x, entity.dxf.end.y, front_lines2[-1][1][1] * -1)

            if item_plan[0][0] <= entity.dxf.start.x <= item_plan[1][0]:
                entity.dxf.start = (entity.dxf.start.x, entity.dxf.start.y, line_equation(item_plan, entity.dxf.start.x) * -1)

            if item_plan[0][0] <= entity.dxf.end.x <= item_plan[1][0]:
                entity.dxf.end = (entity.dxf.end.x, entity.dxf.end.y, line_equation(item_plan, entity.dxf.end.x) * -1)
            
        msp.add_line(start=entity.dxf.start, end=entity.dxf.end, dxfattribs={"layer": entity.dxf.layer})
    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
        for item_plan in front_lines2:
            points = entity.get_points()
            new_points = [point for point in points]
            for i in range(len(new_points)):
                if new_points[i][0] <= front_lines2[0][0][0] or new_points[i][0] >= front_lines2[-1][1][0]:
                    new_points[i] = (new_points[i][0], new_points[i][1], front_lines2[0][0][1])

                if item_plan[0][0] <= new_points[i][0] <= item_plan[1][0]:
                    new_points[i] = (new_points[i][0], new_points[i][1], item_plan[0][1])

            # entity.set_points(new_points)
        # msp.add_lwpolyline(new_points)

    # msp.add_line(start=(item_plan[0], item_plan[2]), end=(item_plan[1], item_plan[3]))
    # msp.add_foreign_entity(item_plan[-1][0])
    # msp.add_line(start=item_plan[0], end=item_plan[1])
    # msp.add_foreign_entity(entity)

doc.saveas(f"{path}mapping_elevation{file_e}{file_p}")


doc2 = ezdxf.new()
msp2 = doc2.modelspace()

for item_plan in front_lines2:
    msp2.add_line(start=item_plan[0], end=item_plan[1])
doc2.saveas(f"{path}mapping_planlines_{file_e}{file_p}")
