import ezdxf


the_info = 'types'
# the_info = 'layers'


doc = ezdxf.readfile('inputDXF/1.dxf')
print('DXF version: ', doc.dxfversion, '\n')


# Get all layers and their names
layers = doc.layers
layer_names = [layer.dxf.name for layer in layers]
print('All layers names: ', layer_names, '\n')


# Get a sample data for each dfxtype/layer
myList = list()
msp = doc.modelspace()
for entity in msp:
    if the_info == 'types':
        thefilter = entity.dxftype()
    elif the_info == 'layers':
        thefilter = entity.dxf.layer
    
    if not thefilter in myList:
        print(thefilter)
        print(entity.dxf.all_existing_dxf_attribs())
        myList.append(thefilter)


# Get all used dxftypes/layers
print(f'\nProject {the_info}: ', myList, '\n')


print('======================================================')


# Query for all LINE entities in modelspace
for e in msp.query("LINE"):
    print("Start point: %s\n" % e.dxf.start)
    print("End point: %s\n" % e.dxf.end)

# Query for LINE entities with specific layer name
entities_on_layer = msp.query(f'LINE[layer=="FP-Window"]')


# Save layers to a new file
doc2 = ezdxf.new(dxfversion='R2018')
msp2 = doc2.modelspace()

i = 0
omitted = set()
for entity in msp:
    # if entity.dxftype() in ['WIPEOUT', 'INSERT', 'MTEXT', 'DIMENSION']:
    # if entity.dxftype() == 'HATCH':
        try:
            # print(entity.dxftype())
            # print(entity.dxf.all_existing_dxf_attribs())
            msp2.add_foreign_entity(entity)
        except:
            i += 1
            omitted.add(entity.dxftype())
            # print(vars(entity))
            # print(entity.text)

print('\nNumber of omitted entities: ', i, omitted, '\n')
doc2.saveas(f"decomposed/new{i}.dxf")


# Get entities of a specific layer with insert type
layer_name = 'FP-Window'
for entity in msp:
    # if entity.dxf.layer == layer_name:
    if entity.dxftype() == 'INSERT' and entity.dxf.layer == layer_name:
        x0 = entity.dxf.insert.x
        y0 = entity.dxf.insert.y
        z0 = entity.dxf.insert.z
        a = (x0, y0, z0)
        block = entity.doc.blocks[entity.dxf.name]
        print(entity.dxftype())
        print('vars: ', vars(block))
        for e in block:
            print('-------------------------------------------')
            if e.dxftype() == 'LINE': #'LWPOLYLINE': / 'CIRCLE': / 'INSERT':
                print(f'\t{e.dxftype()}', 'in insert')
                print('\tvars: ', vars(e.dxf))
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

# terminal: python info.py > output.txt
