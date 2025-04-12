Tell me thanks.
<p><a href="https://www.buymeacoffee.com/gh0stck29u"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a></p>
# 🧩 Developer Toolkit for Blender

**Developer Toolkit** — это удобный инструмент для разработчиков аддонов Blender, который позволяет:

- 🔹 Быстро добавлять и отслеживать аддоны из локальных папок
- 🔁 Перезагружать аддоны с автоматическим .zip-пакетированием
- ⚙️ Управлять путями, названиями модулей и статусами активации
- 🧠 Перезагружать сразу несколько аддонов одной кнопкой
- ❌ Перезагружать даже при ошибках (с пропуском `unregister`)
- 🧼 Избавиться от ручного zip и переустановки при разработке

---

## 📦 Возможности

| 🔧 Функция             | 📝 Описание                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| ➕ **Add Addon**        | Укажи путь и имя модуля — аддон появится в списке                           |
| 🔁 **Reload Addon**     | Автоматически создаёт `.zip`, переустанавливает и активирует аддон         |
| ⚙️ **Auto Save**        | Опционально сохраняет `.blend` перед перезагрузкой                         |
| 🧼 **Clear Console**    | Очищает консоль Python перед перезагрузкой                                 |
| 🧠 **Batch Reloading**  | Перезагружает все выбранные аддоны одной кнопкой                           |
| ✏️ **Edit Path & Name** | Позволяет переименовать или изменить путь к исходникам                     |
| 👁 **UI Refresh**       | Принудительно обновляет интерфейс                                          |
| ✅ **Active Status**    | Показывает, активен ли аддон сейчас                                         |

---

## 🧩 Совместимость

- ✅ Blender **3.x – 4.4+**
- 🛠 Разработано для локальной работы с исходниками
- 💼 Подходит как для одного аддона, так и для пачки в разработке

---

## 🚀 Установка

1. 📥 Скачай `.zip`-архив из [репозитория](#)  
2. В Blender открой `Edit > Preferences > Add-ons > Install...`  
3. Выбери `developer_toolkit.zip`  
4. Активируй чекбокс **Developer Toolkit**  
5. В 3D Viewport открой **N-Panel > вкладка Dev**

---

## 📋 Как использовать

### 🔹 Добавление аддона
- Нажми кнопку **Add Addon**
- Укажи путь к папке, содержащей `__init__.py`
- Имя модуля определится автоматически (или введи вручную)
- Подтверди — аддон добавится в список

### 🔁 Перезагрузка
- Нажми кнопку **🔁 Reload**  
- Можно выбрать **"Reload without unregistering"**, чтобы избежать сбоев при ошибках

### 🧠 Массовая перезагрузка
- Отметь несколько аддонов галочками
- Нажми **Reload Selected**

---

## 🛠 Поддержка и обратная связь

Нашёл баг или хочешь предложить улучшение?  
📬 Открой [issue](https://github.com/твоя-ссылка/issues) или отправь pull request — сообщество будет признательно!

---

## 📜 Лицензия

**MIT License** — свободно используйте, модифицируйте, распространяйте с указанием автора.

---

💡 _Разработка аддонов ещё никогда не была такой быстрой и удобной._


