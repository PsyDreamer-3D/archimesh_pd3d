# SPDX-FileCopyrightText: 2016-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------------------
# support routines and general functions
# Author: Antonio Vazquez (antonioya)
#
# ----------------------------------------------------------
# noinspection PyUnresolvedReferences
import bpy
from os import path


# --------------------------------------------------------------------
# Get length Blender units
# --------------------------------------------------------------------
def get_blendunits(units):
    if bpy.context.scene.unit_settings.system == "IMPERIAL":
        return units * 0.3048
    else:
        return units


# --------------------------------------------------------------------
# Set normals
# True= faces to inside
# False= faces to outside
# --------------------------------------------------------------------
def set_normals(myobject, direction=False):
    bpy.context.view_layer.objects.active = myobject
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.mesh.select_all(action='SELECT')
    # recalculate outside normals
    bpy.ops.mesh.normals_make_consistent(inside=direction)
    # go object mode again
    bpy.ops.object.editmode_toggle()


# --------------------------------------------------------------------
# Remove doubles
# --------------------------------------------------------------------
def remove_doubles(myobject):
    bpy.context.view_layer.objects.active = myobject
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.mesh.select_all(action='SELECT')
    # remove
    bpy.ops.mesh.remove_doubles()
    # go object mode again
    bpy.ops.object.editmode_toggle()


# --------------------------------------------------------------------
# Set shade smooth
# --------------------------------------------------------------------
def set_smooth(myobject):
    # deactivate others
    for o in bpy.data.objects:
        if o.select_get() is True:
            o.select_set(False)

    myobject.select_set(True)
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.shade_smooth()


# --------------------------------------------------------------------
# Add modifier (subdivision)
# --------------------------------------------------------------------
def set_modifier_subsurf(myobject):
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='SUBSURF')
        for mod in myobject.modifiers:
            if mod.type == 'SUBSURF':
                mod.levels = 2


# --------------------------------------------------------------------
# Add modifier (mirror)
# --------------------------------------------------------------------
def set_modifier_mirror(myobject, axis="Y"):
    bpy.ops.object.select_all(action='DESELECT')
    myobject.select_set(True)
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='MIRROR')
        for mod in myobject.modifiers:
            if mod.type == 'MIRROR':
                if axis == "X":
                    mod.use_axis[0] = True
                else:
                    mod.use_axis[0] = False

                if axis == "Y":
                    mod.use_axis[1] = True
                else:
                    mod.use_axis[1] = False

                if axis == "Z":
                    mod.use_axis[2] = True
                else:
                    mod.use_axis[2] = False

                mod.use_clip = True


# --------------------------------------------------------------------
# Add modifier (array)
# --------------------------------------------------------------------
def set_modifier_array(myobject, axis, move, repeat, fix=False, fixmove=0, zmove=0):
    bpy.ops.object.select_all(action='DESELECT')
    myobject.select_set(True)
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='ARRAY')
        for mod in myobject.modifiers:
            if mod.type == 'ARRAY':
                if mod.name == "Array":
                    mod.name = "Array_" + axis
                    mod.count = repeat
                    mod.use_constant_offset = fix
                    if axis == "X":
                        mod.relative_offset_displace[0] = move
                        mod.constant_offset_displace[0] = fixmove
                        mod.relative_offset_displace[1] = 0.0
                        mod.constant_offset_displace[1] = 0.0
                        mod.relative_offset_displace[2] = 0.0
                        mod.constant_offset_displace[2] = zmove

                    if axis == "Y":
                        mod.relative_offset_displace[0] = 0.0
                        mod.constant_offset_displace[0] = 0.0
                        mod.relative_offset_displace[1] = move
                        mod.constant_offset_displace[1] = fixmove
                        mod.relative_offset_displace[2] = 0.0
                        mod.constant_offset_displace[2] = 0.0


# --------------------------------------------------------------------
# Add modifier (curve)
# --------------------------------------------------------------------
def set_modifier_curve(myobject, mycurve):
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='CURVE')
        for mod in myobject.modifiers:
            if mod.type == 'CURVE':
                mod.deform_axis = 'POS_X'
                mod.object = mycurve


# --------------------------------------------------------------------
# Add modifier (solidify)
# --------------------------------------------------------------------
def set_modifier_solidify(myobject, width):
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        for mod in myobject.modifiers:
            if mod.type == 'SOLIDIFY':
                mod.thickness = width
                mod.use_even_offset = True
                mod.use_quality_normals = True
                break


# --------------------------------------------------------------------
# Add modifier (boolean)
# --------------------------------------------------------------------
def set_modifier_boolean(myobject, bolobject):
    boolean_modifier = myobject.modifiers.new("", 'BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = bolobject


# --------------------------------------------------------------------
# Scale a door/window hole control box so it cuts through the room's walls
# --------------------------------------------------------------------
def fit_hole_to_wall(ctrl, room):
    t = room.RoomGenerator[0].wall_width
    if t > 0:
        # Measure the mesh, not ctrl.dimensions: a freshly rebuilt box has no
        # evaluated bounds until the depsgraph updates.
        ys = [v.co.y for v in ctrl.data.vertices]
        ctrl.scale.y = (t + 0.45) / (max(ys) - min(ys))  # Add some gap
    else:
        ctrl.scale.y = 1


# --------------------------------------------------------------------
# Keep Boolean cutters connected across property-update rebuilds
#
# Door/window/room property updates delete and recreate their child objects
# (the "_Group" empty with its control boxes, or the room's baseboard/shell).
# Booleans that cut with those objects, and the group's parenting to the room
# set up by Auto Holes, would otherwise be lost, so callers capture them before
# deleting and restore them onto the recreated objects.
# --------------------------------------------------------------------
CTRL_ROLES = ("archimesh.ctrl_hole", "archimesh.ctrl_base")


def find_ctrl_boxes(group):
    return {role: child for child in group.children for role in CTRL_ROLES if child.get(role)}


def capture_group_links(group):
    roles = {ctrl: role for role, ctrl in find_ctrl_boxes(group).items()}
    booleans = [(obj.name, mod.name, roles[mod.object])
                for obj in bpy.data.objects
                for mod in obj.modifiers
                if mod.type == 'BOOLEAN' and mod.object in roles]
    return {
        "parent": group.parent,
        "parent_inverse": group.matrix_parent_inverse.copy(),
        "booleans": booleans,
    }


def restore_group_links(group, links):
    parent = links["parent"]
    if parent is not None:
        # Only the parent relationship is restored, not the old local transform:
        # the rebuild already placed the group at its old local location, and
        # its rotation must follow the (possibly just edited) rotation property.
        group.parent = parent
        group.matrix_parent_inverse = links["parent_inverse"]

    ctrls = find_ctrl_boxes(group)
    if parent is not None and len(parent.RoomGenerator) > 0 and "archimesh.ctrl_hole" in ctrls:
        fit_hole_to_wall(ctrls["archimesh.ctrl_hole"], parent)

    for owner_name, mod_name, role in links["booleans"]:
        owner = bpy.data.objects.get(owner_name)
        mod = owner.modifiers.get(mod_name) if owner is not None else None
        if mod is None or role not in ctrls:
            print("Archimesh: could not reconnect Boolean '%s' on '%s'; run Auto Holes again"
                  % (mod_name, owner_name))
            continue
        mod.object = ctrls[role]


def capture_child_booleans(child):
    return [(mod.name, mod.object, mod.operation, mod.solver)
            for mod in child.modifiers
            if mod.type == 'BOOLEAN' and mod.object is not None]


def restore_child_booleans(child, booleans):
    for name, target, operation, solver in booleans:
        mod = child.modifiers.new(name, 'BOOLEAN')
        mod.object = target
        mod.operation = operation
        mod.solver = solver


# --------------------------------------------------------------------
# Set material to object
# --------------------------------------------------------------------
def set_material(myobject, mymaterial):
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        myobject.data.materials.append(mymaterial)


# --------------------------------------------------------------------
# Set material to selected faces
# --------------------------------------------------------------------
def set_material_faces(myobject, idx):
    bpy.context.view_layer.objects.active = myobject
    myobject.select_set(True)
    bpy.context.object.active_material_index = idx
    if bpy.context.view_layer.objects.active.name == myobject.name:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.material_slot_assign()
        # Deselect
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


# --------------------------------------------------------------------
# Select faces
# --------------------------------------------------------------------
def select_faces(myobject, selface, clear):
    myobject.select_set(True)
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        # deselect everything
        if clear:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')

        # reselect the originally selected face
        bpy.ops.object.mode_set(mode='OBJECT')
        myobject.data.polygons[selface].select = True


# --------------------------------------------------------------------
# Select vertices
# --------------------------------------------------------------------
def select_vertices(myobject, selvertices, clear=True):
    myobject.select_set(True)
    bpy.context.view_layer.objects.active = myobject
    if bpy.context.view_layer.objects.active.name == myobject.name:
        # deselect everything
        if clear:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')

        # Select Vertices
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        sel_mode = bpy.context.tool_settings.mesh_select_mode

        bpy.context.tool_settings.mesh_select_mode = [True, False, False]
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for i in selvertices:
            myobject.data.vertices[i].select = True

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.context.tool_settings.mesh_select_mode = sel_mode
        bpy.ops.object.mode_set(mode='OBJECT')


# --------------------------------------------------------------------
# Mark Seam
# --------------------------------------------------------------------
def mark_seam(myobject):
    # noinspection PyBroadException
    try:
        myobject.select_set(True)
        bpy.context.view_layer.objects.active = myobject
        if bpy.context.view_layer.objects.active.name == myobject.name:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.mark_seam()
            bpy.ops.object.mode_set(mode='OBJECT')
    except:
        bpy.ops.object.mode_set(mode='OBJECT')


# --------------------------------------------------------------------
# Unwrap mesh
# --------------------------------------------------------------------
def unwrap_mesh(myobject, allfaces=True):
    # noinspection PyBroadException
    try:
        myobject.select_set(True)
        bpy.context.view_layer.objects.active = myobject
        if bpy.context.view_layer.objects.active.name == myobject.name:
            # Unwrap
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            if allfaces is True:
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_all()
            bpy.ops.uv.unwrap()
            bpy.ops.object.mode_set(mode='OBJECT')
    except:
        bpy.ops.object.mode_set(mode='OBJECT')


# --------------------------------------------------------------------
# Get Node Index(multilanguage support)
# --------------------------------------------------------------------
def get_node_index(nodes, datatype):
    idx = 0
    for m in nodes:
        if m.type == datatype:
            return idx
        idx += 1

    # Raise rather than fall back to an arbitrary index: a wrong guess silently
    # miswires or deletes nodes (e.g. the Material Output).
    raise LookupError("Archimesh: no node of type %s in material tree" % datatype)


# --------------------------------------------------------------------
# Remove the default surface shader from a new material tree.
# The default was a Diffuse BSDF before 2.80 and is a Principled BSDF since.
# --------------------------------------------------------------------
def remove_default_shader(nodes):
    for node in [n for n in nodes if n.type in {'BSDF_PRINCIPLED', 'BSDF_DIFFUSE'}]:
        nodes.remove(node)


# --------------------------------------------------------------------
# Create cycles diffuse material
# --------------------------------------------------------------------
def create_diffuse_material(matname, replace, r, g, b, rv=0.8, gv=0.8, bv=0.8, mix=0.1, twosides=False):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)  # viewport color
    nodes = mat.node_tree.nodes

    # support for multilanguage
    node = nodes.new('ShaderNodeBsdfDiffuse')
    node.name = 'Diffuse BSDF'
    node.inputs[0].default_value = [r, g, b, 1]
    node.location = 200, 320

    node = nodes.new('ShaderNodeBsdfGlossy')
    node.name = 'Glossy_0'
    node.location = 200, 0

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_0'
    node.inputs[0].default_value = mix
    node.location = 500, 160

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 1100, 160

    # Connect nodes
    outn = nodes['Diffuse BSDF'].outputs[0]
    inn = nodes['Mix_0'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Glossy_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[2]
    mat.node_tree.links.new(outn, inn)

    if twosides is False:
        outn = nodes['Mix_0'].outputs[0]
        inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
        mat.node_tree.links.new(outn, inn)

    if twosides is True:
        node = nodes.new('ShaderNodeNewGeometry')
        node.name = 'Input_1'
        node.location = -80, -70

        node = nodes.new('ShaderNodeBsdfDiffuse')
        node.name = 'Diffuse_1'
        node.inputs[0].default_value = [0.30, 0.30, 0.30, 1]
        node.location = 200, -280

        node = nodes.new('ShaderNodeMixShader')
        node.name = 'Mix_1'
        node.inputs[0].default_value = mix
        node.location = 800, -70

        outn = nodes['Input_1'].outputs[6]
        inn = nodes['Mix_1'].inputs[0]
        mat.node_tree.links.new(outn, inn)

        outn = nodes['Diffuse_1'].outputs[0]
        inn = nodes['Mix_1'].inputs[2]
        mat.node_tree.links.new(outn, inn)

        outn = nodes['Mix_0'].outputs[0]
        inn = nodes['Mix_1'].inputs[1]
        mat.node_tree.links.new(outn, inn)

        outn = nodes['Mix_1'].outputs[0]
        inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
        mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles translucent material
# --------------------------------------------------------------------
def create_translucent_material(matname, replace, r, g, b, rv=0.8, gv=0.8, bv=0.8, mix=0.1):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)  # viewport color
    nodes = mat.node_tree.nodes

    # support for multilanguage
    node = nodes.new('ShaderNodeBsdfDiffuse')
    node.name = 'Diffuse BSDF'
    node.inputs[0].default_value = [r, g, b, 1]
    node.location = 200, 320

    node = nodes.new('ShaderNodeBsdfTranslucent')
    node.name = 'Translucent_0'
    node.location = 200, 0

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_0'
    node.inputs[0].default_value = mix
    node.location = 500, 160

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 1100, 160

    # Connect nodes
    outn = nodes['Diffuse BSDF'].outputs[0]
    inn = nodes['Mix_0'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Translucent_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[2]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Mix_0'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles glass material
# --------------------------------------------------------------------
def create_glass_material(matname, replace, rv=0.333, gv=0.342, bv=0.9):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)
    nodes = mat.node_tree.nodes

    # The default tree's surface shader is not used; this builder wires its own.
    remove_default_shader(nodes)

    node = nodes.new('ShaderNodeLightPath')
    node.name = 'Light_0'
    node.location = 10, 160

    node = nodes.new('ShaderNodeBsdfRefraction')
    node.name = 'Refraction_0'
    node.inputs[2].default_value = 1  # IOR 1.0
    node.location = 250, 400

    node = nodes.new('ShaderNodeBsdfGlossy')
    node.name = 'Glossy_0'
    node.location = 250, 100

    node = nodes.new('ShaderNodeBsdfTransparent')
    node.name = 'Transparent_0'
    node.location = 500, 10

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_0'
    node.inputs[0].default_value = 0.035
    node.location = 500, 160

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_1'
    node.inputs[0].default_value = 0.1
    node.location = 690, 290

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 920, 290

    # Connect nodes
    outn = nodes['Light_0'].outputs[1]
    inn = nodes['Mix_1'].inputs[0]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Refraction_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Glossy_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[2]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Mix_0'].outputs[0]
    inn = nodes['Mix_1'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Transparent_0'].outputs[0]
    inn = nodes['Mix_1'].inputs[2]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Mix_1'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# ---------------------------------------------
# Create cycles transparents material
# --------------------------------------------------------------------
def create_transparent_material(matname, replace, r=1, g=1, b=1, alpha=0):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (r, g, b, 1.0)
    nodes = mat.node_tree.nodes

    # The default tree's surface shader is not used; this builder wires its own.
    remove_default_shader(nodes)

    node = nodes.new('ShaderNodeBsdfTransparent')
    node.name = 'Transparent_0'
    node.location = 250, 160
    node.inputs[0].default_value = [r, g, b, alpha]

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 700, 160

    # Connect nodes
    outn = nodes['Transparent_0'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles glossy material
# --------------------------------------------------------------------
def create_glossy_material(matname, replace, r, g, b, rv=0.578, gv=0.555, bv=0.736, rvalue=0.2):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)
    nodes = mat.node_tree.nodes

    # The default tree's surface shader is not used; this builder wires its own.
    remove_default_shader(nodes)

    node = nodes.new('ShaderNodeBsdfGlossy')
    node.name = 'Glossy_0'
    node.inputs[0].default_value = [r, g, b, 1]
    node.inputs[1].default_value = rvalue
    node.location = 200, 160

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 700, 160

    # Connect nodes
    outn = nodes['Glossy_0'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles emission material
# --------------------------------------------------------------------
def create_emission_material(matname, replace, r, g, b, energy):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    nodes = mat.node_tree.nodes

    # The default tree's surface shader is not used; this builder wires its own.
    remove_default_shader(nodes)

    node = nodes.new('ShaderNodeEmission')
    node.name = 'Emission_0'
    node.inputs[0].default_value = [r, g, b, 1]
    node.inputs[1].default_value = energy
    node.location = 200, 160

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 700, 160

    # Connect nodes
    outn = nodes['Emission_0'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles glass material
# --------------------------------------------------------------------
def create_old_glass_material(matname, replace, rv=0.352716, gv=0.760852, bv=0.9):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)
    nodes = mat.node_tree.nodes

    # The default tree's surface shader is not used; this builder wires its own.
    remove_default_shader(nodes)

    node = nodes.new('ShaderNodeLightPath')
    node.name = 'Light_0'
    node.location = 10, 160

    node = nodes.new('ShaderNodeBsdfGlass')
    node.name = 'Glass_0'
    node.location = 250, 300

    node = nodes.new('ShaderNodeBsdfTransparent')
    node.name = 'Transparent_0'
    node.location = 250, 0

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_0'
    node.inputs[0].default_value = 0.1
    node.location = 500, 160

    node = nodes.new('ShaderNodeMixShader')
    node.name = 'Mix_1'
    node.inputs[0].default_value = 0.1
    node.location = 690, 290

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 920, 290

    # Connect nodes
    outn = nodes['Light_0'].outputs[1]
    inn = nodes['Mix_0'].inputs[0]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Light_0'].outputs[2]
    inn = nodes['Mix_1'].inputs[0]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Glass_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Transparent_0'].outputs[0]
    inn = nodes['Mix_0'].inputs[2]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Mix_0'].outputs[0]
    inn = nodes['Mix_1'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Mix_1'].outputs[0]
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles brick texture material
# --------------------------------------------------------------------
def create_brick_material(matname, replace, r, g, b, rv=0.8, gv=0.636, bv=0.315):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)
    nodes = mat.node_tree.nodes

    # support for multilanguage
    principled_node = nodes[get_node_index(nodes, 'BSDF_PRINCIPLED')]

    principled_node.inputs[0].default_value = [r, g, b, 1]
    principled_node.location = 500, 160

    output_node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    output_node.location = 700, 160

    brick_node = nodes.new('ShaderNodeTexBrick')
    brick_node.name = 'Brick_0'
    # By name: positional indices change between Blender versions.
    brick_node.inputs['Mortar'].default_value = [0.407, 0.411, 0.394, 1]
    brick_node.inputs['Scale'].default_value = 3
    brick_node.inputs['Mortar Size'].default_value = 0.001
    brick_node.inputs['Brick Width'].default_value = 0.60
    brick_node.inputs['Row Height'].default_value = 0.30
    brick_node.location = 300, 160

    rgb_node = nodes.new('ShaderNodeRGB')
    rgb_node.name = 'RGB_0'
    rgb_node.outputs[0].default_value = [r, g, b, 1]
    rgb_node.location = 70, 160

    # Connect nodes
    outn = rgb_node.outputs['Color']
    inn = brick_node.inputs['Color1']
    mat.node_tree.links.new(outn, inn)

    inn = brick_node.inputs['Color2']
    mat.node_tree.links.new(outn, inn)

    outn = brick_node.outputs['Color']
    inn = principled_node.inputs['Base Color']
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Create cycles fabric texture material
# --------------------------------------------------------------------
def create_fabric_material(matname, replace, r, g, b, rv=0.8, gv=0.636, bv=0.315):
    # Avoid duplicate materials
    if replace is False:
        matlist = bpy.data.materials
        for m in matlist:
            if m.name == matname:
                return m
    # Create material
    mat = bpy.data.materials.new(matname)
    mat.diffuse_color = (rv, gv, bv, 1.0)
    nodes = mat.node_tree.nodes

    # support for multilanguage
    node = nodes.new('ShaderNodeBsdfDiffuse')
    node.name = 'Diffuse BSDF'
    node.inputs[0].default_value = [r, g, b, 1]
    node.location = 810, 270

    node = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')]
    node.location = 1210, 320

    node = nodes.new('ShaderNodeTexCoord')
    node.name = 'UVCoordinates'
    node.location = 26, 395

    node = nodes.new('ShaderNodeMapping')
    node.name = 'UVMapping'
    node.location = 266, 380
    node.inputs['Scale'].default_value[0] = 1000
    node.inputs['Scale'].default_value[1] = 1000
    node.inputs['Scale'].default_value[2] = 1000

    # ===========================================================================
    # Image texture
    # ===========================================================================
    # Load image file.

    realpath = path.join(path.dirname(__file__), "images", "fabric_diffuse.png")
    print("Loading: " + realpath)
    try:
        img = bpy.data.images.load(realpath)
    except:
        raise NameError("Cannot load image %s" % realpath)

    # Create image texture from image
    ctex = bpy.data.textures.new('ColorTex', type='IMAGE')
    ctex.image = img

    node = nodes.new('ShaderNodeTexImage')
    node.name = 'Image1'
    node.image = ctex.image
    node.location = 615, 350

    node = nodes.new('ShaderNodeBsdfTransparent')
    node.name = 'Transparent1'
    node.location = 810, 395
    node.inputs[0].default_value = [r, g, b, 1]

    node = nodes.new('ShaderNodeAddShader')
    node.name = 'Add1'
    node.location = 1040, 356

    # Connect nodes
    outn = nodes['UVCoordinates'].outputs['UV']
    inn = nodes['UVMapping'].inputs['Vector']
    mat.node_tree.links.new(outn, inn)

    outn = nodes['UVMapping'].outputs['Vector']
    inn = nodes['Image1'].inputs['Vector']
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Image1'].outputs['Color']
    inn = nodes['Diffuse BSDF'].inputs['Color']
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Transparent1'].outputs['BSDF']
    inn = nodes['Add1'].inputs[0]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Diffuse BSDF'].outputs['BSDF']
    inn = nodes['Add1'].inputs[1]
    mat.node_tree.links.new(outn, inn)

    outn = nodes['Add1'].outputs['Shader']
    inn = nodes[get_node_index(nodes, 'OUTPUT_MATERIAL')].inputs[0]
    mat.node_tree.links.new(outn, inn)

    return mat


# --------------------------------------------------------------------
# Copy bin file
# --------------------------------------------------------------------
def copy_binfile(fromfile, tofile):
    with open(fromfile, 'rb') as f1:
        with open(tofile, 'wb') as f2:
            while True:
                mybytes = f1.read(1024)
                if mybytes:
                    f2.write(mybytes)
                else:
                    break


# --------------------------------------------------------------------
# Parent object (keep positions)
# --------------------------------------------------------------------
def parentobject(parentobj, childobj):
    # noinspection PyBroadException
    try:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = parentobj
        parentobj.select_set(True)
        childobj.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
        return True
    except:
        return False


# ------------------------------------------------------------------------------
# Create control box
#
# objName: Object name
# x: size x axis
# y: size y axis
# z: size z axis
# tube: True create a tube, False only sides
# ------------------------------------------------------------------------------
def create_control_box(objname, x, y, z, tube=True):
    myvertex = [(-x / 2, 0, 0.0),
                (-x / 2, y, 0.0),
                (x / 2, y, 0.0),
                (x / 2, 0, 0.0),
                (-x / 2, 0, z),
                (-x / 2, y, z),
                (x / 2, y, z),
                (x / 2, 0, z)]

    if tube is True:
        myfaces = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (3, 7, 4, 0), (2, 6, 7, 3), (5, 4, 7, 6)]
    else:
        myfaces = [(0, 4, 5, 1), (2, 6, 7, 3)]

    mesh = bpy.data.meshes.new(objname)
    myobject = bpy.data.objects.new(objname, mesh)

    myobject.location = bpy.context.scene.cursor.location
    bpy.context.collection.objects.link(myobject)

    mesh.from_pydata(myvertex, [], myfaces)
    mesh.update(calc_edges=True)

    return myobject


# ------------------------------------------------------------------------------
# Remove all children objects
# ------------------------------------------------------------------------------
def remove_children(myobject):
    # Remove children
    for child in myobject.children:
        # noinspection PyBroadException
        try:
            # noinspection PyBroadException
            try:
                # remove child relationship
                for grandchild in child.children:
                    grandchild.parent = None
                # remove modifiers
                # Data API, not bpy.ops: the operator acts on the active object, not on child.
                child.modifiers.clear()
            except:
                pass
            # clear child data
            if child.type == 'MESH':
                old = child.data
                child.select_set(True)
                bpy.ops.object.delete()
                bpy.data.meshes.remove(old)
            if child.type == 'CURVE':
                child.select_set(True)
                bpy.ops.object.delete()
        except:
            pass


# --------------------------------------------------------------------
# Get all parents
# --------------------------------------------------------------------
def get_allparents(myobj):
    obj = myobj
    mylist = []
    while obj.parent is not None:
        mylist.append(obj)
        objp = obj.parent
        obj = objp

    mylist.append(obj)

    return mylist


# --------------------------------------------------------------------
# Verify all faces are in vertice group to avoid Blander crash
#
# Review the faces array and remove any vertex out of the range
# this avoid any bug that can appear avoiding Blender crash
# --------------------------------------------------------------------
def check_mesh_errors(myvertices, myfaces):
    vmax = len(myvertices)

    f = 0
    for face in myfaces:
        for v in face:
            if v < 0 or v > vmax:
                print("Face=" + str(f) + "->removed vertex=" + str(v))
                myfaces[f].remove(v)
        f += 1

    return myfaces
