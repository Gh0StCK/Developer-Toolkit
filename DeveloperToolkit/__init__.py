bl_info = {
    "name": "Developer Toolkit",
    "blender": (3, 0, 0),
    "category": "Development",
    "author": "Stanislav Kolesnikov",
    "version": (1, 0, 0),
    "description": "Инструменты для разработки аддонов Blender. Перезагрузка аддонов из исходников без ручного ZIP.",
    "location": "View 3D > Sidebar > Dev",
}

import bpy
import os
import sys
import zipfile
import tempfile
import datetime
import pathlib

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, UIList


# ------------------------- УТИЛИТЫ -------------------------

def force_full_ui_refresh():
    """Принудительно обновить интерфейс Blender (все области/регионы)."""
    wm = bpy.context.window_manager
    if not wm:
        return
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES', 'OUTLINER', 'TEXT_EDITOR'}:
                area.tag_redraw()
            for region in area.regions:
                region.tag_redraw()


def get_addon_item(context, index):
    """Вернуть элемент списка аддонов по индексу или None."""
    addons = context.scene.dev_toolkit_addons
    if 0 <= index < len(addons):
        return addons[index]
    return None


def validate_addon_path(path: str) -> tuple[bool, str]:
    """Проверить, что путь существует и содержит __init__.py."""
    if not path:
        return False, "Путь к исходникам не задан."
    if not os.path.exists(path):
        return False, f"Путь не существует: {path}"
    init_file = os.path.join(path, "__init__.py")
    if not os.path.exists(init_file):
        return False, f"Файл __init__.py не найден в {path}"
    return True, ""


class AddonValidator:
    """Валидатор и фабрика элементов списка аддонов."""

    @staticmethod
    def validate_addon_data(addon_module: str, addon_path: str, context) -> tuple[bool, str]:
        """Проверка корректности данных перед добавлением в список."""
        if not addon_module:
            return False, "Введите имя модуля аддона."
        ok, err = validate_addon_path(addon_path)
        if not ok:
            return False, err
        # Проверка на дубликат имени
        for item in context.scene.dev_toolkit_addons:
            if item.name == addon_module:
                return False, f"Аддон {addon_module} уже в списке."
        return True, ""

    @staticmethod
    def create_addon_item(context, addon_module: str, addon_path: str):
        """Создать новый элемент списка аддонов."""
        item = context.scene.dev_toolkit_addons.add()
        item.name = addon_module
        item.path = addon_path
        item.is_enabled = addon_module in context.preferences.addons
        item.auto_reload = True
        item.last_reload = "Еще не перезагружался"
        force_full_ui_refresh()
        return item


# ------------------------- ДАННЫЕ -------------------------

class AddonDevToolkitSettings(PropertyGroup):
    """Настройки Developer Toolkit."""
    autosave_on_reload: BoolProperty(
        name="Автосохранение",
        description="Автоматически сохранять файл перед перезагрузкой аддона",
        default=True,
    )
    clear_console: BoolProperty(
        name="Очистка консоли",
        description="Очищать консоль Python перед перезагрузкой",
        default=True,
    )


class AddonItem(PropertyGroup):
    """Элемент списка аддонов."""
    name: StringProperty(
        name="Имя аддона",
        description="Имя модуля аддона (используется для включения/отключения)",
        default="",
    )
    path: StringProperty(
        name="Путь к исходникам",
        description="Полный путь к директории с исходниками аддона",
        default="",
        subtype='DIR_PATH',
    )
    is_enabled: BoolProperty(
        name="Активен",
        description="Аддон активен в Blender",
        default=False,
    )
    auto_reload: BoolProperty(
        name="Автообновление",
        description="Включить аддон в массовое обновление",
        default=True,
    )
    last_reload: StringProperty(
        name="Последняя перезагрузка",
        description="Время последней перезагрузки аддона",
        default="",
    )


# ------------------------- ОПЕРАТОРЫ -------------------------

class DEV_OT_AddAddon(Operator):
    """Добавить аддон в список для разработки."""
    bl_idname = "dev.add_addon"
    bl_label = "Добавить аддон"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: StringProperty(
        name="Файл аддона",
        description="Выберите __init__.py или папку аддона",
        default="",
        subtype='FILE_PATH',
    )
    directory: StringProperty(name="Директория", subtype='DIR_PATH')
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})
    filter_glob: StringProperty(default="__init__.py;*.py", options={'HIDDEN'})

    def invoke(self, context, event):
        # Открываем стандартный файловый браузер без промежуточных окон
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Если пользователь отменил выбор
        chosen = os.path.normpath(self.filepath or self.directory or "")
        if not chosen:
            self.report({'WARNING'}, "Файл не выбран")
            return {'CANCELLED'}

        # Получаем директорию аддона и его имя
        addon_dir = chosen if os.path.isdir(chosen) else os.path.dirname(chosen)
        addon_dir = os.path.normpath(addon_dir)
        if not os.path.exists(addon_dir):
            self.report({'ERROR'}, f"Путь не существует: {addon_dir}")
            return {'CANCELLED'}
        addon_name = os.path.basename(addon_dir)

        # Здесь при желании можно добавить строгую проверку на __init__.py
        # init_path = os.path.join(addon_dir, "__init__.py")
        # if not os.path.exists(init_path): ...

        # Проверка на дубликат
        for item in context.scene.dev_toolkit_addons:
            if item.name == addon_name:
                self.report({'ERROR'}, f"Аддон {addon_name} уже в списке.")
                return {'CANCELLED'}

        AddonValidator.create_addon_item(context, addon_name, addon_dir)
        force_full_ui_refresh()
        self.report({'INFO'}, f"Аддон {addon_name} добавлен в список")
        return {'FINISHED'}


class DEV_OT_RemoveAddon(Operator):
    """Удалить аддон из списка."""
    bl_idname = "dev.remove_addon"
    bl_label = "Удалить из списка"
    bl_options = {'REGISTER', 'UNDO'}

    addon_index: IntProperty()

    def execute(self, context):
        addons = context.scene.dev_toolkit_addons
        if 0 <= self.addon_index < len(addons):
            addon_name = addons[self.addon_index].name
            addons.remove(self.addon_index)
            self.report({'INFO'}, f"Аддон {addon_name} удален из списка")
            force_full_ui_refresh()
            return {'FINISHED'}
        self.report({'ERROR'}, "Неверный индекс аддона")
        return {'CANCELLED'}


class DEV_OT_ReloadAddon(Operator):
    """Перезагрузить аддон из исходников."""
    bl_idname = "dev.reload_addon"
    bl_label = "Перезагрузить аддон"
    bl_options = {'REGISTER', 'UNDO'}

    addon_index: IntProperty()
    skip_unregister: BoolProperty(
        default=False,
        description="Пропустить отключение аддона (полезно при ошибках)",
    )

    # ---- вспомогательные методы ----

    def create_zip(self, source_dir: str, addon_name: str, zip_path: str) -> bool:
        """Создать ZIP-архив из директории с исходниками."""
        src = pathlib.Path(source_dir)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in src.rglob("*"):
                if p.is_dir():
                    continue
                if "__pycache__" in p.parts or ".git" in p.parts:
                    continue
                if p.suffix in {".pyc", ".tmp"}:
                    continue
                rel = p.relative_to(src)
                arc = os.path.join(addon_name, str(rel))
                zf.write(str(p), arc)
        return os.path.exists(zip_path)

    def clean_addon_modules(self, addon_name: str):
        """Удалить модули аддона из sys.modules, аккуратно вызвав unregister()."""
        names = [n for n in list(sys.modules.keys())
                 if n == addon_name or n.startswith(addon_name + ".")]

        for n in names:
            mod = sys.modules.get(n)
            if not mod:
                continue
            try:
                unregister = getattr(mod, "unregister", None)
                if callable(unregister):
                    unregister()
            except Exception:
                pass

        for n in names:
            sys.modules.pop(n, None)

    # ---- основной execute ----

    def execute(self, context):
        addon_item = get_addon_item(context, self.addon_index)
        if addon_item is None:
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}

        source_dir = addon_item.path
        addon_name = addon_item.name

        ok, err = validate_addon_path(source_dir)
        if not ok:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        # Автосохранение и очистка консоли
        settings = context.scene.dev_toolkit_settings
        if settings.autosave_on_reload and bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
        if settings.clear_console:
            try:
                bpy.ops.console.clear({'window': context.window,
                                       'screen': context.window.screen,
                                       'area': next(a for a in context.window.screen.areas if a.type == 'CONSOLE'),
                                       'region': next(r for r in next(a for a in context.window.screen.areas if a.type == 'CONSOLE').regions if r.type == 'WINDOW')})
            except Exception:
                pass

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(tempfile.gettempdir(), f"{addon_name}_{timestamp}.zip")

        try:
            if not self.create_zip(source_dir, addon_name, zip_path):
                self.report({'ERROR'}, "ZIP-архив не был создан")
                return {'CANCELLED'}

            # Отключение
            if addon_name in context.preferences.addons:
                if not self.skip_unregister:
                    try:
                        bpy.ops.preferences.addon_disable(module=addon_name)
                    except Exception:
                        pass
            # Чистка модулей всегда
            self.clean_addon_modules(addon_name)

            # Установка и включение
            bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
            bpy.ops.preferences.addon_enable(module=addon_name)
            addon_item.is_enabled = True

        except Exception as e:
            addon_item.is_enabled = False
            self.report({'ERROR'}, f"Ошибка при перезагрузке аддона: {e}")
            return {'CANCELLED'}
        finally:
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception:
                pass

        addon_item.last_reload = datetime.datetime.now().strftime("%H:%M:%S")
        self.report({'INFO'}, f"Аддон {addon_name} перезагружен")
        force_full_ui_refresh()
        return {'FINISHED'}


class DEV_OT_ReloadSelectedAddons(Operator):
    """Перезагрузить все отмеченные аддоны."""
    bl_idname = "dev.reload_selected_addons"
    bl_label = "Обновить выбранные"
    bl_options = {'REGISTER', 'UNDO'}

    skip_unregister: BoolProperty(
        default=False,
        description="Пропустить отключение аддонов (если стандартная перезагрузка глючит).",
    )

    @classmethod
    def description(cls, context, properties):
        if properties.skip_unregister:
            return ("Перезагрузка без отключения: полезно, если unregister падает "
                    "или нужно сохранить состояние в памяти.")
        else:
            return ("Полная перезагрузка: отключить → установить из ZIP → включить. "
                    "Рекомендуемый способ.")

    def execute(self, context):
        reloaded = 0
        for index, addon in enumerate(context.scene.dev_toolkit_addons):
            if addon.auto_reload:
                bpy.ops.dev.reload_addon(addon_index=index, skip_unregister=self.skip_unregister)
                reloaded += 1
        self.report({'INFO'}, f"Обновлено аддонов: {reloaded}")
        return {'FINISHED'}


class DEV_OT_ChangeAddonPath(Operator):
    """Изменить путь к исходникам аддона."""
    bl_idname = "dev.change_addon_path"
    bl_label = "Изменить путь"
    bl_options = {'REGISTER', 'UNDO'}

    addon_index: IntProperty()

    # Используем filepath/directory для диалога
    filepath: StringProperty(
        name="Путь к исходникам",
        description="Полный путь к директории с исходниками аддона",
        default="",
        subtype='DIR_PATH',
    )
    directory: StringProperty(name="Директория", subtype='DIR_PATH')
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})

    def invoke(self, context, event):
        addon = get_addon_item(context, self.addon_index)
        if addon:
            self.filepath = addon.path
            self.directory = addon.path
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        new_path = os.path.normpath(self.filepath or self.directory or "")
        ok, err = validate_addon_path(new_path)
        if not ok:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}
        addon = get_addon_item(context, self.addon_index)
        if not addon:
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
        addon.path = new_path
        self.report({'INFO'}, f"Путь к исходникам аддона {addon.name} обновлён")
        force_full_ui_refresh()
        return {'FINISHED'}


class DEV_OT_ChangeAddonName(Operator):
    """Изменить имя аддона."""
    bl_idname = "dev.change_addon_name"
    bl_label = "Изменить имя"
    bl_options = {'REGISTER', 'UNDO'}

    addon_index: IntProperty()
    new_name: StringProperty(name="Новое имя", description="Новое имя аддона", default="")

    def invoke(self, context, event):
        addon_item = get_addon_item(context, self.addon_index)
        if not addon_item:
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
        self.new_name = addon_item.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        addon_item = get_addon_item(context, self.addon_index)
        if not addon_item:
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
        new_name = (self.new_name or "").strip()
        if not new_name:
            self.report({'ERROR'}, "Введите новое имя аддона")
            return {'CANCELLED'}
        # Проверка на коллизию имён
        for i, it in enumerate(context.scene.dev_toolkit_addons):
            if it.name == new_name and i != self.addon_index:
                self.report({'ERROR'}, f"Аддон с именем {new_name} уже существует")
                return {'CANCELLED'}
        addon_item.name = new_name
        self.report({'INFO'}, f"Имя аддона изменено на {new_name}")
        force_full_ui_refresh()
        return {'FINISHED'}


# ------------------------- UI -------------------------

class DEV_UL_AddonsList(UIList):
    """Список аддонов для разработки."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "auto_reload", text="")
            main_row = row.row()
            main_row.prop(item, "name", text="", emboss=False, icon='PLUGIN')
            edit_op = row.operator("dev.change_addon_name", text="", icon='GREASEPENCIL', emboss=False)
            edit_op.addon_index = index
            if item.is_enabled:
                main_row.label(text="", icon='CHECKMARK')
            remove_op = row.operator("dev.remove_addon", text="", icon='X', emboss=False)
            remove_op.addon_index = index
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name)


class DEV_PT_DevToolkitPanel(Panel):
    """Панель инструментов разработчика."""
    bl_label = "Developer Toolkit"
    bl_idname = "DEV_PT_DevToolkitPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dev'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        main_box = layout.box()

        row = main_box.row(align=True)
        row.operator("dev.add_addon", text="Добавить аддон", icon='ADD')

        if len(scene.dev_toolkit_addons) > 0:
            row = main_box.row()
            row.template_list(
                "DEV_UL_AddonsList", "",
                scene, "dev_toolkit_addons",
                scene, "dev_toolkit_addon_index",
                rows=3
            )

        if 0 <= scene.dev_toolkit_addon_index < len(scene.dev_toolkit_addons):
            addon = scene.dev_toolkit_addons[scene.dev_toolkit_addon_index]
            info_box = main_box.box()

            path_row = info_box.row(align=True)
            path_row.label(text="", icon='FILE_FOLDER')
            path_row.label(text=addon.path or "(путь не задан)")
            path_op = path_row.operator("dev.change_addon_path", text="", icon='FILEBROWSER', emboss=False)
            path_op.addon_index = scene.dev_toolkit_addon_index

            time_row = info_box.row(align=True)
            time_row.label(text="", icon='TIME')
            if addon.last_reload and addon.last_reload != "Еще не перезагружался":
                time_row.label(text=f"Обновлён в {addon.last_reload}")
            else:
                time_row.label(text="Еще не обновлялся", icon='ERROR')

        box = main_box.box()
        row = box.row(align=True)
        row.operator("dev.reload_selected_addons", text="Обновить", icon='FILE_REFRESH')
        op = row.operator("dev.reload_selected_addons", text="Обновить без отключения", icon='LOOP_BACK')
        op.skip_unregister = True

        settings_box = layout.box()
        row = settings_box.row()
        row.label(text="Настройки:", icon='PREFERENCES')
        row = settings_box.row(align=True)
        split = row.split(factor=0.5, align=True)
        split.prop(scene.dev_toolkit_settings, "autosave_on_reload")
        split.prop(scene.dev_toolkit_settings, "clear_console")


# ------------------------- РЕГИСТРАЦИЯ -------------------------

classes = [
    AddonDevToolkitSettings,
    AddonItem,
    DEV_OT_AddAddon,
    DEV_OT_RemoveAddon,
    DEV_OT_ReloadAddon,
    DEV_OT_ReloadSelectedAddons,
    DEV_OT_ChangeAddonPath,
    DEV_OT_ChangeAddonName,
    DEV_UL_AddonsList,
    DEV_PT_DevToolkitPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dev_toolkit_settings = PointerProperty(type=AddonDevToolkitSettings)
    bpy.types.Scene.dev_toolkit_addons = CollectionProperty(type=AddonItem)
    bpy.types.Scene.dev_toolkit_addon_index = IntProperty(default=0)


def unregister():
    del bpy.types.Scene.dev_toolkit_addon_index
    del bpy.types.Scene.dev_toolkit_addons
    del bpy.types.Scene.dev_toolkit_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
