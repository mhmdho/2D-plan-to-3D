import os
import ezdxf
import numpy as np
import pyvista as pv
from roof_utilities import extrude_as_gable, extrude_as_gable2, get_all_lines, create_floor_surface
from mesh_utilities import update_layers, get_ScaleFactor_and_Translation, prepare_for_3DViewers, convert_tr_to_d
from mesh_utilities import Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Outline_window, Mesh_Balcony, Mesh_Floors


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

# lightred = (.7, .4, .4)
# Colors = [lightred, 'lightgrey'   , 'lightbrown', 'lightgreen', 'lightblue', '#FFFFFF', '#FFFFFF']
# Colors = ['#694b29', None, None, None, '#357EC7', '#FFFFFF', '#FFFFFF']
# Textures = [None, Wall_Texture, Roof_Texture, Wall_Texture, None, Balcony_Texture, None]
# Colors = [None, None, None, None, None, None, None]
# Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture, Balcony_Texture, Floor_Texture]

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

# if Mesh_Outline_window is not None and len(Mesh_Outline_window) > 0:
#     Mesh_Outline_window = prepare_for_3DViewers(Mesh_Outline_window, center=center, scale_factor=scale_factor)
#     plotter.add_mesh(Mesh_Outline_window, color='blue', line_width=4, point_size=0)

plotter.enable_depth_peeling()
plotter.export_obj('outputOBJ/output.obj')
plotter.add_axes()
plotter.show_grid()
plotter.show()
plotter.close()

convert_tr_to_d('outputOBJ/output.mtl')
