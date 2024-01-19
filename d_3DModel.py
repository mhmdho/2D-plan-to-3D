import os
import ezdxf
import numpy as np
import pyvista as pv
from roof_utilities import extrude_as_gable, extrude_as_gable2, get_all_lines, create_floor_surface
from mesh_utilities import update_layers, get_ScaleFactor_and_Translation, prepare_for_3DViewers, convert_tr_to_d
from mesh_utilities import Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Outline_window, Mesh_Balcony, Mesh_Floors
from dxf_to_pyvista_el import dxf_to_pyvista_line_el, dxf_to_pyvista_polyline_el, dxf_to_pyvista_hatch_el


folder_path = "decomposed"                     # Path to the decomposed folder
BaseHeight = 125.5                             # Height of base floor
WallHeight = 157.25                            # Height of other floors
RoofHeight = 174.4                             # Height of each roof
heights = []
# heights = [125.5, 164.5, 150, 174.4]         # in the case where heights are different for every floor
win_down_perc = .16                            # down height percentage of the windows and doors where there is wall  
win_up_perc = .18                              # up height percentage of the windows and doors where there is wall  

Wall_Texture = pv.Texture('Textures/wall.jpg')
Window_Texture = pv.Texture('Textures/window2.jpg')
Door_Texture = pv.Texture('Textures/door.png')
Roof_Texture = pv.Texture('Textures/roof.jpg')
Stair_Texture = pv.Texture('Textures/stair.jpg')
Balcony_Texture = pv.Texture('Textures/wall.jpg')
Floor_Texture = pv.Texture('Textures/stair.jpg')

Layers = ['Door',    'Wall',    'Roof',    'Stair',   'Window',  'Balcony', 'Floors']                  # Order of Layers 
Colors = ['#694b29', '#FFFFFF', '#787878', '#FFFFFF', '#357EC7', '#FFFFFF', '#FFFFFF']
Textures = [None, None, None, None, None, None, None]
Opacities = [1., 1., 1., 1., 1., 1., 1.]
Texture_Scales = [2, 2, 2, 2, 2, 2, 2]

##########################################################################################################

plan_files = [file for file in os.listdir(folder_path) if file.endswith('.dxf') and file.startswith('plan')]  # List all plan files in the folder
plan_files.sort(reverse=False)
N = len(plan_files)                    # Number of total plan files (floors + roof)

if len(heights)==0:
    heights = [WallHeight for n in range(N)]
    if 'plan_0.dxf' in plan_files:
        heights[0] = BaseHeight
    if 'plan_roof.dxf' in plan_files:
        heights[-1] = RoofHeight

x_translate = np.zeros(N)
y_translate = np.zeros(N)
z_translate = [sum(heights[:n]) for n in range(len(heights))]

for i, plan in enumerate(plan_files):
    
    doc = ezdxf.readfile(os.path.join(folder_path, plan))
    msp = doc.modelspace()
    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    height = heights[i]
    
    #All Plans except last one:
    if i < N-1: 
        update_layers(msp, Translation_Vector, height, win_down_perc, win_up_perc)
        
        # Extruding lower roofs on lower plans: 
        roof_path = f"{folder_path}/{os.path.splitext(plan)[0]}/roof"
        if os.path.exists(roof_path):
            for file in os.listdir(roof_path):
                if file.lower().endswith('.dxf') and file.lower().startswith('roof'):
                    roof_msp = ezdxf.readfile(os.path.join(roof_path, file)).modelspace()
                    roof_translation = [x_translate[i], y_translate[i], z_translate[i+1]]
                    # roof = extrude_as_gable(roof_msp, max_height=RoofHeight, Translation_Vector=roof_translation)
                    roof = extrude_as_gable2(roof_msp, RoofHeight, Translation_Vector=roof_translation, Alpha=65, Betha=65, A=.7, B=.8)
                    Mesh_Roof.append(roof)
          
        print(f'{os.path.splitext(plan)[0]} completed')
        
    #last plan or plan_roof:  
    elif i == N-1:
        if 'plan_roof.dxf' not in plan_files: 
            update_layers(msp, Translation_Vector, height, win_down_perc, win_up_perc)
            print(f'{os.path.splitext(plan)[0]} completed')

            # Draw a flat roof when plan_roof is absent:
            layer_names = ['roof', 'gable', 'شیروانی', 'سقف', 'wal', 'دیوار', 'stair', 'پله', 'door', 'در', 'win', 'پنجره']
            all_top_lines = get_all_lines(msp, Translation_Vector, layer_names)
            roof_surface = create_floor_surface(all_top_lines)
            top_Roof = roof_surface.translate([0, 0, heights[-1]], inplace=False)
        else:
            # top_Roof = extrude_as_gable(msp, max_height=RoofHeight, Translation_Vector=Translation_Vector)
            top_Roof = extrude_as_gable2(msp, RoofHeight, Translation_Vector, Alpha=65, Betha=65, A=.7, B=.8)

        Mesh_Roof.append(top_Roof)
        print(f'roof completed')
        

All_mesh = pv.MultiBlock()
meshes = [Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Balcony, Mesh_Floors]
for mesh in meshes:
    if mesh is not None and len(mesh) > 0:
        All_mesh.append(mesh)
    
##########################################################################################################

plotter = pv.Plotter(notebook=False)
plotter.set_background('#282828')  # Set the background color here

center, scale_factor = get_ScaleFactor_and_Translation(All_mesh, max_boundary=100)

for i,mesh in enumerate(meshes):
    if mesh is not None and len(mesh) > 0:
        mesh = prepare_for_3DViewers(mesh, center=center, scale_factor=scale_factor)
        # mesh = TextureScale(mesh, Texture_Scales[i])
        plotter.add_mesh(mesh, color=Colors[i], texture=Textures[i], opacity=Opacities[i], line_width=2, point_size=0)


####################################################################################################
####################################################################################################
#3d Elevation mapping:
        
Mesh_front = pv.MultiBlock()
Mesh_back = pv.MultiBlock()
Mesh_right = pv.MultiBlock()
Mesh_left = pv.MultiBlock()

Mesh_el = [Mesh_front, Mesh_back, Mesh_right, Mesh_left]

el_files = [file for file in os.listdir(folder_path) if file.endswith('.dxf') and file.startswith('elevation')]  # List all el files in the folder
el_files.sort(reverse=False)
N = len(el_files)                    # Number of total plan files (floors + roof)


Translation_front = [-center[0], -center[2], center[1] + 20]
Translation_back = [center[0], -center[2], center[1] - 20]
Translation_right = [-center[0] - 20, -center[2], center[1]]
Translation_left = [-center[0] + 20, -center[2], center[1]]

Translation_el = [Translation_front, Translation_back, Translation_right, Translation_left]


def msp_to_mesh_el(msp):

    Mesh = pv.MultiBlock()

    for entity in msp:    

        if 'roof' not in entity.dxf.layer.lower():

            if entity.dxftype() == 'LINE':
                mesh = dxf_to_pyvista_line_el(entity)
                Mesh.append(mesh)
                
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                lines = dxf_to_pyvista_polyline_el(entity)
                for line in lines:
                    Mesh.append(line)
                            
            elif entity.dxftype() == 'HATCH':
                all_hatch = dxf_to_pyvista_hatch_el(entity)
                for hatch in all_hatch:
                    Mesh.append(hatch)
    
    return Mesh


def prepare_for_3DViewers_el(mesh, scale_factor, translation_el):
        
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()

    # mesh0 = mesh.copy()
    mesh0 = mesh.tube(radius=.5, n_sides=4, inplace=False, capping=False)
    mesh_centered = mesh0.translate(translation_el)
    transformed_mesh = mesh_centered.scale([scale_factor, scale_factor, scale_factor], inplace=False)
   
    transformed_mesh = transformed_mesh.point_data_to_cell_data()
    transformed_mesh = transformed_mesh.compute_normals()
    transformed_mesh = transformed_mesh.texture_map_to_plane()
    transformed_mesh = transformed_mesh.triangulate()

    return transformed_mesh


for i, el in enumerate(el_files):
    
    doc = ezdxf.readfile(os.path.join(folder_path, el))
    msp = doc.modelspace()

    Mesh = msp_to_mesh_el(msp)
    if Mesh is not None and len(Mesh)>0:
        Mesh_el[i] = Mesh

    Mesh_el[i] = prepare_for_3DViewers_el(Mesh_el[i], scale_factor, Translation_el[i])

    plotter.add_mesh(Mesh_el[i], color='k', texture=None, opacity=1, line_width=0, point_size=0)
    
    print(f'{os.path.splitext(el)[0]} completed')


################################################################################################
################################################################################################

plotter.enable_depth_peeling()
plotter.export_obj('outputOBJ/output.obj')
# plotter.add_axes()
# plotter.show_grid()
plotter.show()
plotter.close()

convert_tr_to_d('outputOBJ/output.mtl')
