Tell me thanks.
<p><a href="https://www.buymeacoffee.com/gh0stck29u"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a></p>

# 🧩 Developer Toolkit for Blender

**Developer Toolkit** is a convenient utility for Blender addon developers that allows you to:

- 🔹 Quickly add and track addons from local source folders  
- 🔁 Reload addons with automatic `.zip` packaging and reinstallation  
- ⚙️ Manage addon paths, module names, and activation states  
- 🧠 Reload multiple addons at once  
- ❌ Reload even if the addon has errors (skip `unregister`)  
- 🧼 Eliminate the need for manual zipping and reinstalling during development

---
**Refactor: simplify addon import workflow** (28.11.2025)

- Removed redundant intermediate popup window  
- Added a single operator that directly opens the file browser  
- Addon is now registered immediately after selecting `__init__.py`

**Fix: Improved Language Detection and UI Localization

- The addon now correctly follows Blender's language settings: system locale is used only when the interface language is **Automatic** and translations are enabled.  
- If interface translations are disabled, the addon always stays in English for consistency.  
- Explicit language choices (**English** / **Russian**) fully override automatic detection.  
- All UI labels and operator messages now reliably switch between languages based on the active Blender settings.

---

## 📦 Features

| 🔧 Feature             | 📝 Description                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| ➕ **Add Addon**        | Enter the path and module name — the addon will be added to the list           |
| 🔁 **Reload Addon**     | Automatically creates a `.zip`, reinstalls and reactivates the addon           |
| ⚙️ **Auto Save**        | Optionally saves your `.blend` file before reloading                           |
| 🧼 **Clear Console**    | Clears the Python console before reload                                        |
| 🧠 **Batch Reloading**  | Reloads all selected addons with a single click                                |
| ✏️ **Edit Path & Name** | Easily rename or relocate the source directory                                 |
| 👁 **UI Refresh**       | Forces UI refresh to reflect changes immediately                               |
| ✅ **Active Status**    | Indicates whether the addon is currently active                                |

---

## 🧩 Compatibility

- ✅ Blender **4.4+**
- 🛠 Designed for local source-based addon development
- 💼 Works great with both single or multiple addon workflows

---

## 🚀 Installation

1. 📥 Download the `.zip` archive from the [repository](#)  
2. In Blender: `Edit > Preferences > Add-ons > Install...`  
3. Choose `developer_toolkit.zip`  
4. Enable the checkbox for **Developer Toolkit**  
5. In the 3D Viewport: open **N-Panel > Dev tab**

---

## 📋 How to Use

### 🔹 Adding an Addon
- Click **Add Addon**
- Select the folder containing `__init__.py`
- The module name will be auto-detected based on the folder name (or enter it manually)
- Confirm — the addon will be added to the list

### 🔁 Reloading
- Click the **🔁 Reload** button  
- You may use **"Reload without unregistering"** to avoid unregister errors

---

## 🛠 Support & Feedback

Found a bug or have a suggestion?  
📬 Feel free to open an [issue](https://github.com/Gh0StCK/Developer-Toolkit/issues) or submit a pull request — contributions are welcome!

---

## 📜 License

**MIT License** — Free to use, modify, and distribute with attribution.
