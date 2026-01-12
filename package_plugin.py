
import os
import zipfile
import shutil

BASE_DIR = os.getcwd()
PLUGIN_SRC = os.path.join(BASE_DIR, 'wordpress-plugin', 'postpro')
MEDIA_PLUGINS_DIR = os.path.join(BASE_DIR, 'media', 'plugins')
ZIP_PATH = os.path.join(MEDIA_PLUGINS_DIR, 'postpro-plugin.zip')

def package_plugin():
    if not os.path.exists(PLUGIN_SRC):
        print(f"Error: Plugin source not found at {PLUGIN_SRC}")
        return

    # Create destination directory
    os.makedirs(MEDIA_PLUGINS_DIR, exist_ok=True)

    print(f"Packaging plugin from {PLUGIN_SRC} to {ZIP_PATH}...")
    
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory
        for root, dirs, files in os.walk(PLUGIN_SRC):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate archive name (relative path inside zip)
                # We want the zip to contain a root folder 'postpro/'
                rel_path = os.path.relpath(file_path, os.path.dirname(PLUGIN_SRC))
                zipf.write(file_path, rel_path)
    
    print("Success! Plugin zip created.")
    print(f"Size: {os.path.getsize(ZIP_PATH)} bytes")

if __name__ == "__main__":
    package_plugin()
