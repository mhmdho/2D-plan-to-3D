from sklearn.cluster import KMeans
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


# Number of plans/elevations you expect
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


for i in range(n_clusters):
    new_doc = ezdxf.new()
    msp_new = new_doc.modelspace()
    
    # Entities corresponding to current cluster
    entities_for_cluster = [entity for j, entity in enumerate(entities_with_centroids) if labels[j] == i]
    
    for entity in entities_for_cluster:
        recreate_entity_in_msp(entity, msp_new)
    
    new_doc.saveas(f"decomposed/cluster_{i}.dxf")
