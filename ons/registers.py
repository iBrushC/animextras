import bpy
import rna_keymap_ui

def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
# def get_hotkey_entry_item(km, kmi_name):
    for i, km_item in enumerate(km.keymap_items):
        print(km.keymap_items.keys()[i] == kmi_name)
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
        # elif properties == 'none':
        #     return km_item
    return None
