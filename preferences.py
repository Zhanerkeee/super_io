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
import rna_keymap_ui


def get_pref():
    """get preferences of this plugin"""
    return bpy.context.preferences.addons.get(__folder_name__).preferences


class OperatorProperty(PropertyGroup):
    name: StringProperty(name='Property')
    value: StringProperty(name='Value')


def correct_blidname(self, context):
    if self.bl_idname.startswith('bpy.ops.'):
        self.bl_idname = self.bl_idname[8:]
    if self.bl_idname.endswith('()'):
        self.bl_idname = self.bl_idname[:-2]


def correct_name(self, context):
    pref = get_pref()
    names = [item.name for item in pref.config_list if item.name == self.name and item.name != '']
    if len(names) != 1:
        self.name += '(1)'


class ExtensionOperatorProperty(PropertyGroup):
    # USE
    use_config: BoolProperty(name='Use', default=True)
    # UI
    color_tag: EnumProperty(name='Color Tag',
                            items=[
                                (f'COLOR_0{i}', '', '', f'COLLECTION_COLOR_0{i}' if i != 0 else 'OUTLINER_COLLECTION',
                                 i) for i in range(0, 9)])
    # information
    name: StringProperty(name='Preset Name', update=correct_name)
    description: StringProperty(name='Description',
                                description='Show in the popup operator tips')
    # extension
    extension: StringProperty(name='Extension')
    # custom match rule
    match_rule: EnumProperty(name='Match Rule',
                             items=[('NONE', 'None (Default)', ''),
                                    ('STARTSWITH', 'Startswith', ''),
                                    ('ENDSWITH', 'Endswith', ''),
                                    ('IN', 'Contain', ''),
                                    ('REGEX', 'Regex (Match or not)', ''), ],
                             default='NONE', description='Matching rule of the name')

    match_value: StringProperty(name='Match Value', default='')

    # remove grease pencil from default because this design is only allow one default importer
    operator_type: EnumProperty(
        name='Operator Type',
        items=[
            ("", "Default", "Default blender build-in importer", "CUBE", 0),
            None,
            ('DEFAULT_DAE', 'Collada (.dae)', '', 'CUBE', 99),
            ('DEFAULT_ABC', 'Alembic (.abc)', '', 'CUBE', 98),
            ('DEFAULT_USD', 'USD (.usd/.usda/.usdc)', '', 'CUBE', 97),
            ('DEFAULT_SVG', 'SVG (.svg)', '', 'GP_SELECT_POINTS', 96),
            ('DEFAULT_PLY', 'Stanford (.ply)', '', 'CUBE', 95),
            ('DEFAULT_STL', 'Stl (.stl)', '', 'CUBE', 94),
            ('DEFAULT_FBX', 'FBX (.fbx)', '', 'CUBE', 93),
            ('DEFAULT_GLTF', 'glTF 2.0 (.gltf/.glb)', '', 'CUBE', 92),
            ('DEFAULT_OBJ', 'Wavefront (.obj)', '', 'CUBE', 91),
            ('DEFAULT_X3D', 'X3D (.x3d/.wrl)', '', 'CUBE', 90),

            ("", "Blend File", "Blend File", "BLENDER", 0),
            None,
            ('APPEND_BLEND_MATERIAL', 'Append Materials', 'Append All', 'MATERIAL', 1),
            ('APPEND_BLEND_COLLECTION', 'Append Collections', 'Append All',
             'OUTLINER_COLLECTION', 2),
            ('APPEND_BLEND_OBJECT', 'Append Objects', 'Append All', 'OBJECT_DATA', 3),
            ('APPEND_BLEND_WORLD', 'Append Worlds', 'Append All', 'WORLD', 4),
            ('APPEND_BLEND_NODETREE', 'Append Node Groups', 'Append All', 'NODETREE', 5),

            None,
            ('LINK_BLEND_MAT', 'Link Materials', 'Load All', 'MATERIAL', 11),
            ('LINK_BLEND_COLLECTION', 'Link Collections', 'Load All',
             'OUTLINER_COLLECTION', 12),
            ('LINK_BLEND_OBJECT', 'Link Objects', 'Load All', 'OBJECT_DATA',
             13),
            ('LINK_BLEND_WORLD', 'Link Worlds', 'Load All', 'WORLD', 14),
            ('LINK_BLEND_NODE', 'Link Node Groups', 'Load All', 'NODETREE',
             15),

            ("", "Add-ons", "Custom operator and properties input", "USER", 0),
            # ('ADDONS_SVG', 'Grease Pencil (.svg)', '', 'GP_SELECT_STROKES', 100),
            ('ADDONS_BLEND_MATERIAL', 'Append and assign material',
             'Import material from a single file and assign it to active object', 'MATERIAL', 101),
            ('ADDONS_BLEND_WORLD', 'Append and assign world',
             'Import world from a single file and set it as context world', 'WORLD', 102),
            None,
            ('CUSTOM', 'Custom', '', 'USER', 666),
        ],
        default='DEFAULT_OBJ', )

    # custom operator
    bl_idname: StringProperty(name='Operator Identifier', update=correct_blidname)
    context: EnumProperty(name="Operator Context",
                          items=[("INVOKE_DEFAULT", "INVOKE_DEFAULT", ''),
                                 ("EXEC_DEFAULT", "EXEC_DEFAULT", ''), ],
                          default='EXEC_DEFAULT')
    prop_list: CollectionProperty(type=OperatorProperty)


class OperatorPropAction:
    bl_label = "Operator Props Operate"
    bl_options = {'REGISTER', 'UNDO'}

    config_list_index: IntProperty()
    prop_index: IntProperty()
    action = None

    def execute(self, context):
        pref = get_pref()
        item = pref.config_list[self.config_list_index]

        if self.action == 'ADD':
            item.prop_list.add()
        elif self.action == 'REMOVE':
            item.prop_list.remove(self.prop_index)

        return {'FINISHED'}


class SPIO_OT_OperatorPropAdd(OperatorPropAction, bpy.types.Operator):
    bl_idname = "wm.spio_operator_prop_add"
    bl_label = "Add Prop"

    action = 'ADD'


class SPIO_OT_OperatorPropRemove(OperatorPropAction, bpy.types.Operator):
    bl_idname = "wm.spio_operator_prop_remove"
    bl_label = "Remove Prop"

    action = 'REMOVE'


from .ops.utils import convert_value


class SPIO_OT_ExtensionListAction:
    """Add / Remove / Copy current config"""
    bl_label = "Config Operate"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    action = None

    def execute(self, context):
        pref = get_pref()

        if self.action == 'ADD':
            new_item = pref.config_list.add()
            new_item.name = f'Config{len(pref.config_list)}'
            pref.config_list_index = len(pref.config_list) - 1

        elif self.action == 'REMOVE':
            pref.config_list.remove(self.index)
            pref.config_list_index = self.index - 1 if self.index != 0 else 0

        elif self.action == 'COPY':
            src_item = pref.config_list[self.index]

            new_item = pref.config_list.add()

            for key in src_item.__annotations__.keys():
                value = getattr(src_item, key)
                if key != 'prop_list':
                    setattr(new_item, key, value)
                # prop list
                if len(new_item.prop_list) != 0:
                    for prop_index, prop_item in enumerate(src_item.prop_list):
                        prop, value = prop_item.name, prop_item.value
                        # skip if the prop is not filled
                        if prop == '' or value == '': continue
                        prop_item = new_item.prop_list.add()
                        setattr(prop_item, prop, convert_value(value))

            pref.config_list_index = len(pref.config_list) - 1

        elif self.action in {'UP', 'DOWN'}:
            my_list = pref.config_list
            index = pref.config_list_index
            neighbor = index + (-1 if self.action == 'UP' else 1)
            my_list.move(neighbor, index)
            self.move_index(context)

        return {'FINISHED'}

    def move_index(self, context):
        pref = get_pref()
        index = pref.config_list_index
        new_index = index + (-1 if self.action == 'UP' else 1)
        pref.config_list_index = max(0, min(new_index, len(pref.config_list) - 1))


class SPIO_OT_ExtensionListAdd(SPIO_OT_ExtensionListAction, bpy.types.Operator):
    bl_idname = "spio.config_list_add"
    bl_label = "Add Config"

    action = 'ADD'


class SPIO_OT_ExtensionListRemove(SPIO_OT_ExtensionListAction, bpy.types.Operator):
    bl_idname = "spio.config_list_remove"
    bl_label = "Remove Config"

    action = 'REMOVE'


class SPIO_OT_ExtensionListCopy(SPIO_OT_ExtensionListAction, bpy.types.Operator):
    bl_idname = "spio.config_list_copy"
    bl_label = "Copy Config"

    action = 'COPY'


class SPIO_OT_ExtensionListMoveUP(SPIO_OT_ExtensionListAction, bpy.types.Operator):
    bl_idname = "spio.config_list_move_up"
    bl_label = 'Move Up'

    action = 'UP'


class SPIO_OT_ExtensionListMoveDown(SPIO_OT_ExtensionListAction, bpy.types.Operator):
    bl_idname = "spio.config_list_move_down"
    bl_label = 'Move Down'

    action = 'DOWN'


class ConfigListFilterProperty(PropertyGroup):
    filter_type: EnumProperty(name='Filter Type', items=[
        ('name', 'Name', ''),
        ('extension', 'Extension', ''),
        ('match_rule', 'Match Rule', ''),
        ('color_tag', 'Color Tag', ''),
    ], default='name')
    filter_name: StringProperty(default='', name="Name")

    filter_extension: StringProperty(default='', name="Extension")

    filter_match_rule: EnumProperty(name='Match Rule',
                                    items=[('NONE', 'None (Default)', ''),
                                           ('STARTSWITH', 'Startswith', ''),
                                           ('ENDSWITH', 'Endswith', ''),
                                           ('IN', 'Contain', ''),
                                           ('REGEX', 'Regex (Match or not)', ''), ],
                                    default='NONE', description='Matching rule of the name')

    filter_color_tag: EnumProperty(name='Color Tag',
                                   items=[(f'COLOR_0{i}', '', '',
                                           f'COLLECTION_COLOR_0{i}' if i != 0 else 'OUTLINER_COLLECTION', i) for i in
                                          range(0, 9)])

    reverse: BoolProperty(name="Reverse", default=False,
                          options=set(),
                          description="Reverse", )


class SPIO_OT_color_tag_selector(bpy.types.Operator):
    bl_idname = 'spio.color_tag_selector'
    bl_label = 'Color Tag'

    index: IntProperty(name='Config list Index')

    dep_classes = []

    @classmethod
    def poll(cls, context):
        return len(get_pref().config_list) != 0

    def execute(self, context):
        # clear
        for cls in self.dep_classes:
            bpy.utils.unregister_class(cls)
        self.dep_classes.clear()

        pref = get_pref()
        item = pref.config_list[self.index]

        for i in range(0, 9):
            # set color tag
            def execute(self, context):
                self.item.color_tag = f'COLOR_0{self.index}'
                context.area.tag_redraw()
                return {'FINISHED'}

            # define
            op_cls = type("DynOp",
                          (bpy.types.Operator,),
                          {"bl_idname": f'wm.spio_color_tag_{i}',
                           "bl_label": 'Select',
                           "bl_description": f'Color {i}',
                           "execute": execute,
                           # custom pass in
                           'index': i,
                           'item': item, },
                          )

            self.dep_classes.append(op_cls)

        # register
        for cls in self.dep_classes:
            bpy.utils.register_class(cls)

        def draw(cls, context):
            layout = cls.layout
            row = cls.layout.row(align=True)
            row.scale_x = 1.12
            for i in range(0, 9):
                row.operator(f'wm.spio_color_tag_{i}', text='',
                             icon=f'COLLECTION_COLOR_0{i}' if i != 0 else 'X')

        context.window_manager.popup_menu(draw, title="Color", icon='OUTLINER_COLLECTION')

        return {'FINISHED'}


class PREF_UL_ConfigList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()

        row.operator('spio.color_tag_selector', text='',
                     icon=f'COLLECTION_{item.color_tag}' if item.color_tag != 'COLOR_00' else 'OUTLINER_COLLECTION').index = index
        row.prop(item, 'name', text='', emboss=False)
        row.prop(item, 'extension', text='', emboss=False)
        row.prop(item, 'use_config', text='')

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        filter = context.window_manager.spio_filter

        items = getattr(data, propname)
        ordered = []

        filtered = bpy.types.UI_UL_list.filter_items_by_name(getattr(filter, 'filter_' + filter.filter_type),
                                                             self.bitflag_filter_item,
                                                             items,
                                                             filter.filter_type.removeprefix('filter_'),
                                                             reverse=filter.reverse)

        try:
            ordered = bpy.types.UI_UL_list.sort_items_helper(items, filter.filter_type.removeprefix('filter_'))
        except:
            pass

        return filtered, ordered

        # OLD STYLE
        #################################################
        # filtered = [self.bitflag_filter_item] * len(items)
        # if filter.filter_type == 'extension':
        #     for i, item in enumerate(items):
        #         if item.extension != filter.filter_extension and filter.filter_extension != '':
        #             filtered[i] &= ~self.bitflag_filter_item

        # # invert
        # if filtered and filter.reverse:
        #     show_flag = self.bitflag_filter_item & ~self.bitflag_filter_item
        #     for i, bitflag in enumerate(filtered):
        #         if bitflag == show_flag:
        #             filtered[i] = self.bitflag_filter_item
        #         else:
        #             filtered[i] &= ~self.bitflag_filter_item
        # ordered = bpy.types.UI_UL_list.sort_items_helper(items, lambda i: len(i.extension), True)
        #################################################


class SPIO_MT_ConfigIOMenu(bpy.types.Menu):
    bl_label = "Config Import/Export"
    bl_idname = "SPIO_PT_ConfigIOMenu"

    def draw(self, context):
        layout = self.layout
        layout.operator('spio.import_config', icon='IMPORT')
        layout.operator('spio.export_config', icon='EXPORT')


class SPIO_Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    # UI
    ui: EnumProperty(name='UI', items=[
        ('SETTINGS', 'Settings', '', 'PREFERENCES', 0),
        ('CONFIG', 'Config', '', 'PRESET', 1),
        ('URL', 'Help', '', 'URL', 2),
    ],default = 'CONFIG')
    use_N_panel: BoolProperty(name='Use N Panel', default=True)

    # Settings
    force_unicode: BoolProperty(name='Force Unicode',
                                description='Force to use "utf-8" to decode filepath \nOnly enable when your system coding "utf-8"',
                                default=False)
    report_time: BoolProperty(name='Report Time',
                              description='Report import time', default=True)

    disable_warning_rules: BoolProperty(name='Close Warning Rules', default=False)
    # Preset
    config_list: CollectionProperty(type=ExtensionOperatorProperty)
    config_list_index: IntProperty(min=0, default=0)

    def draw(self, context):
        layout = self.layout.split(factor=0.2)
        layout.scale_y = 1.2

        col = layout.column(align=True)
        col.prop(self, 'ui', expand=True)

        col.separator(factor=2)

        col = layout.column()
        if self.ui == 'SETTINGS':
            self.draw_settings(context, col)

        elif self.ui == 'CONFIG':
            self.draw_config(context, col)

        elif self.ui == 'URL':
            self.draw_url(context, col)

    def draw_url(self, context, layout):
        box = layout.box()
        box.label(text='Help', icon='HELP')
        row = box.row()
        row.operator('wm.url_open', text='Manual').url = 'http://atticus-lv.gitee.io/super_io/#/'

        box = layout.box()
        box.label(text='Sponsor: 只剩一瓶辣椒酱', icon='FUND')
        row = box.row()
        row.operator('wm.url_open', text='斑斓魔法CG官网', icon='URL').url = 'https://www.blendermagic.cn/'
        row.row(align=True).operator('wm.url_open', text='辣椒B站频道',
                                     icon='URL').url = 'https://space.bilibili.com/35723238'

        box.label(text='Developer: Atticus', icon='MONKEY')
        row = box.row()
        row.operator('wm.url_open', text='Atticus Github', icon='URL').url = 'https://github.com/atticus-lv'
        row.row(align=True).operator('wm.url_open', text='AtticusB站频道',
                                     icon='URL').url = 'https://space.bilibili.com/1509173'

    def draw_settings(self, context, layout):
        col = layout.column(align=True).box()
        col.use_property_split = True

        row = col.row(align=True)
        row.alert = True
        row.prop(self, 'force_unicode', text='')
        row.label(text='Force Unicode')

        row = col.row(align=True)
        row.prop(self, 'use_N_panel', text='')
        row.label(text='Use N Panel')

        row = col.row(align=True)
        row.prop(self, 'report_time', text='')
        row.label(text='Report Time')

        row = col.row(align=True)
        row.prop(self, 'disable_warning_rules', text='')
        row.label(text='Close Warning Rules')

        col = layout.column(align=True).box()
        col.use_property_split = True
        self.draw_keymap(context, col)

    def draw_keymap(self, context, layout):
        col = layout.box().column()
        col.label(text="Keymap", icon="KEYINGSET")
        km = None
        wm = context.window_manager
        kc = wm.keyconfigs.user

        old_km_name = ""
        get_kmi_l = []

        for km_add, kmi_add in addon_keymaps:
            for km_con in kc.keymaps:
                if km_add.name == km_con.name:
                    km = km_con
                    break

            for kmi_con in km.keymap_items:
                if kmi_add.idname == kmi_con.idname and kmi_add.name == kmi_con.name:
                    get_kmi_l.append((km, kmi_con))

        get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

        for km, kmi in get_kmi_l:
            if not km.name == old_km_name:
                col.label(text=str(km.name), icon="DOT")

            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

            old_km_name = km.name

    def draw_config(self, context, layout):
        row = layout.column().row(align=False)
        row.alignment = 'CENTER'

        row.scale_y = 1.25
        row.scale_x = 1.5

        row.menu(SPIO_MT_ConfigIOMenu.bl_idname, text='', icon='FILE_TICK')
        # filter panel
        filter = context.window_manager.spio_filter
        if filter.filter_type == 'extension':
            row.prop(filter, 'filter_extension', text="", icon='VIEWZOOM')
        elif filter.filter_type == 'name':
            row.prop(filter, "filter_name", text="", icon='VIEWZOOM')
        elif filter.filter_type == 'match_rule':
            row.prop(filter, "filter_match_rule", icon='SHORTDISPLAY', text='')
        elif filter.filter_type == 'color_tag':
            row.prop(filter, 'filter_color_tag', expand=True)

        row.popover(panel="SPIO_PT_ListFilterPanel", icon="FILTER", text='')

        # split left and right
        row = layout.column(align=True).row()
        row_left = row

        row_l = row_left.row(align=False)
        col_list = row_l.column(align=True)
        col_btn = row_l.column(align=True)

        col_list.template_list(
            "PREF_UL_ConfigList", "Config List",
            self, "config_list",
            self, "config_list_index")

        col_btn.operator('spio.config_list_add', text='', icon='ADD')

        d = col_btn.operator('spio.config_list_remove', text='', icon='REMOVE')
        d.index = self.config_list_index

        col_btn.separator()

        col_btn.operator('spio.config_list_move_up', text='', icon='TRIA_UP')
        col_btn.operator('spio.config_list_move_down', text='', icon='TRIA_DOWN')

        col_btn.separator()

        c = col_btn.operator('spio.config_list_copy', text='', icon='DUPLICATE')
        c.index = self.config_list_index

        if len(self.config_list) == 0: return
        item = self.config_list[self.config_list_index]
        if not item: return

        col = layout.column()
        box = col.box().column()
        box.label(text=item.name, icon='EDITMODE_HLT')

        box.use_property_split = True
        box1 = box.box()
        box1.prop(item, 'name')
        box1.prop(item, 'extension')
        box1.prop(item, 'description')

        box2 = box.box()
        box2.prop(item, 'match_rule')
        if item.match_rule != 'NONE':
            box2.prop(item, 'match_value', text='Match Value' if item.match_rule != 'REGEX' else 'Expression')
            if not self.disable_warning_rules:
                box3 = box2.box().column(align=True)
                box3.alert = True
                sub_row = box3.row()
                sub_row.label(text="Warning", icon='ERROR')
                sub_row.prop(self, 'disable_warning_rules', toggle=True)
                box4 = box3
                # box4.alert = False
                box4.label(text="1. If file name not matching this rule")
                box4.label(text="   It will search for the next config which match")
                box4.label(text="2. If no config’s rule is matched")
                box4.label(
                    text="   It will popup all available importer in a menu after import all file that match a rule")

        box3 = box.box()
        box3.prop(item, 'operator_type')

        if item.operator_type == 'CUSTOM':
            box3.prop(item, 'context')
            box3.prop(item, 'bl_idname')

            # ops props
            col = box3.box().column()

            row = col.row(align=True)
            if item.bl_idname != '':
                text = 'bpy.ops.' + item.bl_idname + '(' + 'filepath,' + '{prop=value})'
            else:
                text = 'No Operator Found'
            row.alert = True
            row.label(icon='TOOL_SETTINGS', text=text)

            if item.bl_idname != '':
                row = col.row()
                if len(item.prop_list) != 0:
                    row.label(text='Property')
                    row.label(text='Value')
                for prop_index, prop_item in enumerate(item.prop_list):
                    row = col.row(align=True)
                    row.prop(prop_item, 'name', text='')
                    row.prop(prop_item, 'value', text='')

                    d = row.operator('wm.spio_operator_prop_remove', text='', icon='PANEL_CLOSE', emboss=False)
                    d.config_list_index = self.config_list_index
                    d.prop_index = prop_index

                row = col.row(align=True)
                row.alignment = 'LEFT'
                d = row.operator('wm.spio_operator_prop_add', text='Add Property', icon='ADD', emboss=False)
                d.config_list_index = self.config_list_index


classes = [
    OperatorProperty,
    SPIO_OT_OperatorPropAdd, SPIO_OT_OperatorPropRemove,

    ExtensionOperatorProperty,
    SPIO_OT_ExtensionListAdd, SPIO_OT_ExtensionListRemove, SPIO_OT_ExtensionListCopy, SPIO_OT_ExtensionListMoveUP,
    SPIO_OT_ExtensionListMoveDown,

    SPIO_OT_color_tag_selector,

    ConfigListFilterProperty, PREF_UL_ConfigList,
    SPIO_MT_ConfigIOMenu,
    SPIO_Preference
]

addon_keymaps = []


def add_keybind():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.super_import", 'V', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new("wm.super_import", 'V', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))


def remove_keybind():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)

    addon_keymaps.clear()


def register():
    add_keybind()

    for cls in classes:
        bpy.utils.register_class(cls)

    try:
        for key in get_pref().config_list.__annotations__.keys():
            the_value = getattr(ExtensionOperatorProperty, key)
    except Exception as e:
        print(e)

    bpy.types.WindowManager.spio_filter = PointerProperty(type=ConfigListFilterProperty)


def unregister():
    remove_keybind()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.spio_filter
