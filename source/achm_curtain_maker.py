# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------------------
# Automatic generation of curtains
# Author: Antonio Vazquez (antonioya)
#
# ----------------------------------------------------------
# noinspection PyUnresolvedReferences
import bpy
import bmesh
from copy import copy
from math import cos, sin, radians
from bpy.types import Operator, PropertyGroup, Object, Panel, Material
from bpy.props import BoolProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty, \
    CollectionProperty
from .achm_tools import *


# ------------------------------------------------------------------
# Define UI class
# Japanese curtains
# ------------------------------------------------------------------
class ARCHIMESH_OT_Japan(Operator):
    bl_idname = "mesh.archimesh_japan"
    bl_label = "Japanese curtains"
    bl_description = "Japanese curtains Generator"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(
            name='Width',
            min=0.30, max=4, default=1, precision=3,
            description='Total width',
            )
    height: FloatProperty(
            name='Height',
            min=0.20, max=50, default=1.8, precision=3,
            description='Total height',
            )
    num: IntProperty(
            name='Rails',
            min=2, max=5, default=2,
            description='Number total of rails',
            )
    palnum: IntProperty(
            name='Panels',
            min=1, max=2, default=1,
            description='Panels by rail',
            )

    open01: FloatProperty(
            name='Position 01',
            min=0, max=1, default=0, precision=3,
            description='Position of the panel',
            )
    open02: FloatProperty(
            name='Position 02',
            min=0, max=1, default=0, precision=3,
            description='Position of the panel',
            )
    open03: FloatProperty(
            name='Position 03',
            min=0, max=1, default=0, precision=3,
            description='Position of the panel',
            )
    open04: FloatProperty(
            name='Position 04',
            min=0, max=1, default=0, precision=3,
            description='Position of the panel',
            )
    open05: FloatProperty(
            name='Position 05',
            min=0, max=1, default=0, precision=3,
            description='Position of the panel',
            )

    # Materials
    crt_mat: BoolProperty(
            name="Create default Cycles materials",
            description="Create default materials for Cycles render",
            default=True,
            )

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        space = bpy.context.space_data
        if not space.local_view:
            # Imperial units warning
            if bpy.context.scene.unit_settings.system == "IMPERIAL":
                row = layout.row()
                row.label(text="Warning: Imperial units not supported", icon='COLOR_RED')

            box = layout.box()
            row = box.row()
            row.prop(self, 'width')
            row.prop(self, 'height')
            row = box.row()
            row.prop(self, 'num')
            row.prop(self, 'palnum')

            if self.num >= 1:
                row = box.row()
                row.prop(self, 'open01', slider=True)
            if self.num >= 2:
                row = box.row()
                row.prop(self, 'open02', slider=True)
            if self.num >= 3:
                row = box.row()
                row.prop(self, 'open03', slider=True)
            if self.num >= 4:
                row = box.row()
                row.prop(self, 'open04', slider=True)
            if self.num >= 5:
                row = box.row()
                row.prop(self, 'open05', slider=True)

            box = layout.box()
            if not context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
                box.enabled = False
            box.prop(self, 'crt_mat')
            if self.crt_mat:
                box.label(text="* Remember to verify fabric texture folder")
        else:
            row = layout.row()
            row.label(text="Warning: Operator does not work in local view mode", icon='ERROR')

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    # noinspection PyUnusedLocal
    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            create_japan_mesh(self)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}


# ------------------------------------------------------------------------------
# Generate mesh data
# All custom values are passed using self container (self.myvariable)
# ------------------------------------------------------------------------------
def create_japan_mesh(self):
    # deactivate others
    for o in bpy.data.objects:
        if o.select_get() is True:
            o.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    # Create units
    generate_japan(self)

    return


# ------------------------------------------------------------------
# Define operator class to create object
# Roller curtains
# ------------------------------------------------------------------
class ARCHIMESH_OT_Roller(Operator):
    bl_idname = "mesh.archimesh_roller"
    bl_label = "Roller curtains"
    bl_description = "Roller_curtains Generator"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Use Properties panel (N) to define parms", icon='INFO')

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            create_roller_object(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}


# ------------------------------------------------------------------------------
# Create main object (the roller tube). The other parts are children of it.
# ------------------------------------------------------------------------------
def create_roller_object(context):
    for o in bpy.data.objects:
        o.select_set(False)

    mainmesh = bpy.data.meshes.new("Roller")
    mainobject = bpy.data.objects.new("Roller", mainmesh)
    mainobject.location = context.scene.cursor.location
    context.collection.objects.link(mainobject)
    mainobject.RollerObjectGenerator.add()

    shape_roller_and_create_children(mainobject, mainmesh)

    mainobject.select_set(True)
    context.view_layer.objects.active = mainobject


# ------------------------------------------------------------------------------
# Rebuild the roller after a geometry or material-flag change
# ------------------------------------------------------------------------------
# noinspection PyUnusedLocal
def update_roller(self, context):
    # The property group belongs to the main object, so this works whether the
    # edit comes from the sidebar or from a script on a non-active object.
    o = self.id_data
    kept_materials = capture_materials([o] + list(o.children_recursive))
    oldmesh = o.data
    oldname = o.data.name
    tmp_mesh = bpy.data.meshes.new("temp")
    for obj in bpy.data.objects:
        obj.select_set(False)

    for child in o.children:
        remove_children(child)
    remove_children(o)

    shape_roller_and_create_children(o, tmp_mesh)
    o.data = tmp_mesh
    restore_materials([o] + list(o.children_recursive), kept_materials)
    bpy.data.meshes.remove(oldmesh)
    tmp_mesh.name = oldname

    o.select_set(True)
    bpy.context.view_layer.objects.active = o


# Color and opacity only touch the roller's own materials, so they skip the
# rebuild. Rebuilding would also bring back the captured material, undoing the
# change (see restore_materials).
# noinspection PyUnusedLocal
def update_roller_fabric(self, context):
    apply_roller_fabric(self)


# ------------------------------------------------------------------
# Define property group class to create or modify
# ------------------------------------------------------------------
class RollerProperties(PropertyGroup):
    width: FloatProperty(
            name='Width',
            min=0.30, max=4, default=1, precision=3,
            description='Total width', update=update_roller,
            )
    height: FloatProperty(
            name='Height',
            min=0.01, max=50, default=1.7, precision=3,
            description='Fabric drop when fully lowered', update=update_roller,
            )
    ratio: IntProperty(
            name='Extend', min=0, max=100, default=100,
            description='% of the drop that is unrolled (100 fully lowered)', update=update_roller,
            )

    # Materials
    crt_mat: BoolProperty(
            name="Create default Cycles materials",
            description="Create default materials for Cycles render",
            default=True, update=update_roller,
            )
    objcol: FloatVectorProperty(
            name="Color",
            description="Fabric color",
            default=(0.653, 0.485, 0.265, 1.0),
            min=0, max=1,
            subtype='COLOR',
            size=4, update=update_roller_fabric,
            )
    opacity: FloatProperty(
            name='Opacity', min=0, max=1, default=0.8, precision=2, subtype='FACTOR',
            description='How much light the fabric blocks (0 sheer, 1 blackout)',
            update=update_roller_fabric,
            )
    # Each roller owns its fabric materials so color and opacity are per curtain.
    # Shared by-name materials would recolor every roller in the file at once.
    fabric: PointerProperty(type=Material)
    fabric_solid: PointerProperty(type=Material)


bpy.utils.register_class(RollerProperties)
Object.RollerObjectGenerator = CollectionProperty(type=RollerProperties)


# ------------------------------------------------------------------
# Define panel class to modify object
# ------------------------------------------------------------------
class ARCHIMESH_PT_RollerObjectgenerator(Panel):
    bl_idname = "OBJECT_PT_roller_generator"
    bl_label = "Roller curtain"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Create'

    @classmethod
    def poll(cls, context):
        o = context.object
        return o is not None and len(o.RollerObjectGenerator) > 0

    def draw(self, context):
        layout = self.layout
        if context.mode == 'EDIT_MESH':
            layout.label(text='Warning: Operator does not work in edit mode.', icon='ERROR')
            return
        if context.space_data.local_view:
            layout.label(text="Warning: Operator does not work in local view mode", icon='ERROR')
            return

        rp = context.object.RollerObjectGenerator[0]
        if context.scene.unit_settings.system == "IMPERIAL":
            row = layout.row()
            row.label(text="Warning: Imperial units not supported", icon='COLOR_RED')

        box = layout.box()
        row = box.row()
        row.prop(rp, 'width')
        row.prop(rp, 'height')
        row = box.row()
        row.prop(rp, 'ratio', slider=True)

        box = layout.box()
        if context.scene.render.engine not in {'CYCLES', 'BLENDER_EEVEE'}:
            box.enabled = False
        box.prop(rp, 'crt_mat')
        if rp.crt_mat:
            row = box.row()
            row.prop(rp, 'objcol')
            row = box.row()
            row.prop(rp, 'opacity', slider=True)


# ------------------------------------------------------------------------------
# Generate japanese curtains
# All custom values are passed using self container (self.myvariable)
# ------------------------------------------------------------------------------
def generate_japan(self):
    support = []
    panel = []

    location = bpy.context.scene.cursor.location
    myloc = copy(location)  # copy location to keep 3D cursor position

    # ------------------
    # Rail
    # ------------------
    myrail = create_japan_rail("Rail",
                               self.width - 0.02, self.num,
                               myloc.x, myloc.y, myloc.z,
                               self.crt_mat)
    # refine
    remove_doubles(myrail)
    set_normals(myrail)

    # --------------------------------------------------------------------------------
    # Supports
    # --------------------------------------------------------------------------------
    width = (self.width / self.num) / self.palnum
    # left
    posx = 0.01 + 0.01
    posy = 0.006
    posz = 0.006
    for x in range(self.num):
        mysup = create_japan_support("Support_" + str(x) + ".L",
                                     width - 0.02,    # subtract 2 cm
                                     0, 0, 0,
                                     self.crt_mat)
        support.extend([mysup])
        mysup.parent = myrail

        if x == 0:
            f = self.open01
        if x == 1:
            f = self.open02
        if x == 2:
            f = self.open03
        if x == 3:
            f = self.open04
        if x == 4:
            f = self.open05

        if self.palnum == 1:
            maxpos = ((self.width / self.palnum) - width - 0.02) * f
        else:
            maxpos = ((self.width / self.palnum) - width) * f

        mysup.location.x = posx + maxpos
        mysup.location.y = -posy
        mysup.location.z = posz

        posy += 0.015
    # Right
    if self.palnum > 1:
        posx = self.width - width  # + 0.01
        posy = 0.006
        posz = 0.006
        for x in range(self.num):
            mysup = create_japan_support("Support_" + str(x) + ".R",
                                         width - 0.02,   # subtract 2 cm
                                         0, 0, 0,
                                         self.crt_mat)
            support.extend([mysup])
            mysup.parent = myrail

            if x == 0:
                f = self.open01
            if x == 1:
                f = self.open02
            if x == 2:
                f = self.open03
            if x == 3:
                f = self.open04
            if x == 4:
                f = self.open05

            maxpos = ((self.width / self.palnum) - width) * f

            mysup.location.x = posx - maxpos
            mysup.location.y = -posy
            mysup.location.z = posz

            posy += 0.015
    # --------------------------------------------------------------------------------
    # Panels
    # --------------------------------------------------------------------------------
    width = ((self.width / self.num) / self.palnum) + 0.01
    posx = -0.01
    posy = -0.006
    posz = -0.008
    x = 1
    fabricmat = None
    if self.crt_mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
        fabricmat = create_fabric_material("Fabric_material", False, 0.653, 0.485, 0.265,
                                           0.653, 0.485, 0.265)

    for sup in support:
        mypanel = create_japan_panel("Panel_" + str(x),
                                     width, self.height,
                                     0, 0, 0,
                                     self.crt_mat, fabricmat)
        panel.extend([mypanel])
        mypanel.parent = sup
        mypanel.location.x = posx
        mypanel.location.y = posy
        mypanel.location.z = posz
        x += 1
    # ------------------------
    # Strings
    # ------------------------
    x = myrail.location.x
    y = myrail.location.y
    z = myrail.location.z

    long = -1
    if self.height < 1:
        long = -self.height

    myp = [((0, 0, 0), (- 0.25, 0, 0), (0.0, 0, 0)),
           ((0, 0, long), (- 0.01, 0, long), (0.25, 0, long))]  # double element
    mycurve1 = create_bezier("String_1", myp, (x, y, z))
    mycurve1.parent = myrail
    mycurve1.location.x = self.width
    mycurve1.location.y = -0.004
    mycurve1.location.z = 0.005

    mycurve2 = create_bezier("String_2", myp, (x, y, z))
    mycurve2.parent = myrail
    mycurve2.location.x = self.width
    mycurve2.location.y = -0.01
    mycurve2.location.z = 0.005

    if self.crt_mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
        mat = create_diffuse_material("String_material", False, 0.1, 0.1, 0.1,
                                      0.1, 0.1, 0.1, 0.01)
        set_material(mycurve1, mat)
        set_material(mycurve2, mat)

    # refine
    for obj in support:
        remove_doubles(obj)
        set_normals(obj)

    # deactivate others
    for o in bpy.data.objects:
        if o.select_get() is True:
            o.select_set(False)

    myrail.select_set(True)
    bpy.context.view_layer.objects.active = myrail

    return


# ------------------------------------------------------------------------------
# Create japan rail
#
# objName: Name for the new object
# sX: Size in X axis
# ways: Number of ways
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
# ------------------------------------------------------------------------------
def create_japan_rail(objname, sx, ways, px, py, pz, mat):
    myvertex = []
    myfaces = []

    waysize = 0.005  # gap
    sz = 0.0145
    size = 0.005
    sizeint = 0.01
    tap = 0.01
    sy = (size * 2) + (waysize * ways) + (sizeint * (ways - 1))
    v = 0
    # left extension
    myvertex.extend([(0, 0, 0), (0, 0, sz), (0, -sy, sz), (0, -sy, 0),
                     (tap, 0, 0), (tap, 0, sz), (tap, -sy, sz), (tap, -sy, 0)])
    myfaces.extend([(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (3, 2, 6, 7), (2, 1, 5, 6), (3, 0, 4, 7)])
    v += 8
    # Center
    myvertex.extend([(tap, -size, size), (tap, -size, 0), (tap, 0, 0), (tap, 0, sz), (tap, -sy, sz), (tap, -sy, 0),
                     (tap, -sy + size, 0), (tap, -sy + size, sz - 0.002)])
    myvertex.extend([(sx + tap, -size, size), (sx + tap, -size, 0), (sx + tap, 0, 0),
                     (sx + tap, 0, sz), (sx + tap, -sy, sz),
                     (sx + tap, -sy, 0), (sx + tap, -sy + size, 0), (sx + tap, -sy + size, sz - 0.002)])
    myfaces.extend([(v, v + 8, v + 9, v + 1), (v + 1, v + 9, v + 10, v + 2), (v + 2, v + 10, v + 11, v + 3),
                    (v + 3, v + 11, v + 12, v + 4),
                    (v + 4, v + 12, v + 13, v + 5), (v + 5, v + 13, v + 14, v + 6), (v + 7, v + 15, v + 14, v + 6)])
    v += 16
    # Right extension
    myvertex.extend([(sx + tap, 0, 0), (sx + tap, 0, sz), (sx + tap, -sy, sz),
                     (sx + tap, -sy, 0), (sx + tap + tap, 0, 0),
                     (sx + tap + tap, 0, sz), (sx + tap + tap, -sy, sz), (sx + tap + tap, -sy, 0)])
    myfaces.extend([(v, v + 1, v + 2, v + 3), (v + 4, v + 5, v + 6, v + 7),
                    (v, v + 1, v + 5, v + 4), (v + 3, v + 2, v + 6, v + 7),
                    (v + 2, v + 1, v + 5, v + 6), (v + 3, v, v + 4, v + 7)])
    v += 8

    # Internal
    space = waysize + size
    if ways > 1:
        for x in range(ways - 1):
            myvertex.extend([(tap, -space, sz), (tap, -space, 0), (tap, -space - sizeint, 0),
                             (tap, -space - sizeint, size)])
            myvertex.extend([(sx + tap, -space, sz), (sx + tap, -space, 0), (sx + tap, -space - sizeint, 0),
                             (sx + tap, -space - sizeint, size)])
            myfaces.extend([(v, v + 4, v + 5, v + 1), (v + 1, v + 5, v + 6, v + 2), (v + 2, v + 6, v + 7, v + 3)])
            v += 8
            space = space + waysize + sizeint

    mymesh = bpy.data.meshes.new(objname)
    myobject = bpy.data.objects.new(objname, mymesh)

    myobject.location[0] = px
    myobject.location[1] = py
    myobject.location[2] = pz
    bpy.context.collection.objects.link(myobject)

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

    # ---------------------------------
    # Materials
    # ---------------------------------
    if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
        # External
        mat = create_diffuse_material(objname + "_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)
        set_material(myobject, mat)

    return myobject


# ------------------------------------------------------------------------------
# Create japan support
#
# objName: Name for the new object
# sX: Size in X axis
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
# ------------------------------------------------------------------------------
def create_japan_support(objname, sx, px, py, pz, mat):
    myvertex = []
    myfaces = []

    waysize = 0.008
    sz = 0.015
    sy = 0.006

    myvertex.extend([(0, 0, 0), (0, 0, -sz), (0, -sy, -sz), (0, -sy, -waysize), (0, -0.003, -waysize), (0, -0.003, 0)])
    myvertex.extend(
        [(sx, 0, 0), (sx, 0, -sz), (sx, -sy, -sz), (sx, -sy, - waysize), (sx, -0.003, -waysize), (sx, -0.003, 0)])
    myfaces.extend(
        [(0, 1, 7, 6), (2, 3, 9, 8), (1, 7, 8, 2), (3, 4, 10, 9), (4, 5, 11, 10), (0, 6, 11, 5), (0, 1, 2, 3, 4, 5),
         (6, 7, 8, 9, 10, 11)])

    mymesh = bpy.data.meshes.new(objname)
    myobject = bpy.data.objects.new(objname, mymesh)

    myobject.location[0] = px
    myobject.location[1] = py
    myobject.location[2] = pz
    bpy.context.collection.objects.link(myobject)

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

    # ---------------------------------
    # Materials
    # ---------------------------------
    if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
        # External
        mat = create_diffuse_material(objname + "_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)
        set_material(myobject, mat)

    return myobject


# ------------------------------------------------------------------------------
# Create japan panel
#
# objName: Name for the new object
# sX: Size in X axis
# sZ: Size in Z axis
# pX: position X axis
# pY: position Y axis
# pZ: position Z axis
# mat: Flag for creating materials
# fabricMat: Fabric material
# ------------------------------------------------------------------------------
def create_japan_panel(objname, sx, sz, px, py, pz, mat, fabricmat):
    myvertex = []
    myfaces = []

    myvertex.extend([(0, 0, 0), (0, 0, -sz), (sx, 0, -sz), (sx, 0, 0)])
    myfaces.extend([(0, 1, 2, 3)])

    mymesh = bpy.data.meshes.new(objname)
    myobject = bpy.data.objects.new(objname, mymesh)

    myobject.location[0] = px
    myobject.location[1] = py
    myobject.location[2] = pz
    bpy.context.collection.objects.link(myobject)

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

    # ---------------------------------
    # Materials
    # ---------------------------------
    if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
        unwrap_mesh(myobject, True)
        # remap UV to use all texture
        for uv_loop in myobject.data.uv_layers.active.data:
            myvector = uv_loop.uv
            if myvector.x > 0.0001:
                myvector.x = 1

        set_material(myobject, fabricmat)
    return myobject


# ------------------------------------------------------------------------------
# Create bezier curve
# ------------------------------------------------------------------------------
def create_bezier(objname, points, origin, depth=0.001, fill='FULL'):
    curvedata = bpy.data.curves.new(name=objname, type='CURVE')
    curvedata.dimensions = '3D'
    curvedata.fill_mode = fill
    curvedata.bevel_resolution = 5
    curvedata.bevel_depth = depth

    myobject = bpy.data.objects.new(objname, curvedata)
    myobject.location = origin

    bpy.context.collection.objects.link(myobject)

    polyline = curvedata.splines.new('BEZIER')
    polyline.bezier_points.add(len(points) - 1)

    for idx, (knot, h1, h2) in enumerate(points):
        point = polyline.bezier_points[idx]
        point.co = knot
        point.handle_left = h1
        point.handle_right = h2
        point.handle_left_type = 'FREE'
        point.handle_right_type = 'FREE'

    return myobject


# ------------------------------------------------------------------------------
# Generate Roller curtains
# Shapes the main object's mesh (the tube) and creates the other parts as children.
# ------------------------------------------------------------------------------
def shape_roller_and_create_children(mainobject, tmp_mesh):
    rp = mainobject.RollerObjectGenerator[0]
    use_mat = rp.crt_mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}
    # A zero-height panel would be a degenerate face, so a fully rolled-up
    # curtain keeps a 2 mm lip under the tube.
    drop = max(rp.height * rp.ratio / 100, 0.002)

    plastic = None
    if use_mat:
        ensure_roller_fabric(rp)
        plastic = create_diffuse_material("Plastic_roller_material", False, 0.653, 0.485, 0.265, 0.653, 0.485, 0.265,
                                          0.2)

    # ------------------
    # Roller Top
    # ------------------
    fill_roller_rail_mesh(tmp_mesh, rp.width, 0.035)
    finish_roller_mesh(tmp_mesh)
    if use_mat:
        tmp_mesh.materials.append(rp.fabric_solid)

    # ------------------
    # Sides
    # ------------------
    for side, px in (("L", 0.026), ("R", rp.width - 0.026)):
        myside = create_roller_side(mainobject, side, px)
        if use_mat:
            myside.data.materials.append(plastic)

    # ------------------
    # Panel
    # ------------------
    verts = [(0, 0, 0), (0, 0, -drop), (rp.width, 0, -drop), (rp.width, 0, 0)]
    panelmesh = bpy.data.meshes.new("Panel")
    panelmesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    # UVs in meters keep the weave the same size whatever the width or drop.
    uvs = panelmesh.uv_layers.new(name="UVMap")
    for loop in panelmesh.loops:
        co = verts[loop.vertex_index]
        uvs.data[loop.index].uv = (co[0], co[2])
    mypanel = bpy.data.objects.new("Panel", panelmesh)
    bpy.context.collection.objects.link(mypanel)
    mypanel.parent = mainobject
    mypanel.location = (0, 0.035, 0)
    if use_mat:
        panelmesh.materials.append(rp.fabric)

    # ------------------
    # Roller Bottom
    # ------------------
    bottommesh = bpy.data.meshes.new("Roller_bottom")
    fill_roller_rail_mesh(bottommesh, rp.width, 0.001)
    finish_roller_mesh(bottommesh)
    mybottom = bpy.data.objects.new("Roller_bottom", bottommesh)
    bpy.context.collection.objects.link(mybottom)
    mybottom.parent = mypanel
    mybottom.location = (0, 0, -drop)
    if use_mat:
        bottommesh.materials.append(plastic)

    # ------------------------
    # Strings
    # ------------------------
    myp = [((0.0000, -0.0328, -0.0000), (0.0000, -0.0403, -0.3327), (0.0000, -0.0293, 0.1528)),
           ((0.0000, 0.0000, 0.3900), (0.0000, -0.0264, 0.3900), (-0.0000, 0.0226, 0.3900)),
           ((-0.0000, 0.0212, 0.0000), (-0.0000, 0.0189, 0.1525), (-0.0000, 0.0260, -0.3326)),
           ((-0.0000, -0.0000, -0.8518), (-0.0000, 0.0369, -0.8391), (0.0000, -0.0373, -0.8646))]  # double element
    mycurve = create_bezier("String", myp, (0, 0, 0))
    set_curve_cycle(mycurve)
    mycurve.parent = mainobject
    mycurve.location = (rp.width + 0.015, 0, -0.38)
    if use_mat:
        mat = create_diffuse_material("String_material", False, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.01)
        mycurve.data.materials.append(mat)

    for o in bpy.data.objects:
        if o.select_get() is True and o.name != mainobject.name:
            o.select_set(False)


# ------------------------------------------------------------------------------
# Fill a mesh with an open cylinder along X (the roller tube or bottom rail)
#
# width: Total width of roller
# radio: Roll radio
# ------------------------------------------------------------------------------
def fill_roller_rail_mesh(mymesh, width, radio):
    myvertex = []
    myfaces = []
    pies = 16

    for x in (0.0, width):
        for i in range(pies):
            seg = radians(i * 360 / pies)
            myvertex.append((x, cos(seg) * radio, sin(seg) * radio))

    for n in range(pies):
        nxt = (n + 1) % pies
        myfaces.append((n, nxt, nxt + pies, n + pies))

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)


# ------------------------------------------------------------------------------
# Outward normals and smooth shading without entering edit mode, since this
# also runs inside property update callbacks.
# ------------------------------------------------------------------------------
def finish_roller_mesh(mymesh):
    bm = bmesh.new()
    bm.from_mesh(mymesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mymesh)
    bm.free()
    mymesh.shade_smooth()


# ------------------------------------------------------------------------------
# Create roller side cap
#
# myroller: Roller to add sides
# side: Side of the cap R/L
# px: position X axis
# ------------------------------------------------------------------------------
def create_roller_side(myroller, side, px):
    myvertex, myfaces = roller_side()

    mymesh = bpy.data.meshes.new("Side." + side)
    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)
    finish_roller_mesh(mymesh)

    myside = bpy.data.objects.new("Side." + side, mymesh)
    bpy.context.collection.objects.link(myside)
    myside.location = (px, 0, 0)
    if side == "L":
        myside.rotation_euler = (0, 0, radians(180))
    myside.parent = myroller

    mod = myside.modifiers.new("Subdivision", 'SUBSURF')
    mod.levels = 2

    return myside


# ------------------------------------------------------------------------------
# Roller fabric materials
#
# The panel shader multiplies the grayscale weave texture by the chosen color,
# then mixes it with a Transparent BSDF so opacity sets how much light passes.
# The tube uses a plain diffuse in the same color: rolled-up fabric is many
# layers thick and shouldn't look see-through.
# ------------------------------------------------------------------------------
def ensure_roller_fabric(rp):
    # Recreated if missing, e.g. after the user purged unused materials.
    if rp.fabric is None:
        rp.fabric = create_roller_fabric_material("Roller_fabric_material")
    if rp.fabric_solid is None:
        rp.fabric_solid = create_diffuse_material("Roller_fabric_solid_material", True, 0.8, 0.8, 0.8)
    apply_roller_fabric(rp)


def create_roller_fabric_material(matname):
    mat = bpy.data.materials.new(matname)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    remove_default_shader(nodes)
    output = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    output.location = 1210, 320

    coords = nodes.new('ShaderNodeTexCoord')
    coords.location = 26, 395

    # UVs are in meters, so this repeats the weave every millimeter.
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = 266, 380
    mapping.inputs['Scale'].default_value = (1000, 1000, 1000)

    image = nodes.new('ShaderNodeTexImage')
    image.image = load_fabric_image()
    image.location = 450, 380

    tint = nodes.new('ShaderNodeMix')
    tint.name = 'Roller_tint'
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs[0].default_value = 1.0
    tint.location = 650, 380

    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = 850, 300

    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = 850, 420

    mix = nodes.new('ShaderNodeMixShader')
    mix.name = 'Roller_opacity'
    mix.location = 1040, 356

    links.new(coords.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], image.inputs['Vector'])
    links.new(image.outputs['Color'], _socket(tint.inputs, 'A_Color'))
    links.new(_socket(tint.outputs, 'Result_Color'), diffuse.inputs['Color'])
    links.new(transparent.outputs['BSDF'], mix.inputs[1])
    links.new(diffuse.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    return mat


# Mix node sockets share display names across data types ("A", "B"), so look
# them up by identifier.
def _socket(sockets, identifier):
    for socket in sockets:
        if socket.identifier == identifier:
            return socket
    raise LookupError("Archimesh: node has no socket '%s'" % identifier)


def apply_roller_fabric(rp):
    color = tuple(rp.objcol)
    if rp.fabric is not None:
        rp.fabric.diffuse_color = color
        nodes = rp.fabric.node_tree.nodes
        tint = nodes.get('Roller_tint')
        mix = nodes.get('Roller_opacity')
        if tint is None or mix is None:
            # The user rebuilt the shader; leave it alone rather than guess.
            print("Archimesh: %s has no Roller_tint/Roller_opacity node, color and opacity not applied"
                  % rp.fabric.name)
        else:
            _socket(tint.inputs, 'B_Color').default_value = color
            mix.inputs[0].default_value = rp.opacity

    if rp.fabric_solid is not None:
        rp.fabric_solid.diffuse_color = color
        diffuse = rp.fabric_solid.node_tree.nodes.get('Diffuse BSDF')
        if diffuse is None:
            print("Archimesh: %s has no Diffuse BSDF node, color not applied" % rp.fabric_solid.name)
        else:
            diffuse.inputs['Color'].default_value = color


# ----------------------------------------------
# Roller side data
# ----------------------------------------------
def roller_side():
    # ------------------------------------
    # Mesh data
    # ------------------------------------
    minx = -7.54842304218073e-08
    maxx = 0.05209559202194214
    miny = -0.04486268758773804
    maxy = 0.04486268758773804
    minz = -0.04486268758773804
    maxz = 0.08202265202999115

    # Vertex
    myvertex = [(maxx - 0.004684023559093475, maxy, minz + 0.04486270064847542),
                (maxx - 0.004684023559093475, maxy - 0.0034149661660194397, minz + 0.027694489806890488),
                (maxx - 0.004684023559093475, maxy - 0.013139978051185608, minz + 0.013139985501766205),
                (maxx - 0.004684023559093475, maxy - 0.02769448049366474, minz + 0.0034149736166000366),
                (maxx - 0.004684023559093475, miny + 0.044862685327428764, minz),
                (maxx - 0.004684023559093475, miny + 0.027694476768374443, minz + 0.0034149736166000366),
                (maxx - 0.004684023559093475, miny + 0.013139978051185608, minz + 0.013139985501766205),
                (maxx - 0.004684023559093475, miny + 0.0034149661660194397, minz + 0.02769448794424534),
                (maxx - 0.004684023559093475, miny, minz + 0.04486269387439812),
                (maxx - 0.004684023559093475, miny + 0.0034149624407291412, minz + 0.06203090213239193),
                (maxx - 0.004684023559093475, miny + 0.013139966875314713, maxz - 0.050299935042858124),
                (maxx - 0.004684023559093475, miny + 0.027694474905729294, maxz - 0.04057491198182106),
                (maxx - 0.004684023559093475, maxy - 0.027694473043084145, maxz - 0.04057491570711136),
                (maxx - 0.004684023559093475, maxy - 0.013139966875314713, maxz - 0.05029993876814842),
                (maxx - 0.004684023559093475, maxy - 0.0034149587154388428, minz + 0.062030890956521034),
                (maxx - 0.0046574510633945465, miny + 0.028278490528464317, minz + 0.0048249028623104095),
                (maxx - 0.0046574510633945465, miny + 0.014219092205166817, minz + 0.014219097793102264),
                (maxx - 0.0046574510633945465, miny + 0.004824899137020111, minz + 0.028278499841690063),
                (maxx - 0.003122705966234207, maxy, minz + 0.04486270064847542),
                (maxx - 0.003122705966234207, maxy - 0.0034149661660194397, minz + 0.027694489806890488),
                (maxx - 0.003122705966234207, maxy - 0.013139978051185608, minz + 0.013139985501766205),
                (maxx - 0.003122705966234207, maxy - 0.02769448049366474, minz + 0.0034149736166000366),
                (maxx - 0.003149278461933136, maxy - 0.04486268735455812, maxz - 0.03868604078888893),
                (maxx - 0.003149278461933136, maxy - 0.02827848680317402, maxz - 0.04198484495282173),
                (maxx - 0.003149278461933136, maxy - 0.014219081029295921, maxz - 0.05137905105948448),
                (maxx - 0.003149278461933136, maxy - 0.004824887961149216, minz + 0.06144687905907631),
                (maxx - 0.02118653617799282, miny + 0.027694474905729294, maxz - 0.04057491570711136),
                (maxx - 0.02118653617799282, miny + 0.013139966875314713, maxz - 0.050299935042858124),
                (maxx - 0.02118653617799282, miny + 0.0034149624407291412, minz + 0.06203090213239193),
                (maxx - 0.02118653617799282, miny, minz + 0.04486269262849252),
                (maxx - 0.003122705966234207, miny, minz + 0.04486269387439812),
                (maxx - 0.003122705966234207, miny + 0.0034149624407291412, minz + 0.06203090213239193),
                (maxx - 0.003122705966234207, miny + 0.013139966875314713, maxz - 0.050299935042858124),
                (maxx - 0.003122705966234207, miny + 0.027694474905729294, maxz - 0.04057491198182106),
                (maxx - 0.02118653617799282, maxy - 0.02769448049366474, minz + 0.0034149661660194397),
                (maxx - 0.02118653617799282, maxy - 0.013139978051185608, minz + 0.013139981776475906),
                (maxx - 0.02118653617799282, maxy - 0.0034149661660194397, minz + 0.02769448794424534),
                (maxx - 0.02118653617799282, maxy, minz + 0.044862699402576034),
                (maxx - 0.020517520606517792, miny + 0.01146744191646576, minz + 0.03102993033826351),
                (maxx - 0.020517520606517792, miny + 0.01930307224392891, minz + 0.019303075969219208),
                (maxx - 0.020517520606517792, miny + 0.031029919162392616, minz + 0.01146744191646576),
                (maxx - 0.020517520606517792, miny + 0.04486268576937835, minz + 0.008715935051441193),
                (maxx - 0.003122705966234207, maxy - 0.013139966875314713, maxz - 0.02605174481868744),
                (maxx, miny + 0.013139966875314713, maxz - 0.026319395750761032),
                (maxx, miny + 0.027694474905729294, maxz - 0.026230186223983765),
                (maxx, maxy - 0.013139966875314713, maxz - 0.02605174481868744),
                (maxx - 0.0046574510633945465, miny + 0.0015261024236679077, minz + 0.04486269394558251),
                (maxx - 0.0046574510633945465, miny + 0.004824895411729813, minz + 0.061446888372302055),
                (maxx - 0.0046574510633945465, miny + 0.014219081029295921, maxz - 0.05137904919683933),
                (maxx - 0.0046574510633945465, miny + 0.02827848680317402, maxz - 0.04198484495282173),
                (maxx, maxy - 0.027694473043084145, maxz - 0.026230186223983765),
                (maxx, maxy - 0.04486268735205459, maxz - 0.02629481628537178),
                (maxx - 0.003122705966234207, maxy - 0.027694473043084145, maxz - 0.04057491570711136),
                (maxx - 0.003122705966234207, maxy - 0.013139966875314713, maxz - 0.05029993876814842),
                (maxx - 0.003122705966234207, maxy - 0.0034149587154388428, minz + 0.062030890956521034),
                (maxx - 0.003149278461933136, maxy - 0.0015261024236679077, minz + 0.044862700489230356),
                (maxx - 0.003149278461933136, maxy - 0.004824899137020111, minz + 0.028278501704335213),
                (maxx - 0.003149278461933136, maxy - 0.014219092205166817, minz + 0.014219097793102264),
                (maxx - 0.003149278461933136, maxy - 0.028278492391109467, minz + 0.0048249028623104095),
                (maxx - 0.003149278461933136, miny + 0.0015261024236679077, minz + 0.04486269394558251),
                (maxx - 0.003149278461933136, miny + 0.004824895411729813, minz + 0.061446888372302055),
                (maxx - 0.003149278461933136, miny + 0.014219081029295921, maxz - 0.05137904919683933),
                (maxx - 0.003149278461933136, miny + 0.02827848680317402, maxz - 0.04198484495282173),
                (maxx - 0.02118653617799282, maxy - 0.0034149587154388428, minz + 0.062030889093875885),
                (maxx - 0.02118653617799282, maxy - 0.013139966875314713, maxz - 0.05029993876814842),
                (maxx - 0.02118653617799282, maxy - 0.027694473043084145, maxz - 0.04057491570711136),
                (maxx - 0.02118653617799282, maxy - 0.04486268735205459, maxz - 0.03715994209051132),
                (maxx - 0.020517520606517792, maxy - 0.011467430740594864, minz + 0.058695447631180286),
                (maxx - 0.020517520606517792, maxy - 0.019303061068058014, maxz - 0.05646303482353687),
                (maxx - 0.020517520606517792, maxy - 0.031029915437102318, maxz - 0.04862739145755768),
                (maxx - 0.020517520606517792, maxy - 0.044862687395027134, maxz - 0.045875877141952515),
                (maxx, miny + 0.0034149661660194397, minz + 0.02769448794424534),
                (maxx, miny + 0.013139978051185608, minz + 0.013139985501766205),
                (maxx, miny + 0.027694476768374443, minz + 0.0034149736166000366),
                (maxx, miny + 0.044862685327428764, minz),
                (maxx - 0.02118653617799282, miny + 0.0034149661660194397, minz + 0.02769448794424534),
                (maxx - 0.02118653617799282, miny + 0.013139978051185608, minz + 0.013139981776475906),
                (maxx - 0.02118653617799282, miny + 0.027694476768374443, minz + 0.0034149661660194397),
                (maxx - 0.02118653617799282, miny + 0.044862685327428764, minz),
                (maxx - 0.020517520606517792, maxy - 0.031029922887682915, minz + 0.01146744191646576),
                (maxx - 0.020517520606517792, maxy - 0.01930307224392891, minz + 0.019303075969219208),
                (maxx - 0.020517520606517792, maxy - 0.01146744191646576, minz + 0.03102993033826351),
                (maxx - 0.020517520606517792, maxy - 0.008715927600860596, minz + 0.04486269835125789),
                (maxx - 0.0046574510633945465, maxy - 0.04486268735455812, maxz - 0.03868604078888893),
                (maxx - 0.0046574510633945465, maxy - 0.02827848680317402, maxz - 0.04198484495282173),
                (maxx - 0.0046574510633945465, maxy - 0.014219081029295921, maxz - 0.05137905105948448),
                (maxx - 0.0046574510633945465, maxy - 0.004824887961149216, minz + 0.06144687905907631),
                (maxx - 0.0046574510633945465, maxy - 0.0015261024236679077, minz + 0.044862700489230356),
                (maxx - 0.0046574510633945465, maxy - 0.004824899137020111, minz + 0.028278501704335213),
                (maxx - 0.0046574510633945465, maxy - 0.014219092205166817, minz + 0.014219097793102264),
                (maxx - 0.0046574510633945465, maxy - 0.028278492391109467, minz + 0.0048249028623104095),
                (maxx - 0.003149278461933136, miny + 0.004824899137020111, minz + 0.028278499841690063),
                (maxx - 0.003149278461933136, miny + 0.014219092205166817, minz + 0.014219097793102264),
                (maxx - 0.003149278461933136, miny + 0.028278490528464317, minz + 0.0048249028623104095),
                (maxx, miny, minz + 0.04486269387439812),
                (maxx, miny + 0.0034149624407291412, minz + 0.06203090213239193),
                (maxx, miny + 0.013139966875314713, maxz - 0.050299935042858124),
                (maxx, miny + 0.027694474905729294, maxz - 0.04057491198182106),
                (maxx - 0.020517520606517792, miny + 0.031029917299747467, maxz - 0.04862739145755768),
                (maxx - 0.020517520606517792, miny + 0.019303061068058014, maxz - 0.056463029235601425),
                (maxx - 0.020517520606517792, miny + 0.011467434465885162, minz + 0.05869545880705118),
                (maxx - 0.020517520606517792, miny + 0.008715927600860596, minz + 0.04486269289324163),
                (maxx - 0.003122705966234207, miny + 0.0034149661660194397, minz + 0.02769448794424534),
                (maxx - 0.003122705966234207, miny + 0.013139978051185608, minz + 0.013139985501766205),
                (maxx - 0.003122705966234207, miny + 0.027694476768374443, minz + 0.0034149736166000366),
                (maxx - 0.003122705966234207, miny + 0.044862685327428764, minz),
                (maxx, maxy - 0.02769448049366474, minz + 0.0034149736166000366),
                (maxx, maxy - 0.013139978051185608, minz + 0.013139985501766205),
                (maxx, maxy - 0.0034149661660194397, minz + 0.027694489806890488),
                (maxx, maxy, minz + 0.04486270064847542),
                (maxx, maxy - 0.0034149587154388428, minz + 0.062030890956521034),
                (maxx, maxy - 0.013139966875314713, maxz - 0.05029993876814842),
                (maxx, maxy - 0.027694473043084145, maxz - 0.04057491570711136),
                (maxx, maxy - 0.04486268735205459, maxz - 0.03715994209051132),
                (maxx - 0.003122705966234207, maxy - 0.027694473043084145, maxz - 0.026230186223983765),
                (maxx - 0.003122705966234207, maxy - 0.04486268735205459, maxz - 0.02629481628537178),
                (maxx - 0.003122705966234207, miny + 0.027694474905729294, maxz - 0.026230186223983765),
                (maxx - 0.003122705966234207, miny + 0.013139966875314713, maxz - 0.026319395750761032),
                (maxx - 0.003122705966234207, miny + 0.013139966875314713, maxz - 0.0018796995282173157),
                (maxx - 0.01466318964958191, miny + 0.013139966875314713, maxz - 0.0018796995282173157),
                (maxx, miny + 0.027694474905729294, maxz - 0.0017904937267303467),
                (maxx, maxy - 0.013139966875314713, maxz - 0.001612052321434021),
                (maxx - 0.009187713265419006, maxy - 0.013139966875314713, maxz - 0.02605174481868744),
                (maxx - 0.009187713265419006, maxy - 0.027694473043084145, maxz - 0.026230186223983765),
                (maxx - 0.009187713265419006, maxy - 0.04486268735205459, maxz - 0.02629481628537178),
                (maxx - 0.009187713265419006, miny + 0.027694474905729294, maxz - 0.026230186223983765),
                (maxx - 0.009187713265419006, miny + 0.013139966875314713, maxz - 0.026319395750761032),
                (maxx - 0.003122705966234207, maxy - 0.013139966875314713, maxz - 0.001612052321434021),
                (maxx - 0.01466318964958191, miny + 0.027694474905729294, maxz - 0.0017904937267303467),
                (maxx, miny + 0.022660084068775177, minz + 0.03566607739776373),
                (maxx, miny + 0.02786955051124096, minz + 0.027869559824466705),
                (maxx, miny + 0.03566606715321541, minz + 0.022660093382000923),
                (maxx, miny + 0.04486268649608238, minz + 0.020830770954489708),
                (maxx, miny + 0.02083076350390911, minz + 0.044862694725740226),
                (maxx, miny + 0.022660082206130028, minz + 0.05405931267887354),
                (maxx, miny + 0.02786954492330551, minz + 0.061855828389525414),
                (maxx, miny + 0.035666066221892834, maxz - 0.059820037335157394),
                (maxx, maxy - 0.03566606715321541, minz + 0.022660093382000923),
                (maxx, maxy - 0.02786955051124096, minz + 0.027869559824466705),
                (maxx, maxy - 0.022660084068775177, minz + 0.035666078329086304),
                (maxx, maxy - 0.02083076350390911, minz + 0.044862698354463326),
                (maxx, maxy - 0.02266007848083973, minz + 0.05405930709093809),
                (maxx, maxy - 0.02786954492330551, minz + 0.061855828389525414),
                (maxx, maxy - 0.035666064359247684, maxz - 0.059820037335157394),
                (maxx, maxy - 0.04486268734234705, maxz - 0.05799071677029133),
                (maxx, miny + 0.04486268733843682, minz + 0.04486269544876009),
                (maxx - 0.009557131677865982, maxy - 0.04486268735205459, maxz - 0.02464577928185463),
                (maxx - 0.009557131677865982, miny + 0.027694474905729294, maxz - 0.024581149220466614),
                (maxx - 0.009557131677865982, maxy - 0.013139966875314713, maxz - 0.024402707815170288),
                (maxx - 0.009557131677865982, miny + 0.013139966875314713, maxz - 0.02467035874724388),
                (maxx - 0.009557131677865982, maxy - 0.027694473043084145, maxz - 0.024581149220466614),
                (maxx - 0.015024378895759583, miny + 0.027694474905729294, maxz - 0.00017844140529632568),
                (maxx - 0.015024378895759583, miny + 0.013139966875314713, maxz - 0.0002676546573638916),
                (maxx - 0.015024378895759583, maxy - 0.04486268735205459, maxz - 0.0002430751919746399),
                (maxx - 0.015024378895759583, maxy - 0.027694473043084145, maxz - 0.00017844140529632568),
                (maxx - 0.015024378895759583, maxy - 0.013139966875314713, maxz),
                (maxx, miny + 0.013139966875314713, maxz - 0.0018796995282173157),
                (maxx - 0.01466318964958191, maxy - 0.04486268735205459, maxz - 0.001855120062828064),
                (maxx, maxy - 0.04486268735205459, maxz - 0.001855120062828064),
                (maxx - 0.01466318964958191, maxy - 0.027694473043084145, maxz - 0.0017904937267303467),
                (maxx - 0.01466318964958191, maxy - 0.013139966875314713, maxz - 0.001612052321434021),
                (maxx, maxy - 0.027694473043084145, maxz - 0.0017904937267303467),
                (maxx - 0.020517520606517792, miny + 0.014739999547600746, minz + 0.03238546848297119),
                (maxx - 0.020517520606517792, miny + 0.021807780489325523, minz + 0.02180778607726097),
                (maxx - 0.020517520606517792, miny + 0.03238545823842287, minz + 0.014740003272891045),
                (maxx - 0.020517520606517792, miny + 0.044862685933359736, minz + 0.012258127331733704),
                (maxx - 0.020517520606517792, maxy - 0.014739990234375, minz + 0.05733991041779518),
                (maxx - 0.020517520606517792, maxy - 0.021807771176099777, maxz - 0.05896773934364319),
                (maxx - 0.020517520606517792, maxy - 0.03238545451313257, maxz - 0.051899950951337814),
                (maxx - 0.020517520606517792, maxy - 0.044862687428120204, maxz - 0.049418069422245026),
                (maxx - 0.020517520606517792, maxy - 0.03238546196371317, minz + 0.014740003272891045),
                (maxx - 0.020517520606517792, maxy - 0.021807780489325523, minz + 0.02180778607726097),
                (maxx - 0.020517520606517792, maxy - 0.014739999547600746, minz + 0.03238546848297119),
                (maxx - 0.020517520606517792, maxy - 0.012258119881153107, minz + 0.04486269794694575),
                (maxx - 0.020517520606517792, miny + 0.03238545544445515, maxz - 0.051899950951337814),
                (maxx - 0.020517520606517792, miny + 0.021807771176099777, maxz - 0.05896773561835289),
                (maxx - 0.020517520606517792, miny + 0.014739995822310448, minz + 0.05733991973102093),
                (maxx - 0.020517520606517792, miny + 0.012258119881153107, minz + 0.04486269302378876),
                (minx, miny + 0.014739999547600746, minz + 0.03238546848297119),
                (minx, miny + 0.021807780489325523, minz + 0.02180778607726097),
                (minx, miny + 0.03238545823842287, minz + 0.014740003272891045),
                (minx, miny + 0.044862685933359736, minz + 0.012258127331733704),
                (minx, maxy - 0.014739990234375, minz + 0.05733991041779518),
                (minx, maxy - 0.021807771176099777, maxz - 0.05896773934364319),
                (minx, maxy - 0.03238545451313257, maxz - 0.051899950951337814),
                (minx, maxy - 0.044862687428120204, maxz - 0.049418069422245026),
                (minx, maxy - 0.03238546196371317, minz + 0.014740003272891045),
                (minx, maxy - 0.021807780489325523, minz + 0.02180778607726097),
                (minx, maxy - 0.014739999547600746, minz + 0.03238546848297119),
                (minx, maxy - 0.012258119881153107, minz + 0.04486269794694575),
                (minx, miny + 0.03238545544445515, maxz - 0.051899950951337814),
                (minx, miny + 0.021807771176099777, maxz - 0.05896773561835289),
                (minx, miny + 0.014739995822310448, minz + 0.05733991973102093),
                (minx, miny + 0.012258119881153107, minz + 0.04486269302378876)]

    # Faces
    myfaces = [(37, 0, 1, 36), (36, 1, 2, 35), (35, 2, 3, 34), (34, 3, 4, 78), (78, 4, 5, 77),
               (77, 5, 6, 76), (76, 6, 7, 75), (75, 7, 8, 29), (29, 8, 9, 28), (28, 9, 10, 27),
               (27, 10, 11, 26), (65, 12, 13, 64), (8, 7, 17, 46), (63, 14, 0, 37), (64, 13, 14, 63),
               (34, 78, 41, 79), (64, 63, 67, 68), (76, 75, 38, 39), (65, 64, 68, 69), (27, 26, 98, 99),
               (78, 77, 40, 41), (28, 27, 99, 100), (35, 34, 79, 80), (63, 37, 82, 67), (29, 28, 100, 101),
               (26, 66, 70, 98), (36, 35, 80, 81), (66, 65, 69, 70), (77, 76, 39, 40), (37, 36, 81, 82),
               (75, 29, 101, 38), (19, 18, 109, 108), (31, 32, 61, 60), (2, 1, 88, 89), (103, 102, 91, 92),
               (7, 6, 16, 17), (54, 18, 55, 25), (32, 33, 62, 61), (18, 19, 56, 55), (6, 5, 15, 16),
               (11, 10, 48, 49), (52, 53, 24, 23), (0, 14, 86, 87), (94, 71, 129, 133), (97, 113, 51, 44),
               (33, 32, 117, 116), (18, 54, 110, 109), (32, 31, 95, 96), (96, 97, 44, 43), (102, 103, 72, 71),
               (53, 52, 114, 42), (21, 20, 107, 106), (103, 104, 73, 72), (31, 30, 94, 95), (20, 19, 108, 107),
               (30, 102, 71, 94), (105, 21, 106, 74), (54, 53, 111, 110), (104, 105, 74, 73), (47, 46, 59, 60),
               (90, 89, 57, 58), (87, 86, 25, 55), (48, 47, 60, 61), (49, 48, 61, 62), (83, 49, 62, 22),
               (16, 15, 93, 92), (88, 87, 55, 56), (84, 83, 22, 23), (17, 16, 92, 91), (85, 84, 23, 24),
               (46, 17, 91, 59), (89, 88, 56, 57), (86, 85, 24, 25), (104, 103, 92, 93), (3, 2, 89, 90),
               (20, 21, 58, 57), (13, 12, 84, 85), (9, 8, 46, 47), (102, 30, 59, 91), (30, 31, 60, 59),
               (19, 20, 57, 56), (14, 13, 85, 86), (53, 54, 25, 24), (10, 9, 47, 48), (1, 0, 87, 88),
               (111, 53, 42, 45), (112, 111, 45, 50), (32, 96, 43, 117), (113, 112, 50, 51), (115, 116, 125, 124),
               (42, 114, 123, 122), (116, 117, 126, 125), (114, 115, 124, 123), (112, 113, 144, 143),
               (95, 94, 133, 134),
               (110, 111, 142, 141), (96, 95, 134, 135), (74, 106, 137, 132), (97, 96, 135, 136), (73, 74, 132, 131),
               (107, 108, 139, 138), (113, 97, 136, 144), (72, 73, 131, 130), (108, 109, 140, 139),
               (109, 110, 141, 140),
               (71, 72, 130, 129), (106, 107, 138, 137), (111, 112, 143, 142), (135, 134, 145), (137, 138, 145),
               (142, 143, 145), (136, 135, 145), (131, 132, 145), (143, 144, 145), (144, 136, 145),
               (130, 131, 145), (141, 142, 145), (129, 130, 145), (132, 137, 145), (133, 129, 145),
               (138, 139, 145), (134, 133, 145), (139, 140, 145), (140, 141, 145), (26, 11, 83, 66),
               (66, 83, 12, 65), (12, 83, 84), (22, 52, 23), (83, 11, 49), (21, 105, 58),
               (4, 90, 58, 105), (15, 4, 105, 93), (33, 22, 62), (4, 3, 90), (105, 104, 93),
               (5, 4, 15), (52, 22, 115, 114), (22, 33, 116, 115), (124, 125, 147, 146), (122, 123, 150, 148),
               (125, 126, 149, 147), (123, 124, 146, 150), (157, 128, 151, 153), (159, 157, 153, 154),
               (160, 159, 154, 155),
               (128, 119, 152, 151), (146, 147, 128, 157), (150, 146, 157, 159), (148, 150, 159, 160),
               (147, 149, 119, 128),
               (69, 68, 167, 168), (101, 100, 176, 177), (39, 38, 162, 163), (100, 99, 175, 176), (41, 40, 164, 165),
               (80, 79, 170, 171), (82, 81, 172, 173), (67, 82, 173, 166), (70, 69, 168, 169), (38, 101, 177, 162),
               (98, 70, 169, 174), (40, 39, 163, 164), (79, 41, 165, 170), (99, 98, 174, 175), (81, 80, 171, 172),
               (68, 67, 166, 167), (169, 168, 184, 185), (170, 165, 181, 186), (172, 171, 187, 188),
               (162, 177, 193, 178),
               (164, 163, 179, 180), (167, 166, 182, 183), (174, 169, 185, 190), (168, 167, 183, 184),
               (175, 174, 190, 191),
               (171, 170, 186, 187), (173, 172, 188, 189), (163, 162, 178, 179), (165, 164, 180, 181),
               (177, 176, 192, 193),
               (166, 173, 189, 182), (176, 175, 191, 192), (51, 50, 161, 158), (127, 160, 155), (156, 120, 151, 152),
               (155, 154, 161, 121), (161, 154, 153, 158), (42, 122, 148), (117, 149, 126), (127, 42, 148, 160),
               (118, 152, 119), (158, 153, 151, 120), (50, 45, 121, 161), (117, 118, 119, 149), (43, 44, 120, 156),
               (44, 51, 158, 120), (117, 43, 156, 118), (45, 42, 127, 121)]

    return myvertex, myfaces


# --------------------------------------------------------------------
# Set curve cycle
#
# myObject: Curve object
# --------------------------------------------------------------------
def set_curve_cycle(myobject):
    bpy.context.view_layer.objects.active = myobject
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.curve.select_all(action='SELECT')
    # St cyclic
    bpy.ops.curve.cyclic_toggle(direction='CYCLIC_U')
    # go object mode again
    bpy.ops.object.editmode_toggle()
