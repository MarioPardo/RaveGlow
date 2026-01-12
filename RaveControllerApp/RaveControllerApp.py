import server
import animation_handler
import socket
import json
import threading
import time
from pynput import keyboard


animation_keys = [] #list of keys that are mapped to animations
key_animation_mappings = {} #map keys : animation json



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
        print("5. Start BPM-based Automatic Rave Controller")
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
        elif user_input == "5":
            #threading.Thread(target=server.start_server, daemon=True).start()
            run_bpm_based_automatic()
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
                    print("Sending Payload:", repr(animation_data))
                    server.broadcast_message(animation_data)
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



def run_bpm_based_automatic():
    def prompt_bpm():
        while True:
            bpm_input = input("Enter target BPM: ").strip()
            try:
                bpm_value = float(bpm_input)
                if bpm_value <= 0:
                    raise ValueError
                return bpm_value
            except ValueError:
                print("Invalid BPM. Please enter a positive number.")

    def prompt_color(label):
        available_colors = animation_handler.colors_rgb
        color_names = list(available_colors.keys())
        print(f"\nSelect the {label} color:")
        for idx, name in enumerate(color_names, start=1):
            rgb = available_colors[name]
            print(f"  {idx}. {name} ({rgb[0]}, {rgb[1]}, {rgb[2]})")
        print("  C. Custom RGB value")

        while True:
            choice = input("Enter name, number, or 'C' for custom: ").strip().lower()
            if not choice:
                print("Please enter a choice.")
                continue

            if choice == 'c' or choice == 'custom':
                def prompt_rgb(channel):
                    while True:
                        value = input(f"Enter {channel} value (0-255): ").strip()
                        try:
                            value_int = int(value)
                            if 0 <= value_int <= 255:
                                return value_int
                        except ValueError:
                            pass
                        print("Invalid value. Please enter an integer between 0 and 255.")

                r = prompt_rgb("red")
                g = prompt_rgb("green")
                b = prompt_rgb("blue")
                color_label = f"custom({r},{g},{b})"
                return {"name": color_label, "rgb": (r, g, b)}

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(color_names):
                    name = color_names[idx - 1]
                    return {"name": name, "rgb": available_colors[name]}
                print("Number out of range. Try again.")
                continue

            if choice in available_colors:
                return {"name": choice, "rgb": available_colors[choice]}

            print("Invalid choice. Please try again.")

    def prompt_animations():
        available = animation_handler.available_animations
        print("\nAvailable animations:")
        for idx, name in enumerate(available, start=1):
            print(f"  {idx}. {name}")

        while True:
            raw = input("Enter animations to cycle (comma separated names or numbers): ").strip()
            if not raw:
                print("Please select at least one animation.")
                continue

            selections = [item.strip() for item in raw.split(',') if item.strip()]
            chosen = []
            valid = True
            for entry in selections:
                if entry.isdigit():
                    idx = int(entry)
                    if 1 <= idx <= len(available):
                        chosen.append(available[idx - 1])
                        continue
                    valid = False
                    break
                if entry in available:
                    chosen.append(entry)
                else:
                    valid = False
                    break

            if valid and chosen:
                return chosen

            print("Invalid selection. Try again using the provided names or numbers.")

    def prompt_phrase_interval():
        while True:
            response = input("Change animation every how many phrases? (0 to keep current animation): ").strip()
            if response == "":
                return 1
            try:
                value = int(response)
                if value < 0:
                    raise ValueError
                return value
            except ValueError:
                print("Please enter a non-negative integer.")

    bpm_value = prompt_bpm()
    beat_duration = 60.0 / bpm_value
    animation_bpm = int(round(bpm_value))

    first_color = prompt_color("first")
    second_color = prompt_color("second")
    colors = [first_color, second_color]

    selected_animations = prompt_animations()
    if not selected_animations:
        print("No animations selected. Exiting automatic controller.")
        return

    phrases_per_animation = prompt_phrase_interval()

    print("\nStarting BPM-based automatic controller.")
    print("Press SPACE to start or resync the beat. Press ESC to stop. Press Ctrl+C to exit.")

    threading.Thread(target=server.start_server, daemon=True).start()

    start_event = threading.Event()
    reset_event = threading.Event()
    stop_event = threading.Event()

    beats_per_bar = 4
    bars_per_phrase = 8
    beat_percentage = 1.5

    animation_index = 0
    phrases_for_current_animation = 0
    total_phrases = 0
    total_beats = 0
    beat_in_bar = 0
    bar_in_phrase = 1
    color_index = -1

    def beat_loop():
        nonlocal animation_index, phrases_for_current_animation
        nonlocal total_phrases, total_beats, beat_in_bar, bar_in_phrase, color_index

        next_beat_time = None
        started = False

        while not stop_event.is_set():
            start_event.wait()
            if stop_event.is_set():
                break

            if reset_event.is_set() or not started:
                reset_event.clear()
                started = True
                next_beat_time = time.time()
                beat_in_bar = 0
                bar_in_phrase = 1
                color_index = -1

            if next_beat_time is None:
                next_beat_time = time.time()

            sleep_time = next_beat_time - time.time()
            if sleep_time > 0:
                time.sleep(min(sleep_time, 0.05))
                continue

            beat_in_bar += 1
            if beat_in_bar > beats_per_bar:
                beat_in_bar = 1
                bar_in_phrase += 1
                if bar_in_phrase > bars_per_phrase:
                    bar_in_phrase = 1
                    total_phrases += 1
                    if phrases_per_animation > 0:
                        phrases_for_current_animation += 1
                        if phrases_for_current_animation >= phrases_per_animation:
                            phrases_for_current_animation = 0
                            animation_index = (animation_index + 1) % len(selected_animations)

            color_index = (color_index + 1) % len(colors)
            total_beats += 1

            current_animation = selected_animations[animation_index]
            color = colors[color_index]

            schema = animation_handler.create_temp_anim_from_default(
                current_animation,
                f"Auto_{current_animation}_{total_beats}",
                color["rgb"][0],
                color["rgb"][1],
                color["rgb"][2],
                animation_bpm,
                beat_percentage
            )

            if schema is None:
                print(f"Unable to create default animation for '{current_animation}'. Stopping controller.")
                stop_event.set()
                start_event.set()
                break

            try:
                server.broadcast_message(schema)
            except Exception as exc:
                print(f"Failed to broadcast animation '{current_animation}': {exc}")

            print(f"[{bar_in_phrase}][{beat_in_bar}] : {current_animation} ({color['name']})")

            next_beat_time += beat_duration

        print("Automatic BPM controller loop stopped.")

    beat_thread = threading.Thread(target=beat_loop, daemon=True)
    beat_thread.start()

    def on_press(key):
        if key == keyboard.Key.space:
            if not start_event.is_set():
                print("Beat tracking started.")
            else:
                print("Resyncing beat to spacebar press.")
            reset_event.set()
            start_event.set()
        elif key == keyboard.Key.esc:
            print("ESC pressed. Stopping automatic controller.")
            stop_event.set()
            start_event.set()
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        while listener.is_alive() and not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping automatic controller.")
        stop_event.set()
        start_event.set()
    finally:
        listener.stop()
        listener.join()
        stop_event.set()
        start_event.set()
        beat_thread.join()

    return




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

