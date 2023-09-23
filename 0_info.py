import ezdxf


doc = ezdxf.readfile('inputDXF/1.dxf')
# print(doc.dxfversion)


# Get all layers and their names
layers = doc.layers
layer_names = [layer.dxf.name for layer in layers]
# print(layer_names)


# Get all entity's dxftype/layer
myset = set()
msp = doc.modelspace()
for entity in msp:
    # myset.add(entity.dxftype())
    myset.add(entity.dxf.layer)
print(myset)
