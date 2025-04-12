https://www.buymeacoffee.com/gh0stck29u
🧩 Developer Toolkit for Blender
Developer Toolkit is a convenient utility for Blender addon developers, allowing you to:

🔹 Quickly add and track addons from local source folders
🔹 Reload addons with automatic .zip packaging
🔹 Manage addon paths, module names, and activation states
🔹 Reload multiple addons at once
🔹 Reload even if the addon has errors (skip unregister)
🔹 Eliminate the need for manual zipping and reinstalling during development

📦 Features
Feature	Description
➕ Add Addon	Enter module name and path to add an addon to the list
🔁 Reload Addon	Automatically creates a .zip, reinstalls and reactivates the addon
⚙️ Auto Save	Automatically saves your .blend file before reloading (optional)
🧼 Clear Console	Clears the Python console before reload (optional)
🧠 Batch Reloading	Reload all selected addons with one click
✏️ Edit Path & Name	Easily rename or relocate source directory
👁 UI Refresh	Forces UI refresh to reflect changes immediately
✅ Active Status Indicator	Shows if the addon is currently active
🧩 Compatibility	Supports Blender 3.x – 4.4 (and above)
🚀 Installation
Download the .zip archive from this repository, or install directly in Blender:

Edit > Preferences > Add-ons > Install...

Choose developer_toolkit.zip

Enable the checkbox next to Developer Toolkit

Open the N-Panel > Dev tab in the 3D Viewport

📋 How to Use
🔹 Adding an Addon
Click "Add Addon"

Select the folder containing __init__.py

The module name will be auto-detected (or enter it manually)

Confirm — the addon will be added to the list

🔹 Reloading
Click the 🔁 button or "Reload"

Optionally, use "Reload without unregistering" to avoid issues during errors

🔹 Batch Reloading
Check multiple addons in the list

Click Reload Selected

🛠 Support & Feedback
Found a bug or have an idea?
Please open an issue or submit a pull request — all contributions are welcome!

📜 License
MIT License — Free to use and modify with attribution.
