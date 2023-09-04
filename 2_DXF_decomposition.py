from sklearn.cluster import KMeans
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
    elif entity.dxftype() == 'POLYLINE':
        # Recreating a basic 2D polyline. If your DWG contains 3D polylines or other variations, more handling would be required.
        points = [vertex.dxf.location for vertex in entity.vertices()]
        msp.add_lwpolyline(points)


doc = ezdxf.readfile('inputDXF/1.dxf')

# Get all layers
layers = doc.layers

# List all layer names
layer_names = [layer.dxf.name for layer in layers]
# layer_names = ["FP-Proposed Wall"]
# print(layer_names)

all_lines = []


for layer_name in layer_names:
    msp = doc.modelspace()
    entities_on_layer = msp.query(f'LINE[layer=="{layer_name}"]')
    # Process or save entities_on_layer as needed
    new_doc = ezdxf.new()
    msp = new_doc.modelspace()
    for line in entities_on_layer:
        start_point = line.dxf.start
        end_point = line.dxf.end
        all_lines.append((start_point, end_point))


lines_array = np.array(all_lines)

# Reshape the array to have a single dimension
lines_array = lines_array.reshape((-1, 6))

# num_clusters = 8  # Replace with the desired number of clusters
# Determine the number of clusters
wcss = []
max_clusters = 20  # Maximum number of clusters to try
for n_clusters in range(1, max_clusters + 1):
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(lines_array)
    wcss.append(kmeans.inertia_/1e11)
    if kmeans.inertia_/1e11 < 0.1:
        num_clusters = n_clusters
        break


# Apply K-means clustering
kmeans = KMeans(n_clusters=num_clusters)
kmeans.fit(lines_array)

# Retrieve cluster labels for each line
cluster_labels = kmeans.labels_

# Separate lines into different groups based on cluster labels
clusters = [[] for _ in range(num_clusters)]
for i, label in enumerate(cluster_labels):
    clusters[label].append(all_lines[i])

# Print the clusters
for i, cluster in enumerate(clusters):
    print(f"Cluster {i+1}:")
    new_doc = ezdxf.new()
    msp_new = new_doc.modelspace()
    # for line in cluster:
    #     msp.add_line(start=line[0], end=line[1])
    entities_for_cluster = [entity for j, entity in enumerate(msp) if cluster_labels[j] == i]
    for entity in entities_for_cluster:
        recreate_entity_in_msp(entity, msp_new)
    new_doc.saveas(f"decomposed/file{i}.dxf")
