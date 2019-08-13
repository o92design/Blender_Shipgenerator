bl_info = {
    "name": "Shipgenerator Hull",
    "author": "Oskar Månsson (KiOskars)",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Add",
    "description": "Creates a ship hull surface",
    "warning": "",
    "wiki_url": "",
    "category": "Add Surface",
}

import logging
import bpy
import random

from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    PropertyGroup,
    Object
)

from bpy.props import (IntProperty)


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)-15s | %(name)s-%(levelname)s]:%(message)s')

for name in ('blender_id', 'blender_cloud'):
    logging.getLogger(name).setLevel(logging.DEBUG)


class SHIPGENERATOR_OT_hull(Operator):
    bl_label = "Shipgenerator hull"
    bl_idname = "shipgenerator.hull"
    bl_description = "Create a hull surface"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    width: IntProperty(
        name="Hull Width",
        default=4,
        min=0,
        max=15,
        description="Used as a width property"
    )

    seed: IntProperty(
        name="Generational Seed",
        default=1,
        min=-99999999,
        max=99999999,
        description="Used for randomizing the seed of generation"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def create_surface(self,
                       context,
                       p_name: str,
                       p_location: [float, float, float],
                       p_collection=None,
                       p_parent: Object = None):
        bpy.ops.surface.primitive_nurbs_surface_surface_add()
        new_surface = context.object
        new_surface.name = p_name
        new_surface.location = p_location
        new_surface.parent = p_parent

        new_surface.data.splines[0].use_endpoint_u = True
        new_surface.data.splines[0].use_endpoint_v = True
        new_surface.data.splines[0].use_smooth = False

        self.set_random_positions(new_surface, 0, 0, 0)

        if p_collection is not None:
            context.collection.objects.unlink(new_surface)
            p_collection.objects.link(new_surface)

        return new_surface

    def get_point_y_z(self,
                      p_surface,
                      p_z_row: int,
                      p_y_column: int,
                      p_width: int):
        index = p_y_column * p_width + p_z_row
        return p_surface.data.splines[0].points[index]

    def get_point_index(p_surface,
                        p_index: int):
        return p_surface.data.splines[0].points[p_index]

    def set_random_positions(self,
                             p_surface: bpy.types.SurfaceCurve,
                             p_min_x: int,
                             p_max_x: int,
                             p_seed: int,
                             p_y_offset=2,
                             p_z_offset=2):
        y_start = 0

        row_x = [p_min_x, p_min_x, p_min_x, p_min_x]
        if p_min_x != p_max_x:
            logging.info("Will Randomize X position")

            random.seed(p_seed)

            row_x = [0,
                     random.randrange(p_min_x, p_max_x),
                     random.randrange(p_min_x, p_max_x),
                     random.randrange(p_min_x, p_max_x)]

        row_index = 0
        for point in p_surface.data.splines[0].points:
            position = point.co

            position[0] = row_x[row_index]
            position[1] = y_start
            position[2] = p_z_offset * row_index

            if row_index < 3:
                row_index += 1
            else:
                row_index = 0
                y_start += p_y_offset


    def set_column_points_to_position(self,
                                      p_surface,
                                      p_y: int,
                                      p_width: int,
                                      p_position: []):
        for z_index in range(0, p_width):
            point = self.get_point_y_z(p_surface, z_index, p_y, p_width)
            point.co = p_position[z_index]

    def get_column_points_positions(self,
                                    p_surface,
                                    p_y: int,
                                    p_width: int):
        points_position = []
        for row_index in range(0, p_width):
            point = self.get_point_y_z(p_surface, row_index, p_y, p_width)
            points_position.append(point.co)

        return points_position

    def execute(self, context):
        hull_collection = bpy.data.collections.new('Hull')
        context.scene.collection.children.link(hull_collection)

        surface = self.create_surface(context,
                                      "Hull_Main_Stern",
                                      [0.0, 0.0, 0.0],
                                      hull_collection)

        self.set_random_positions(surface,
                                  3,
                                  6,
                                  self.seed,
                                  3,
                                  2)

        surface_two = self.create_surface(context,
                                          "Hull_Main_Bow",
                                          [0.0, 9.0, 0.0],
                                          hull_collection,
                                          surface)

        for column_index in range(0, 4):
            surface_positions = self.get_column_points_positions(surface, column_index, 4)

            self.set_column_points_to_position(surface_two,
                                               column_index,
                                               4,
                                               surface_positions)

        surface_bow = self.create_surface(context,
                                          "Hull_Bow",
                                          [0, 18, 0],
                                          hull_collection,
                                          surface)

        self.set_random_positions(surface_bow,
                                  3,
                                  6,
                                  self.seed,
                                  random.randrange(2, 7),
                                  2)

        surface_positions = self.get_column_points_positions(surface, 0, 4)

        self.set_column_points_to_position(surface_bow,
                                           0,
                                           4,
                                           surface_positions)

        self.set_column_points_to_position(surface_bow,
                                           3,
                                           4,
                                           [(0, 16, 1, 1),
                                            (0, 17, 3, 1),
                                            (0, 18, 4, 1),
                                            (0, 18, 6, 1)])

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SHIPGENERATOR_OT_hull.bl_idname)


def register():
    bpy.utils.register_class(SHIPGENERATOR_OT_hull)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(SHIPGENERATOR_OT_hull)


if __name__ == "__main__":
    register()
