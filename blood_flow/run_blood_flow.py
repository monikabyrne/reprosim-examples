#!/usr/bin/env python
 
#This routine reads in an arterial tree and solves Pressure-Resistance-Flow equations within this tree.
import time
from reprosim.diagnostics import set_diagnostics_level
from reprosim.indices import perfusion_indices, get_ne_radius
from reprosim.geometry import append_units,define_node_geometry, define_1d_elements,define_rad_from_geom,add_matching_mesh
from reprosim.exports import export_1d_elem_geometry, export_node_geometry, export_1d_elem_field,export_node_field,export_terminal_perfusion
from reprosim.pressure_resistance_flow import evaluate_prq

def main():
    start = time.clock()
    set_diagnostics_level(2) #level 0 - no diagnostics; level 1 - only prints subroutine names (default); level 2 - prints subroutine names and contents of variables
 
    #define model geometry and indices
    perfusion_indices()
 
    #Read in geometry files
    define_node_geometry('Bigger.ipnode')
    define_1d_elements('Bigger.ipelem')

    mesh_type = 'full_plus_tube'
    #mesh_type = 'simple_tree' #'full_plus_tube'  # mesh_type: can be 'simple_tree' or 'full_plus_tube'. Simple_tree is the input
                                  # arterial tree without any special features at the terminal level
                                  # 'full_plus_tube' creates a matching venous mesh and has arteries and
                                  # veins connected by capillary units (capillaries are just tubes represented by an element)
    add_venous_vessels = False
    if mesh_type == 'full_plus_tube':
        add_venous_vessels = True

    if add_venous_vessels:
        #defines capillaries
        append_units()
        #creates a mesh that converges (a venous mesh)
        add_matching_mesh()

    if add_venous_vessels:
        # define radius by Strahler order in diverging (arterial mesh)
        s_ratio = 1.54  # rate of decrease in radius at each order of the arterial tree
        inlet_rad = 3.0  # inlet radius
        order_system = 'strahler'
        order_options = 'arterial'
        name = 'inlet'
        define_rad_from_geom(order_system, s_ratio, name, inlet_rad, order_options, '')

        #defines radius by STrahler order in converging (venous mesh)
        s_ratio_ven=1.55 #rate of decrease in radius at each order of the venous tree
        inlet_rad_ven=5.0 #inlet radius
        order_system = 'strahler'
        order_options = 'venous'
        first_ven_no='' #number of elements read in plus one
        last_ven_no='' #2x the original number of elements + number of connections
        define_rad_from_geom(order_system, s_ratio_ven, first_ven_no, inlet_rad_ven, order_options,last_ven_no)
    else:
        # define radius by Strahler order
        s_ratio = 1.54  # rate of decrease in radius at each order of the arterial tree
        inlet_rad = 3.0  # inlet radius
        order_system = 'strahler'
        order_options = 'all'
        name = 'inlet'
        define_rad_from_geom(order_system, s_ratio, name, inlet_rad, order_options, '')
 
    #Call solve
    bc_type = 'pressure' # 'pressure' or 'flow' if flow, set variable inlet_flow
    inlet_flow = 0 #set to 0 for pressure; inlet_flow=37222 !3branches + venous;  inlet_flow=17346 !9branches plus venous; inlet_flow=1025.8 win's tree
    evaluate_prq(mesh_type,bc_type,inlet_flow)
 
    ##export geometry
    group_name = 'perf_model'
    export_1d_elem_geometry('Output/bigger.exelem', group_name)
    export_node_geometry('Output/bigger.exnode', group_name)

    # export element field for radius
    field_name = 'radius_perf'
    ne_radius = get_ne_radius()
    export_1d_elem_field(ne_radius, 'Output/radius_perf.exelem', name, field_name)
   
    # export flow in each element
    filename = 'Output/flow_perf.exelem'
    field_name = 'flow'
    export_1d_elem_field(7,filename, group_name, field_name)
 
 
    #export node field for pressure
    filename='Output/pressure_perf.exnode'
    field_name = 'pressure_perf'
    export_node_field(1, filename, group_name, field_name)
   
    # Export terminal solution
    export_terminal_perfusion('Output/terminal.exnode', group_name)
    elapsed = time.clock()
    elapsed = elapsed - start
    print "Time spent solving is: ", elapsed
 
 
if __name__ == '__main__':
    main()
