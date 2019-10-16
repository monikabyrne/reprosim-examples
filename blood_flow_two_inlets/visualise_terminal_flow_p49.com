
#chorionic tree
gfx read node inputs_patient_49/chorionic_tree/p49_large_vessels_v3 reg tree
gfx read elem inputs_patient_49/chorionic_tree/p49_large_vessels_v3 reg tree
gfx read elem inputs_patient_49/chorionic_tree/p49_large_vessel_radius_v3 reg tree

# Create Tree
gfx modify g_element "/" general clear;
gfx modify g_element /tree/ general clear;
gfx modify g_element /tree/ lines domain_mesh1d coordinate coordinates tessellation default LOCAL circle_extrusion line_base_size 0 line_orientation_scale radius line_scale_factors 2 select_on material red selected_material default_selected render_shaded;


#terminal elements - choose one

#no anastomosis - flow bc
gfx read node output_patient_49_het_34k_v2_flow/terminal reg terminals
#anastomosis - flow bc
gfx read node output_patient_49_het_34k_v2_anast_flow/terminal reg terminals



# Create terminal spheres
gfx modify g_element /terminals/ general clear;
gfx modify g_element /terminals/ node_points glyph sphere general size "2*2*2" centre 0,0,0 material default data flow spectrum default selected_material default_selected;


# Modify Spectrum
gfx modify spectrum default autorange;

#create a colour bar
gfx create colour_bar spectrum default
gfx cre mat copper ambient 1 0.2 0 diffuse 0.6 0.3 0 specular 0.7 0.7 0.5 shininess 0.3
gfx modify g_element "/" point glyph colour_bar general size "1*1*1" centre 0,0,0 select_on material copper selected_material copper normalised_window_fit_left;

# Open Windows
gfx cre win
gfx edit sce


