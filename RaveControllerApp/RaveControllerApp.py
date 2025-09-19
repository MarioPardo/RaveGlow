


import server
import animation_handler
import socket
import json
from pynput import keyboard
import threading


animation_keys = [] #list of keys that are mapped to animations
key_animation_mappings = {} #map keys : animation json

colors_rgb = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "light_blue": (173, 216, 230),
    "light_green": (144, 238, 144)
}



def load_key_mappings():
    """Load key to animation mappings from JSON file."""
    global key_animation_mappings
    key_animation_mappings = animation_handler.parse_json_entries()

    return




###### MAIN MENU###########
###########################
def display_current_mappings():
    """Display current key to animation mappings."""

    for key,value in key_animation_mappings.items():
        print("\n")
        print(f"Key: {key}")
        try:
            animation_data = json.loads(value)
            for entry_key, entry_value in animation_data.items():
                print(f"\t{entry_key}: {entry_value}")
        except Exception as e:
            print(f"\tError parsing animation JSON: {e}")

    
    return
    



def create_new_mapping():

    key = input("Enter key to bind animation to: ")

    if key in key_animation_mappings:
        overwrite = input(f"Key '{key}' is already mapped. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Aborting mapping creation.")
            return

    schema = animation_handler.create_new_animation()

    if schema is None:
        print("No animation created. Aborting mapping.")
        return

    key_animation_mappings[key] = schema
    animation_handler.append_schema(key,schema)



#Display Menu#
''' Display Command Line Menu
    - display key mappings
    - create new key mapping
    - start server
'''
def display_menu():
    print("Command Line Menu:")
    print("1. Display Key Mappings")
    print("2. Create New Key Mapping")
    print("3. Start Rave Controller")
    print("9. Exit")


    while True:

        print()
        print("1. Display Key Mappings")
        print("2. Create New Key Mapping")
        print("3. Manually Set up Server Info")
        print("4. Start Manual Rave Controller")
        print("9. Exit")

        user_input = input("Please Enter your Choice ")

        if user_input == "1":
            display_current_mappings()
        elif user_input == "2":
            create_new_mapping()
        elif user_input == "3":
            server.manually_setup_server()
        elif user_input == "4":
            threading.Thread(target=server.start_server, daemon=True).start()
            run_manual_controller()
        elif user_input == "9":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

#######################################


##### CONTROLLER #################
##################################

def run_manual_controller():
    print("Controller running. Press mapped keys to trigger animations. Press ESC to exit.")

    def on_press(key):
        try:
            # Convert key to string name if possible
            key_name = key.char if hasattr(key, 'char') else str(key).split('.')[-1]

            if key_name == 'esc':
                print("Exiting controller...")
                return False  # stops the listener

            if key_name in key_animation_mappings:
                try:
                    animation_data = json.loads(key_animation_mappings[key_name])
                    animation_name = animation_data.get("name", "Unknown")
                    print(f"Triggered animation: {animation_name}")
                    server.broadcast_message(key_animation_mappings[key_name])
                except Exception as e:
                    print(f"Error handling animation for key '{key_name}': {e}")

        except AttributeError:
            # Special keys without 'char' attribute are ignored here
            pass

    def on_release(key):
        # Optional: handle key release if needed
        pass

    # Start listener (blocking)
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()




####MAIN ########################
################################

if __name__ == "__main__":

    # Welcome Menu
    print("Welcome to the Rave Controller App!")

    #Set things up
    load_key_mappings()


    #Display Menu
    display_menu()


    #ctrl -c to exit 

