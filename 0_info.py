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


# Get a sample data for each dfxtype/layer
mylist = list(myset)
for entity in msp:
    # thefilter = entity.dxftype()
    thefilter = entity.dxf.layer
    if thefilter in mylist:
        print(thefilter)
        print(entity.dxf.all_existing_dxf_attribs())
        mylist.remove(thefilter)
