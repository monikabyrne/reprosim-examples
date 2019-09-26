#!/usr/bin/env python
 
#This routine reads in an arterial tree and solves Pressure-Resistance-Flow equations within this tree.
import os
import time
from reprosim.diagnostics import set_diagnostics_level
from reprosim.indices import perfusion_indices, get_ne_radius
from reprosim.geometry import append_units,define_node_geometry, define_1d_elements,define_rad_from_geom,add_matching_mesh, \
        calc_capillary_unit_length,define_rad_from_file,update_1d_elem_field
from reprosim.exports import export_1d_elem_geometry, export_node_geometry, export_1d_elem_field,export_node_field,export_terminal_perfusion
from reprosim.pressure_resistance_flow import evaluate_prq, calculate_stats

def main():
    script_start_time = time.clock()
    set_diagnostics_level(1) #level 0 - no diagnostics; level 1 - only prints subroutine names (default); level 2 - prints subroutine names and contents of variables

    #parameters
    export_directory = 'output_patient_51_two_inlets_anast'
    #input and output file names
    node_in_file = 'inputs_patient_51/two_inlets_anast/full_tree.ipnode'
    elem_in_file = 'inputs_patient_51/two_inlets_anast/full_tree.ipelem'
    elem_out_file = 'full_tree.exelem'
    node_out_file = 'full_tree.exnode'
    flow_gen_file = 'terminal flow per generation.csv' #blood flow by generation will be exported to this file

    two_inlets = True #set to True if the arterial tree contains two umbilical inlet elements
    anastomosis = True #set to True if Hyrt's anastomosis between the umbilical arteries exists in the input arterial tree
    if anastomosis:
        anastomosis_elem = 34636
        override_anast_radius = False #set this to True if you need to override the radius of the anastomosis
        anastomosis_radius = 1
    #mesh_type = 'simple_tree' #'full_plus_tube'  # mesh_type: can be 'simple_tree' or 'full_plus_tube'. Simple_tree is the input
                                  # arterial tree without any special features at the terminal level
                                  # 'full_plus_tube' creates a matching venous mesh and connects arteries and
                                  # veins with capillary units (capillaries are tubes represented by an element)
    mesh_type = 'full_plus_tube'

    if mesh_type == 'full_plus_tube':
        add_venous_vessels = True

    if add_venous_vessels:
        #set umbilical_elem_option to either 'single_umbilical_vein' (replace 2 umbilical arteries with a single vein)
        # or 'same_as_arterial'
        umbilical_elem_option = 'single_umbilical_vein'
        umbilical_elements = [1, 2, 3, 34636, 34637, 34638, 34639]

        num_convolutes = 6  # number of terminal convolute connections
        num_generations = 3  # number of generations of symmetric intermediate villous trees

    # parameters used to assign vessel radii

    #radius_from_file = True  #if False, vessel radii are based on vessel geometry, ordering system and diameter ratio
    # if True available arterial vessel radii are read in, while the remaining arterial vessel radii are calculated
    radius_from_file = True
    if radius_from_file:
        radius_in_file = 'inputs_patient_51/two_inlets_anast/full_tree_radius_anast.ipfiel'
    else:
        umbilical_artery_radius = 1.8

    order_system = 'strahler'
    arterial_diameter_ratio = 1.425 #rate of decrease in radius at each order of the arterial tree
    umbilical_vein_radius = 4.0
    venous_diameter_ratio = 1.51  #rate of decrease in radius at each order of the venous tree

    #boundary conditions: pressure at the outlet (umbilical vein) and pressure or volumetric blood flow at the inlet(s)
    bc_type = 'pressure' # 'pressure' or 'flow'
    if  bc_type == 'pressure':
        inlet_pressure = 6650 #Pa (~50mmHg)
        outlet_pressure = 2660 #Pa (~20mmHg)
        inlet_flow = 0 #set to 0 for bc_type = pressure;

    if  bc_type == 'flow':
        inlet_pressure = 0
        outlet_pressure = 2660 #Pa (~20mmHg)
        # 250 ml/min (21% of the fetal cardiac output) 0.06 ml/min = 1 mm3/s
        inlet_flow = 4166.7 # mm3/s #total flow for all umbilical arteries

    #this parameter is used to calculate the volume of vessels in the reconstructed tree that can't be
    #resolved in the images
    # set to 0 if not using
    image_voxel_size = 0.1165     #0.1165 #mm


    #print all script parameters to console
    script_params = locals()
    print("Blood flow simulation parameters:")

    for key in sorted(script_params.keys()):
        if key != 'script_params':
            print(key + " = " + str(script_params[key]))

    if not os.path.exists(export_directory):
        os.makedirs(export_directory)

    # save parameters to text file
    fo = open(export_directory + '/script_parameters.txt', "w")
    for key in sorted(script_params.keys()):
        if key != 'script_params':
            fo.write(key + " = " + str(script_params[key]) + '\n')
    fo.close()

    #define model geometry and indices
    perfusion_indices()

    #define_node_geometry('bigger_umb_art.ipnode')
    define_node_geometry(node_in_file)
    if anastomosis:
        define_1d_elements(elem_in_file,anastomosis_elem)
    else:
        define_1d_elements(elem_in_file)


    #define terminal units (this subroutine always needs to be called regardless of mesh_type
    append_units()

    if add_venous_vessels:
        #creates a mesh that converges (a venous mesh)
        add_matching_mesh(umbilical_elem_option,umbilical_elements)

    if radius_from_file:
        define_rad_from_file(radius_in_file, order_system, arterial_diameter_ratio)
    else:
        order_options = 'arterial'
        name = 'inlet'
        define_rad_from_geom(order_system, arterial_diameter_ratio, name, umbilical_artery_radius, order_options, '')

    if(anastomosis and override_anast_radius):
        ne_radius = get_ne_radius()
        update_1d_elem_field(ne_radius,anastomosis_elem,anastomosis_radius)


    if add_venous_vessels:
        #defines radius by Strahler order in converging (venous mesh)
        order_options = 'venous'
        define_rad_from_geom(order_system, venous_diameter_ratio, '', umbilical_vein_radius, order_options,'')

        calc_capillary_unit_length(num_convolutes,num_generations)


    # Call solve
    if (two_inlets and bc_type == 'flow'):
            inlet_flow = inlet_flow/2.0

    evaluate_prq(mesh_type,bc_type,inlet_flow,inlet_pressure,outlet_pressure)

    calculate_stats(export_directory + '/' + flow_gen_file, image_voxel_size)

    ##export geometry
    group_name = 'perf_model'
    export_1d_elem_geometry(export_directory + '/' + elem_out_file, group_name)
    export_node_geometry(export_directory + '/' + node_out_file, group_name)

    # export element field for radius
    field_name = 'radius_perf'
    ne_radius = get_ne_radius()
    export_1d_elem_field(ne_radius, export_directory + '/radius_perf.exelem', field_name, field_name)
   
    # export flow in each element
    filename = export_directory + '/flow_perf.exelem'
    field_name = 'flow'
    export_1d_elem_field(7,filename, group_name, field_name)
 
    #export node field for pressure
    filename= export_directory + '/pressure_perf.exnode'
    field_name = 'pressure_perf'
    export_node_field(1, filename, group_name, field_name)
   
    # Export terminal solution
    export_terminal_perfusion(export_directory + '/terminal.exnode', group_name)
    elapsed = time.clock()
    elapsed = elapsed - script_start_time
    print "Time spent solving is: ", elapsed
 
 
if __name__ == '__main__':
    main()