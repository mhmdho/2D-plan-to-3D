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


# Get entities of a specific layer
layer_name = 'FP-Window'
for entity in msp:
    # if entity.dxf.layer == layer_name:
    if entity.dxftype() == 'INSERT' and entity.dxf.layer == layer_name:
        x0 = entity.dxf.insert.x
        y0 = entity.dxf.insert.y
        z0 = entity.dxf.insert.z
        a = (x0, y0, z0)
        print(entity.dxftype())
        print(vars(entity.doc.blocks[entity.dxf.name]))
        block = entity.doc.blocks[entity.dxf.name]
        for e in block:
            if e.dxftype() == 'LINE':
                print('LINE')
            if e.dxftype() == 'LWPOLYLINE':
                print('LWPOLYLINE')
            if e.dxftype() == 'CIRCLE':
                print('CIRCLE')
            if e.dxftype() == 'INSERT':
                print('INSERT')
            print('-------------------------------------------')
            print(vars(e.dxf))
            break
        # print(vars(entity.doc.tables))
        # print('-------------------------------------------')
        # print(vars(entity.doc.rootdict))
        # print('-------------------------------------------')
        # print(vars(entity.doc.header))
        # print('-------------------------------------------')
        # print(vars(entity.doc.classes))
        print('-------------------------------------------')
        break
