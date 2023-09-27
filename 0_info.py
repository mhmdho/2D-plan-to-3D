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


# Save layers to a new file
doc2 = ezdxf.new(dxfversion='R2018')
msp2 = doc2.modelspace()
i = 0
omitlist = []
for entity in msp:
    # if entity.dxftype() in ['WIPEOUT', 'INSERT', 'MTEXT', 'DIMENSION']:
    # if entity.dxftype() == 'HATCH':
        try:
            # print(entity.dxftype())
            # print(entity.dxf.all_existing_dxf_attribs())
            msp2.add_foreign_entity(entity)
        except:
            i += 1
            # doc2.saveas(f"decomposed/clus{i}.dxf")
            # print(vars(entity))
            if entity.dxftype() not in omitlist:
                omitlist.append(entity.dxftype())
            # print(entity.text)

print(i, omitlist)
doc2.saveas(f"decomposed/new{i}.dxf")
