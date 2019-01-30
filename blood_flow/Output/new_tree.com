gfx read nodes full_tree.exnode region skeleton_graph;
gfx read elements full_tree.exelem region skeleton_graph;
gfx modify g_element skeleton_graph lines coordinate coordinates material default;
#gfx modify g_element skeleton_graph element_points coordinate coordinates material orange label cmiss_number;
#gfx modify g_element skeleton_graph node_points coordinate coordinates material green point_size 2 label cmiss_number;


gfx cre win;
gfx edit sce;