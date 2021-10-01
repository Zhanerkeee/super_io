import bpy
import os
from bpy.props import (EnumProperty,
                       StringProperty,
                       BoolProperty,
                       CollectionProperty,
                       IntProperty,
                       FloatProperty,
                       PointerProperty)
from bpy.types import PropertyGroup

from . import __folder_name__


def get_pref():
    """get preferences of this plugin"""
    return bpy.context.preferences.addons.get(__folder_name__).preferences


class OperatorInputProperty(PropertyGroup):
    name: StringProperty(name='Property')
    value: StringProperty(name='Value')


def correct_blidname(self, context):
    if self.bl_idname.startswith('bpy.ops.'):
        self.bl_idname = self.bl_idname[8:]
    if self.bl_idname.endswith('()'):
        self.bl_idname = self.bl_idname[:-2]


class ExtensionOperatorProperty(PropertyGroup):
    use: BoolProperty(name='Use', default=True)
    name: StringProperty(name='Extension')
    bl_idname: StringProperty(name='Operator Identifier', update=correct_blidname)
    prop_list: CollectionProperty(type=OperatorInputProperty)


class SPIO_OT_OperatorInputAction(bpy.types.Operator):
    """Add / Remove current prop"""
    bl_idname = "wm.spio_operator_input_action"
    bl_label = "Operator Props Operate"
    bl_options = {'REGISTER', 'UNDO'}

    extension_list_index: IntProperty()
    prop_index: IntProperty()
    action: EnumProperty(items=[
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
    ])

    def execute(self, context):
        pref = get_pref()
        item = pref.extension_list[self.extension_list_index]

        if self.action == 'ADD':
            item.prop_list.add()
        else:
            item.prop_list.remove(self.prop_index)

        return {'FINISHED'}


class SPIO_OT_ExtensionListAction(bpy.types.Operator):
    """Add / Remove current config"""
    bl_idname = "wm.spio_extension_list_action"
    bl_label = "Config Operate"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    action: EnumProperty(items=[
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
    ])

    def execute(self, context):
        pref = get_pref()
        if self.action == 'ADD':
            pref.extension_list.add()
        else:
            pref.extension_list.remove(self.index)

        return {'FINISHED'}


class SPIO_Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    extension_list: CollectionProperty(type=ExtensionOperatorProperty)

    def draw(self, context):
        layout = self.layout.column()

        row = layout.row()
        row.alignment = 'CENTER'
        row.scale_y = 1.25
        row.operator('spio.config_import', icon='IMPORT')
        row.operator('spio.config_export', icon='EXPORT')

        row = layout.row(align=True)
        row.alignment = 'LEFT'

        for extension_list_index, item in enumerate(self.extension_list):
            col = layout.box().column()

            row = col.split(factor=0.75)
            # row.alert = True
            row.prop(item, 'use')
            d = row.operator('wm.spio_extension_list_action', text='Remove', icon='PANEL_CLOSE')
            d.action = 'REMOVE'
            d.index = extension_list_index

            row = col.row()
            row.label(text='File Extension')
            row.label(text='Operator Identifier')

            row = col.row()
            row.prop(item, 'name', text='')
            row.prop(item, 'bl_idname', text='')

            col.separator()

            box = col.box().column()
            row = box.row()
            row.label(text='Property Name')
            row.label(text='Property Value')

            for prop_index, prop_item in enumerate(item.prop_list):
                row = box.row()

                row.prop(prop_item, 'name', text='')
                row.prop(prop_item, 'value', text='')

                d = row.operator('wm.spio_operator_input_action', text='', icon='PANEL_CLOSE', emboss=False)
                d.action = 'REMOVE'
                d.extension_list_index = extension_list_index
                d.prop_index = prop_index

            box.separator()

            row = box.row()
            row.alignment = 'LEFT'
            d = row.operator('wm.spio_operator_input_action', text='Add Property', icon='ADD', emboss=False)
            d.action = 'ADD'
            d.extension_list_index = extension_list_index

        row = layout.row(align=True)
        row.alignment = 'LEFT'
        row.operator('wm.spio_extension_list_action', text='Add Extension Config', icon='FILE_NEW',
                     emboss=False).action = 'ADD'


def register():
    bpy.utils.register_class(OperatorInputProperty)
    bpy.utils.register_class(SPIO_OT_OperatorInputAction)
    bpy.utils.register_class(ExtensionOperatorProperty)
    bpy.utils.register_class(SPIO_OT_ExtensionListAction)
    bpy.utils.register_class(SPIO_Preference)


def unregister():
    bpy.utils.unregister_class(OperatorInputProperty)
    bpy.utils.unregister_class(SPIO_OT_OperatorInputAction)
    bpy.utils.unregister_class(ExtensionOperatorProperty)
    bpy.utils.unregister_class(SPIO_OT_ExtensionListAction)
    bpy.utils.unregister_class(SPIO_Preference)
