from utils import transform_point, radius_scale, rotate_arc, oghlidosi
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
import numpy as np
import ezdxf


def recreate_entity_in_msp(entity, msp):
    """
    Recreate an entity in the provided modelspace (msp).
    """
    if entity.dxftype() == 'LINE':
        msp.add_line(start=entity.dxf.start, end=entity.dxf.end)
    elif entity.dxftype() == 'CIRCLE':
        msp.add_circle(center=entity.dxf.center, radius=entity.dxf.radius)
    elif entity.dxftype() == 'ARC':
        msp.add_arc(center=entity.dxf.center, radius=entity.dxf.radius, start_angle=entity.dxf.start_angle, end_angle=entity.dxf.end_angle)
    elif entity.dxftype() == 'TEXT':
        msp.add_text(entity.dxf.text, dxfattribs={'insert': entity.dxf.insert, 'height': entity.dxf.height})
    elif entity.dxftype() == 'MTEXT':
        msp.add_mtext(entity.dxf.text, dxfattribs={'insert': entity.dxf.insert})
    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
        # Recreating a basic 2D polyline. If your DWG contains 3D polylines or other variations, more handling would be required.
        points = [vertex.dxf.location for vertex in entity.vertices()]
        msp.add_lwpolyline(points)
    elif entity.dxftype() == 'HATCH':
        msp.add_hatch(extrusion=entity.dxf.extrusion, hatch_style=entity.dxf.hatch_style, pattern_type=entity.dxf.pattern_type, pattern_angle=entity.dxf.pattern_angle, pattern_scale=entity.dxf.pattern_scale)
    # elif entity.dxftype() == 'DIMENSION':
    #     msp.add_dimension(defpoint=entity.dxf.defpoint, text_midpoint=entity.dxf.text_midpoint, dimtype=entity.dxf.dimtype, attachment_point=entity.dxf.attachment_point, actual_measurement=entity.dxf.actual_measurement, defpoint2=entity.dxf.defpoint2, defpoint3=entity.dxf.defpoint3)


doc = ezdxf.readfile('inputDXF/1.dxf')
msp = doc.modelspace()


#---------------get all lines for clustering-------------
'''
# List of all layer names
layer_names = [layer.dxf.name for layer in doc.layers]
# layer_names = ["FP-Proposed Wall"]
# print(layer_names)

all_lines = []
for layer_name in layer_names:
    msp = doc.modelspace()
    entities_on_layer = msp.query(f'LINE[layer=="{layer_name}"]')
    new_doc = ezdxf.new()
    msp = new_doc.modelspace()
    for line in entities_on_layer:
        start_point = line.dxf.start
        end_point = line.dxf.end
        all_lines.append((start_point, end_point))

lines_array = np.array(all_lines)

# Reshape the array to a single dimension
lines_array = lines_array.reshape((-1, 6))
'''
#------------------------------------------------------


#---------------get centers for clustering-------------
centroids = []
entities_with_centroids = []

for entity in msp:
    centroid = None
    if entity.dxftype() == 'LINE':
        x = (entity.dxf.start.x + entity.dxf.end.x) / 2
        y = (entity.dxf.start.y + entity.dxf.end.y) / 2
        centroid = (x, y)
    elif entity.dxftype() in ['CIRCLE', 'ARC', 'ELLIPSE']:
        centroid = (entity.dxf.center.x, entity.dxf.center.y)
    elif entity.dxftype() == ['HATCH', 'SPLINE']:
        centroid = (entity.dxf.extrusion.x, entity.dxf.extrusion.y)
    elif entity.dxftype() in ['TEXT', 'MTEXT', 'INSERT', 'WIPEOUT',]:
        centroid = (entity.dxf.insert.x, entity.dxf.insert.y)
    elif entity.dxftype() == 'DIMENSION':
        centroid = (entity.dxf.defpoint.x, entity.dxf.defpoint.y)
    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
        # Recreating a basic 2D polyline. If your DWG contains 3D polylines or other variations, more handling would be required.
        point = [vertex for vertex in entity.vertices()][0]
        centroid = point

    if centroid:
        centroids.append(centroid)
        entities_with_centroids.append(entity)
#------------------------------------------------------


#------------------------KMeans------------------------
# num_clusters = 8  # Replace with the desired number of clusters
# Number of expected plans/elevations (automating num_clusters)
wcss = []
max_clusters = 20  # Maximum number of clusters to try
for n_clusters in range(1, max_clusters + 1):
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(centroids)
    wcss.append(kmeans.inertia_/1e11)
    if kmeans.inertia_/1e11 < 0.05:
        num_clusters = n_clusters
        break

kmeans = KMeans(n_clusters=n_clusters)
labels = kmeans.fit_predict(centroids)

# Get cluster labels for each line
cluster_labels = kmeans.labels_

# . . . . Plot the WCSS values . . . .
# print(wcss)
# plt.plot(range(1, max_clusters + 1), wcss)
# plt.xlabel('Number of Clusters')
# plt.ylabel('WCSS')
# plt.title('Elbow Method')
# plt.show()
#------------------------------------------------------


#------------------------Oghlidosi---------------------
# all_dist = []
# new_doc = ezdxf.new()
# msp = new_doc.modelspace()
# for i in range(len(all_lines)):
#     msp.add_line(start=all_lines[i][0], end=all_lines[i][1])
#     if i > 2:
#         d1 = oghlidosi(all_lines[i-2][-1], all_lines[i-3][-1])
#         d2 = oghlidosi(all_lines[i-1][-2], all_lines[i-2][-1])

#         if d2 > 6200:
#             # oghlidosi(all_lines[-1][-2], all_lines[-2][-1]) > 20*oghlidosi(all_lines[-2][-1], all_lines[-3][-1]): 
#             all_dist.append(d1)
#             # i = len(all_dist)
#             new_doc.saveas(f"seplayer/file{i}.dxf")
#             new_doc = ezdxf.new()
#             msp = new_doc.modelspace()

# print(len(all_dist))
#------------------------------------------------------


#------------------------DBSCAN------------------------
'''
dbscan = DBSCAN(eps=0.00000000001, min_samples=2)
# Fit the model to your data
# Get the cluster labels for each point
cluster_labels = dbscan.fit_predict(lines_array)

print(*cluster_labels)
print(len(cluster_labels))

# Separate lines into different groups based on cluster labels
num_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
'''
#------------------------------------------------------


#-----------------AgglomerativeClustering--------------
'''
# Apply Agglomerative Clustering
clustering = AgglomerativeClustering(n_clusters=8)
cluster_labels = clustering.fit_predict(lines_array)

# Determine the number of clusters
num_clusters = len(np.unique(cluster_labels))
'''
#------------------------------------------------------


'''
# Separate lines into different groups based on cluster labels
clusters = [[] for _ in range(num_clusters)]
for i, label in enumerate(cluster_labels):
    # if label != -1: # for dbscan
        clusters[label].append(all_lines[i])
'''

for i in range(num_clusters):
# for i, cluster in enumerate(clusters):
    # print(f"Cluster {i+1}:")
    new_doc = ezdxf.new()
    msp_new = new_doc.modelspace()
    # for line in cluster:
    #     msp.add_line(start=line[0], end=line[1])
    entities_for_cluster = [entity for j, entity in enumerate(entities_with_centroids) if labels[j] == i]
    # for entity in entities_for_cluster:
    #     recreate_entity_in_msp(entity, msp_new)
    # new_doc.saveas(f"decomposed/cluster_{i}.dxf")
    # or
    # from ezdxf.addons import Importer
    # importer = Importer(doc, new_doc)
    # importer.import_entity(entity, msp_new)


    entities_layers = list({str(entity.dxf.layer).lower() for j, entity in enumerate(entities_with_centroids) if labels[j] == i})
    txt_layer = ' '.join(entities_layers)
    if len(entities_for_cluster) < 100:
        continue

    filename = f'other_{i}'
    if 'roof' in txt_layer and 'door' not in txt_layer and 'window' not in txt_layer and 'foot' not in txt_layer:
        filename = f'plan_{i}'
    if 'furniture' in txt_layer:
        filename = f'plan_{i}'
    if 'foot' in txt_layer:
        filename = f'elevation_{i}'

    for entity in entities_for_cluster:
        if entity.dxftype() in ['MTEXT']:
            if 'room' in str(entity.text).lower():
                filename = f'plan_{i}'

        if entity.dxftype() == 'INSERT':
            layer = entity.dxf.layer
            block = entity.doc.blocks[entity.dxf.name]
            for e in block:
                if e.dxf.invisible == 0:
                    if e.dxftype() == 'LINE':
                        # e.dxf.start = transform_point(e.dxf.start, entity, scale=False)
                        # e.dxf.end = transform_point(e.dxf.end, entity, scale=False)
                        # msp_new.add_foreign_entity(e)
                        start = transform_point(e.dxf.start, entity)
                        end = transform_point(e.dxf.end, entity)
                        msp_new.add_line(start=start, end=end, dxfattribs={"layer": layer})
                    if e.dxftype() in ['LWPOLYLINE', 'POLYLINE']:                        
                        points = [transform_point(vertex, entity) for vertex in e.vertices()]
                        msp_new.add_lwpolyline(points, dxfattribs={"layer": layer})
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
                    elif e.dxftype() == 'INSERT':
                        block2 = e.doc.blocks[e.dxf.name]
                        for e2 in block2:
                            if e2.dxf.invisible == 0:
                                if e2.dxftype() == 'LINE':
                                    start = transform_point(e2.dxf.start, e)
                                    end = transform_point(e2.dxf.end, e)
                                    msp_new.add_line(start=start, end=end, dxfattribs={"layer": layer})
                                elif e2.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                                    points = [transform_point(vertex, e) for vertex in e2.vertices()]
                                    msp_new.add_lwpolyline(points, dxfattribs={"layer": layer})
                                elif e2.dxftype() == 'CIRCLE':
                                    center = transform_point(e2.dxf.center, e)
                                    msp_new.add_circle(center=center, radius=e2.dxf.radius, dxfattribs={"layer": layer})

        else:
            if entity.dxftype() not in ['MTEXT', 'TEXT', 'DIMENSION', 'WIPEOUT']:
                try:
                    msp_new.add_foreign_entity(entity)
                except:
                    pass

    new_doc.saveas(f"decomposed/{filename}.dxf")
