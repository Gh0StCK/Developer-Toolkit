# Этот файл нужен для обозначения директории как Python-пакета

bl_info = {
    "name": "Developer Toolkit",
    "blender": (3, 0, 0),
    "category": "Development",
    "author": "Stanislav Kolesnikov",
    "version": (1, 0, 0),
    "description": "Инструменты для разработки аддонов Blender. Позволяет быстро перезагружать аддоны без ручного создания ZIP.",
    "location": "View 3D > Sidebar > Dev",
}

import bpy
import os
import zipfile
import tempfile
import shutil
import datetime
import time
import pathlib
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList

# Сохранение настроек между сессиями
class AddonDevToolkitSettings(PropertyGroup):
    """Настройки Developer Toolkit"""
    autosave_on_reload: BoolProperty(
        name="Автосохранение",
        description="Автоматически сохранять файл перед перезагрузкой аддона",
        default=True
    )
    clear_console: BoolProperty(
        name="Очистка консоли",
        description="Очищать консоль Python перед перезагрузкой",
        default=True
    )

class AddonItem(PropertyGroup):
    """Элемент списка аддонов"""
    name: StringProperty(
        name="Имя аддона",
        description="Имя модуля аддона (используется для включения/отключения)",
        default=""
    )
    path: StringProperty(
        name="Путь к исходникам",
        description="Полный путь к директории с исходниками аддона",
        default="",
        subtype='DIR_PATH'
    )
    is_enabled: BoolProperty(
        name="Активен",
        description="Аддон активен в Blender",
        default=False
    )
    auto_reload: BoolProperty(
        name="Автообновление",
        description="Включить этот аддон в массовое обновление",
        default=True
    )
    last_reload: StringProperty(
        name="Последняя перезагрузка",
        description="Время последней перезагрузки аддона",
        default=""
    )

def force_update_ui(context):
    """Общая функция для обновления UI"""
    if context.area:
        context.area.tag_redraw()

def force_full_ui_refresh():
    """Принудительное обновление всего интерфейса Blender"""
    # Обновляем все окна и области
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            # Особое внимание областям типа VIEW_3D и PROPERTIES
            if area.type in {'VIEW_3D', 'PROPERTIES'}:
                area.tag_redraw()
            # Обновляем все регионы в области
            for region in area.regions:
                region.tag_redraw()

class AddonValidator:
    """Класс для валидации и создания аддонов"""
    @staticmethod
    def validate_addon_data(addon_module: str, addon_path: str, context) -> tuple[bool, str]:
        """Проверяет данные аддона на корректность
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not addon_module:
            return False, "Введите имя модуля аддона"
            
        if not addon_path:
            return False, "Выберите путь к исходникам аддона"
            
        if not os.path.exists(addon_path):
            return False, f"Путь не существует: {addon_path}"
            
        # Проверяем наличие аддона в списке
        for item in context.scene.dev_toolkit_addons:
            if item.name == addon_module:
                return False, f"Аддон {addon_module} уже в списке"
                
        return True, ""
    
    @staticmethod
    def create_addon_item(context, addon_module: str, addon_path: str) -> AddonItem:
        """Создает новый элемент аддона"""
        item = context.scene.dev_toolkit_addons.add()
        item.name = addon_module
        item.path = addon_path
        item.is_enabled = addon_module in context.preferences.addons
        item.last_reload = "Еще не перезагружался"
        
        # Обновляем интерфейс
        force_full_ui_refresh()
                
        return item

class DEV_OT_AddAddon(Operator):
    """Добавить аддон в список для разработки"""
    bl_idname = "dev.add_addon"
    bl_label = "Добавить аддон"
    bl_options = {'REGISTER', 'UNDO'}
    
    addon_module: StringProperty(
        name="Имя модуля",
        description="Имя модуля аддона (напр. 'AutoApplyScale')",
        default=""
    )
    
    addon_path: StringProperty(
        name="Путь к исходникам",
        description="Полный путь к директории с исходниками аддона",
        default="",
        subtype='DIR_PATH'
    )
    
    use_folder_name: BoolProperty(
        name="Использовать имя папки",
        description="Автоматически использовать имя папки как имя модуля",
        default=True
    )
    
    def update_module_name(self, context):
        """Обновляет имя модуля на основе имени директории"""
        if self.addon_path and self.use_folder_name:
            dir_name = os.path.basename(os.path.normpath(self.addon_path))
            clean_name = ''.join(c for c in dir_name if c.isalnum() or c == '_')
            if clean_name:
                self.addon_module = clean_name
                # Обновляем только текущую область
                if context.area:
                    context.area.tag_redraw()
    
    def invoke(self, context, event):
        self.addon_module = ""
        self.addon_path = ""
        self.use_folder_name = True
        return context.window_manager.invoke_props_dialog(self)
        
    def draw(self, context):
        layout = self.layout
        
        # Добавляем заголовок с инструкцией
        layout.label(text="Выберите директорию с аддоном для разработки:")
        
        # Поле пути с подсказкой
        path_box = layout.box()
        path_row = path_box.row()
        path_row.prop(self, "addon_path", expand=True)
        if not self.addon_path:
            path_box.label(text="👉 Укажите путь к директории с исходниками аддона", icon='INFO')
        
        # Автоматически обновляем имя модуля если включена опция
        if self.addon_path and self.use_folder_name:
            self.update_module_name(context)
            
        # Поле имени модуля с подсказкой
        name_box = layout.box()
        name_box.prop(self, "use_folder_name", text="Использовать имя папки")
        name_box.prop(self, "addon_module")
        
        if self.addon_path:
            if self.use_folder_name:
                name_box.label(text="✓ Имя модуля автоматически определено из пути", icon='CHECKMARK')
            else:
                name_box.label(text="✎ Введите желаемое имя модуля", icon='GREASEPENCIL')
        else:
            name_box.label(text="⚠️ Сначала выберите путь к аддону", icon='ERROR')
    
    def execute(self, context):
        # Нормализуем путь
        normalized_path = os.path.normpath(self.addon_path)
        
        # Валидация данных
        is_valid, error_message = AddonValidator.validate_addon_data(
            self.addon_module, 
            normalized_path,
            context
        )
        
        if not is_valid:
            self.report({'ERROR'}, error_message)
            return {'CANCELLED'}
            
        # Создание аддона
        AddonValidator.create_addon_item(context, self.addon_module, normalized_path)
        
        # Принудительное обновление всего интерфейса
        force_full_ui_refresh()
        
        self.report({'INFO'}, f"Аддон {self.addon_module} добавлен в список")
        return {'FINISHED'}

class DEV_OT_RemoveAddon(Operator):
    """Удалить аддон из списка"""
    bl_idname = "dev.remove_addon"
    bl_label = "Удалить из списка"
    bl_options = {'REGISTER', 'UNDO'}
    
    addon_index: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.addon_index >= 0 and self.addon_index < len(context.scene.dev_toolkit_addons):
            addon_name = context.scene.dev_toolkit_addons[self.addon_index].name
            context.scene.dev_toolkit_addons.remove(self.addon_index)
            self.report({'INFO'}, f"Аддон {addon_name} удален из списка")
        
        return {'FINISHED'}

class DEV_OT_ReloadAddon(Operator):
    """Перезагрузить аддон из исходников"""
    bl_idname = "dev.reload_addon"
    bl_label = "Перезагрузить аддон"
    bl_options = {'REGISTER', 'UNDO'}
    
    addon_index: bpy.props.IntProperty()
    skip_unregister: bpy.props.BoolProperty(
        default=False,
        description="Пропустить отключение аддона (полезно при ошибках)"
    )
    
    def create_zip(self, source_dir, addon_name, zip_path):
        """Создать ZIP-архив из директории с исходниками"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            source_path = pathlib.Path(source_dir)
            
            for file_path in source_path.rglob('*'):
                # Игнорируем директорию __pycache__ и временные файлы
                if '__pycache__' in str(file_path) or file_path.name.endswith(('.pyc', '.tmp')):
                    continue
                
                # Игнорируем .git директорию
                if '.git' in str(file_path):
                    continue
                    
                # Получаем относительный путь
                relative_path = file_path.relative_to(source_path)
                
                # Добавляем имя аддона в путь, чтобы файлы были в директории
                archive_path = os.path.join(addon_name, str(relative_path))
                
                # Если это директория, создаем пустую директорию в ZIP
                if file_path.is_dir():
                    info = zipfile.ZipInfo(archive_path + '/')
                    zipf.writestr(info, '')
                else:
                    # Добавляем файл
                    zipf.write(file_path, archive_path)
        
        return True
    
    def clean_addon_modules(self, addon_name):
        """Очищает все модули аддона из sys.modules"""
        import sys
        import importlib
        
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name == addon_name or module_name.startswith(addon_name + '.'):
                modules_to_remove.append(module_name)
        
        # Сначала пытаемся выгрузить модули правильно
        for module_name in modules_to_remove:
            try:
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    if hasattr(module, 'unregister'):
                        try:
                            module.unregister()
                        except:
                            pass
                    importlib.reload(module)
            except:
                pass
            
        # Затем удаляем их из sys.modules
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
    
    def execute(self, context):
        if self.addon_index < 0 or self.addon_index >= len(context.scene.dev_toolkit_addons):
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
        
        start_time = time.time()
        addon_item = context.scene.dev_toolkit_addons[self.addon_index]
        source_dir = addon_item.path
        addon_name = addon_item.name
        
        # Проверяем существование директории и __init__.py
        if not os.path.exists(source_dir):
            self.report({'ERROR'}, f"Директория исходников не найдена: {source_dir}")
            return {'CANCELLED'}
            
        init_file = os.path.join(source_dir, "__init__.py")
        if not os.path.exists(init_file):
            self.report({'ERROR'}, f"Файл __init__.py не найден в {source_dir}")
            return {'CANCELLED'}
        
        # Автосохранение и очистка консоли
        if context.scene.dev_toolkit_settings.autosave_on_reload and bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
            
        if context.scene.dev_toolkit_settings.clear_console:
            try:
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'CONSOLE':
                            for region in area.regions:
                                if region.type == 'WINDOW':
                                    ctx = {'window': window, 'screen': window.screen, 'area': area, 'region': region}
                                    bpy.ops.console.clear(ctx)
            except Exception as e:
                self.report({'WARNING'}, f"Не удалось очистить консоль: {str(e)}")
        
        # Создаем временный ZIP-файл
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(tempfile.gettempdir(), f"{addon_name}_{timestamp}.zip")
        
        try:
            self.create_zip(source_dir, addon_name, zip_path)
            
            if not os.path.exists(zip_path):
                self.report({'ERROR'}, "ZIP-архив не был создан")
                return {'CANCELLED'}
            
            # Принудительно отключаем и удаляем модуль аддона
            if addon_name in context.preferences.addons:
                if not self.skip_unregister:
                    try:
                        # Пробуем отключить через preferences
                        bpy.ops.preferences.addon_disable(module=addon_name)
                    except:
                        pass
                    
                # В любом случае очищаем модули
                self.clean_addon_modules(addon_name)
            
            # Устанавливаем и включаем аддон
            bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
            bpy.ops.preferences.addon_enable(module=addon_name)
            addon_item.is_enabled = True
            
            # Удаляем временный ZIP-файл
            os.remove(zip_path)
            
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка при перезагрузке аддона: {str(e)}")
            addon_item.is_enabled = False
            return {'CANCELLED'}
        
        elapsed_time = time.time() - start_time
        addon_item.last_reload = datetime.datetime.now().strftime("%H:%M:%S")
        self.report({'INFO'}, f"Аддон успешно перезагружен за {elapsed_time:.2f} секунд")
        
        return {'FINISHED'}

class DEV_OT_ReloadSelectedAddons(Operator):
    """Перезагрузить все отмеченные аддоны

    Стандартная перезагрузка:
    - Отключает аддон
    - Создает новый ZIP
    - Устанавливает новую версию
    - Включает аддон"""
    bl_idname = "dev.reload_selected_addons"
    bl_label = "Обновить выбранные"
    bl_options = {'REGISTER', 'UNDO'}
    
    skip_unregister: bpy.props.BoolProperty(
        default=False,
        description="Пропустить отключение аддонов (используйте, если стандартная перезагрузка вызывает ошибки)",
    )
    
    @classmethod
    def description(cls, context, properties):
        if properties.skip_unregister:
            return """Перезагрузить отмеченные аддоны без их отключения

Используйте этот вариант, если:
- В аддоне есть ошибка, мешающая корректному отключению
- Нужно сохранить состояние аддона в памяти
- Отключение может нарушить работу других аддонов"""
        else:
            return """Перезагрузить отмеченные аддоны (рекомендуемый способ)

Полностью перезагружает аддоны:
- Отключает аддон
- Создает новый ZIP
- Устанавливает новую версию
- Включает аддон"""
    
    def execute(self, context):
        reloaded = 0
        for index, addon in enumerate(context.scene.dev_toolkit_addons):
            if addon.auto_reload:
                # Используем существующий оператор для перезагрузки
                bpy.ops.dev.reload_addon(addon_index=index, skip_unregister=self.skip_unregister)
                reloaded += 1
        
        self.report({'INFO'}, f"Обновлено аддонов: {reloaded}")
        return {'FINISHED'}

class DEV_OT_ChangeAddonPath(Operator):
    """Изменить путь к исходникам аддона"""
    bl_idname = "dev.change_addon_path"
    bl_label = "Изменить путь"
    bl_options = {'REGISTER', 'UNDO'}
    
    addon_index: bpy.props.IntProperty()
    new_path: StringProperty(
        name="Новый путь",
        description="Новый путь к исходникам аддона",
        default="",
        subtype='DIR_PATH'
    )
    
    # Используем filepath вместо new_path для открытия файлового диалога
    filepath: StringProperty(
        name="Путь к исходникам",
        description="Полный путь к директории с исходниками аддона",
        default="",
        subtype='DIR_PATH'
    )
    
    # Настройки для отображения диалога выбора директории
    directory: StringProperty(
        name="Директория",
        subtype='DIR_PATH'
    )
    
    filter_folder: BoolProperty(
        default=True,
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        addon = context.scene.dev_toolkit_addons[self.addon_index]
        self.filepath = addon.path
        self.directory = addon.path
        # Открываем диалог выбора файла/директории
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # Используем путь из диалога выбора файла
        new_path = self.filepath
        
        if not new_path:
            self.report({'ERROR'}, "Укажите путь к исходникам аддона")
            return {'CANCELLED'}
            
        if not os.path.exists(new_path):
            self.report({'ERROR'}, f"Путь не существует: {new_path}")
            return {'CANCELLED'}
            
        init_file = os.path.join(new_path, "__init__.py")
        if not os.path.exists(init_file):
            self.report({'ERROR'}, f"Файл __init__.py не найден в {new_path}")
            return {'CANCELLED'}
            
        addon = context.scene.dev_toolkit_addons[self.addon_index]
        addon.path = new_path
        self.report({'INFO'}, f"Путь к исходникам аддона {addon.name} обновлен")
        return {'FINISHED'}

class DEV_OT_ChangeAddonName(Operator):
    """Изменить имя аддона"""
    bl_idname = "dev.change_addon_name"
    bl_label = "Изменить имя"
    bl_options = {'REGISTER', 'UNDO'}
    
    addon_index: bpy.props.IntProperty()
    new_name: StringProperty(
        name="Новое имя",
        description="Новое имя аддона",
        default=""
    )
    
    def invoke(self, context, event):
        # Проверяем валидность индекса
        if self.addon_index < 0 or self.addon_index >= len(context.scene.dev_toolkit_addons):
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
            
        addon = context.scene.dev_toolkit_addons[self.addon_index]
        self.new_name = addon.name
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        # Проверяем валидность индекса
        if self.addon_index < 0 or self.addon_index >= len(context.scene.dev_toolkit_addons):
            self.report({'ERROR'}, "Неверный индекс аддона")
            return {'CANCELLED'}
            
        if not self.new_name:
            self.report({'ERROR'}, "Введите новое имя аддона")
            return {'CANCELLED'}
        
        current_addon = context.scene.dev_toolkit_addons[self.addon_index]
            
        # Проверяем, не занято ли имя другим аддоном
        for i, item in enumerate(context.scene.dev_toolkit_addons):
            if item.name == self.new_name and i != self.addon_index:
                self.report({'ERROR'}, f"Аддон с именем {self.new_name} уже существует")
                return {'CANCELLED'}
            
        current_addon.name = self.new_name
        self.report({'INFO'}, f"Имя аддона изменено на {self.new_name}")
        return {'FINISHED'}

class DEV_UL_AddonsList(UIList):
    """Список аддонов для разработки"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            # Галочка для включения/отключения автообновления
            row.prop(item, "auto_reload", text="")
            
            # Основная информация об аддоне
            main_row = row.row()
            main_row.prop(item, "name", text="", emboss=False, icon='PLUGIN')
            
            # Кнопка редактирования имени
            edit_op = row.operator("dev.change_addon_name", text="", icon='GREASEPENCIL', emboss=False)
            edit_op.addon_index = index
            
            # Индикатор активности аддона
            if item.is_enabled:
                main_row.label(text="", icon='CHECKMARK')
            
            # Кнопка удаления
            remove_op = row.operator("dev.remove_addon", text="", icon='X', emboss=False)
            remove_op.addon_index = index
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

class DEV_PT_DevToolkitPanel(Panel):
    """Панель инструментов разработчика"""
    bl_label = "Developer Toolkit"
    bl_idname = "DEV_PT_DevToolkitPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dev'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Основной контейнер с фиксированной высотой
        main_box = layout.box()
        
        # Кнопка добавления нового аддона
        row = main_box.row()
        row.operator("dev.add_addon", text="Добавить аддон", icon='ADD')
        
        # Список аддонов
        if len(scene.dev_toolkit_addons) > 0:
            row = main_box.row()
            row.template_list("DEV_UL_AddonsList", "", scene, "dev_toolkit_addons", scene, "dev_toolkit_addon_index", rows=1)
            
            # Информация о выбранном аддоне
            if scene.dev_toolkit_addon_index >= 0 and scene.dev_toolkit_addon_index < len(scene.dev_toolkit_addons):
                addon = scene.dev_toolkit_addons[scene.dev_toolkit_addon_index]
                info_box = main_box.box()
                
                # Путь к исходникам
                path_row = info_box.row(align=True)
                path_row.label(text="", icon='FILE_FOLDER')
                path_row.label(text=addon.path)
                path_op = path_row.operator("dev.change_addon_path", text="", icon='FILEBROWSER', emboss=False)
                path_op.addon_index = scene.dev_toolkit_addon_index
                
                # Время последнего обновления
                time_row = info_box.row(align=True)
                time_row.label(text="", icon='TIME')
                if addon.last_reload != "Еще не перезагружался":
                    time_row.label(text=f"Обновлен в {addon.last_reload}")
                else:
                    time_row.label(text="Еще не обновлялся", icon='ERROR')
            
            # Кнопки массового обновления
            box = main_box.box()
            row = box.row(align=True)
            row.operator("dev.reload_selected_addons", text="Обновить", icon='FILE_REFRESH')
            op = row.operator("dev.reload_selected_addons", text="Обновить без отключения", icon='LOOP_BACK')
            op.skip_unregister = True
        
        # Настройки в боксе с компактным расположением
        settings_box = layout.box()
        row = settings_box.row()
        row.label(text="Настройки:", icon='PREFERENCES')
        
        # Размещаем настройки в один ряд внутри бокса
        row = settings_box.row(align=True)
        split = row.split(factor=0.5, align=True)
        split.prop(scene.dev_toolkit_settings, "autosave_on_reload")
        split.prop(scene.dev_toolkit_settings, "clear_console")

# Список всех классов для регистрации
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
    DEV_PT_DevToolkitPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Регистрируем свойства
    bpy.types.Scene.dev_toolkit_settings = bpy.props.PointerProperty(type=AddonDevToolkitSettings)
    bpy.types.Scene.dev_toolkit_addons = bpy.props.CollectionProperty(type=AddonItem)
    bpy.types.Scene.dev_toolkit_addon_index = bpy.props.IntProperty(default=0)

def unregister():
    # Удаляем свойства
    del bpy.types.Scene.dev_toolkit_addon_index
    del bpy.types.Scene.dev_toolkit_addons
    del bpy.types.Scene.dev_toolkit_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 