#!/usr/bin/env python
 
#This routine reads in an arterial tree and solves Pressure-Resistance-Flow equations within this tree.
import time
from reprosim.diagnostics import set_diagnostics_level
from reprosim.indices import perfusion_indices, get_ne_radius
from reprosim.geometry import append_units,define_node_geometry, define_1d_elements,define_rad_from_geom,add_matching_mesh, \
        calc_capillary_unit_length,define_rad_from_file
from reprosim.exports import export_1d_elem_geometry, export_node_geometry, export_1d_elem_field,export_node_field,export_terminal_perfusion
from reprosim.pressure_resistance_flow import evaluate_prq

def main():
    start = time.clock()
    set_diagnostics_level(1) #level 0 - no diagnostics; level 1 - only prints subroutine names (default); level 2 - prints subroutine names and contents of variables
 
    #define model geometry and indices
    perfusion_indices()
 
    #Read in geometry files
    #define_node_geometry('Small.ipnode')
    #define_1d_elements('Small.ipelem')
    #define_node_geometry('Bigger.ipnode')
    #define_1d_elements('Bigger.ipelem')
    define_node_geometry('bigger_umb_art.ipnode')
    define_1d_elements('bigger_umb_art.ipelem')
    #define_node_geometry('bigger_venous.ipnode')
    #define_1d_elements('bigger_venous.ipelem')
    #define_1d_elements('Bigger_reordered_elems.ipelem')
    #define_node_geometry('full_tree.ipnode')
    #define_1d_elements('full_tree.ipelem')
    #define_node_geometry('new_nodes_v10.ipnode')
    #define_1d_elements('new_elems_v10.ipelem')
    #define_node_geometry('chor_nodes_cycle2_v7.ipnode')
    #define_1d_elements('chor_elems_cycle2_v6.ipelem')
    #define_node_geometry('full_tree_patient_51.ipnode')
    #define_1d_elements('full_tree_patient_51.ipelem')

    mesh_type = 'full_plus_tube'
    #mesh_type = 'simple_tree' #'full_plus_tube'  # mesh_type: can be 'simple_tree' or 'full_plus_tube'. Simple_tree is the input
                                  # arterial tree without any special features at the terminal level
                                  # 'full_plus_tube' creates a matching venous mesh and has arteries and
                                  # veins connected by capillary units (capillaries are just tubes represented by an element)
    add_venous_vessels = False
    if mesh_type == 'full_plus_tube':
        add_venous_vessels = True

    radius_from_file = False  #if False, the radius is based on vessel geometry

    #define terminal units (this subroutine always needs to be called regardless of mesh_type
    append_units()

    if add_venous_vessels:
        #creates a mesh that converges (a venous mesh)

        umbilical_elem_option = 'single_umbilical_vein' #replace 2 umbilical arteries with a single vein
        #umbilical_elem_option = 'same_as_arterial'
        add_matching_mesh(umbilical_elem_option,'umbilical_elements.txt')

        if radius_from_file:
            #only arterial chorionic radii were calculated from images, radii for smaller vessels will be calculated
            order_system = 'strahler'
            s_ratio = 1.54
            define_rad_from_file('chorionic_vessel_radii_cycle2_v3.ipfiel', order_system, s_ratio)
            #define_rad_from_file('bigger_umb_art.ipfiel', order_system, s_ratio)

            #defines radius by Strahler order in converging (venous mesh)
            s_ratio_ven=1.55 #rate of decrease in radius at each order of the venous tree
            inlet_rad_ven=5.0 #inlet radius
            order_system = 'strahler'
            order_options = 'venous'
            first_ven_no='' #number of elements read in plus one
            last_ven_no='' #2x the original number of elements + number of connections
            define_rad_from_geom(order_system, s_ratio_ven, first_ven_no, inlet_rad_ven, order_options,last_ven_no)

        else:

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

        num_convolutes = 6  # number of terminal convolute connections
        num_generations = 3  # number of generations of symmetric intermediate villous trees
        calc_capillary_unit_length(num_convolutes,num_generations)

    else:

        if radius_from_file:
            order_system = 'strahler'
            s_ratio = 1.54
            define_rad_from_file('chorionic_vessel_radii_cycle2_v3.ipfiel', order_system, s_ratio)
            #define_rad_from_file('bigger_umb_art.ipfiel', order_system, s_ratio)

        else:
            # define radius by Strahler order
            s_ratio = 1.54  # rate of decrease in radius at each order of the arterial tree
            inlet_rad = 3.0  # inlet radius
            order_system = 'strahler'
            order_options = 'all'
            name = 'inlet'
            define_rad_from_geom(order_system, s_ratio, name, inlet_rad, order_options, '')

 
    #Call solve
    bc_type = 'pressure' # 'pressure' or 'flow'
    if  bc_type == 'pressure':
        inlet_pressure = 6650 #Pa (~50mmHg)
        outlet_pressure = 2660 #Pa (~20mmHg)
        inlet_flow = 0 #set to 0 for bc_type = pressure;

    if  bc_type == 'flow':
        inlet_pressure = 0
        outlet_pressure = 2660
        inlet_flow = 111666.7 # mm3/s
        #set to 0 for bc_type = pressure; small tree: 111666.7 without capillary resistance !9branches plus venous;  win's tree
        #250 ml/min (21% of the fetal cardiac output) 0.06 ml/min = 1 mm3/s

    evaluate_prq(mesh_type,bc_type,inlet_flow,inlet_pressure,outlet_pressure)
 
    ##export geometry
    group_name = 'perf_model'
    #export_1d_elem_geometry('Output/small.exelem', group_name)
    #export_node_geometry('Output/small.exnode', group_name)
    #export_1d_elem_geometry('Output/bigger.exelem', group_name)
    #export_node_geometry('Output/bigger.exnode', group_name)
    export_1d_elem_geometry('Output/bigger_umb_art.exelem', group_name)
    export_node_geometry('Output/bigger_umb_art.exnode', group_name)
    #export_1d_elem_geometry('Output/bigger_venous.exelem', group_name)
    #export_node_geometry('Output/bigger_venous.exnode', group_name)
    #export_1d_elem_geometry('Output/full_tree.exelem', group_name)
    #export_node_geometry('Output/full_tree.exnode', group_name)
    #export_1d_elem_geometry('Output/new_elems_v10.exelem', group_name)
    #export_node_geometry('Output/new_nodes_v10.exnode', group_name)
    #export_1d_elem_geometry('Output/chor_tree.exelem', group_name)
    #export_node_geometry('Output/chor_tree.exnode', group_name)
    #export_1d_elem_geometry('Output/patient_51.exelem', group_name)
    #export_node_geometry('Output/patient_51.exnode', group_name)

    # export element field for radius
    field_name = 'radius_perf'
    ne_radius = get_ne_radius()
    export_1d_elem_field(ne_radius, 'Output/radius_perf.exelem', field_name, field_name)
   
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