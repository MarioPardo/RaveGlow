'''
This file contains functions that prompt user input for animation parameters. 
Functionss that create individual animations output the JSON which is sent to ESP32 

'''
import json
from pathlib import Path


###JSON functions
#################

FILE_PATH = Path("animation_mappings.json")

def load_json():
    """Load JSON file into dict, create file if it doesn't exist."""
    if not FILE_PATH.exists():
        with open(FILE_PATH, "w") as f:
            json.dump({}, f, indent=4)
    with open(FILE_PATH, "r") as f:
        return json.load(f)

def save_json(data):
    """Save dict back to JSON file."""
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_schemas_by_key(key: str):
    """Print schemas for given key, or say not found."""
    data = load_json()
    if key not in data or not data[key]:
        print(f"No schemas found for key '{key}'")
        return None
    print(json.dumps(data[key], indent=4))
    return data[key]

def get_all_schemas():
    """Return dict of all keys and their schema lists."""
    return load_json()

def append_schema(key: str, schema: dict):
    """
    Replace schema for given key.
    Creates key if it doesn't exist.
    """
    data = load_json()
    data[key] = [schema]
    save_json(data)
    print(f"Schema set for key '{key}'.")


def parse_json_entries():
    """
    Read the JSON and return a dict where each key is a single char (key),
    and the value is a string containing all the JSON schemas for that key.
    """
    data = load_json()
    entries = {}
    for key, schemas in data.items():
        # Combine all schemas for this key into a single pretty-printed string
        json_str = "\n".join(json.dumps(schema, indent=4) for schema in schemas)
        entries[key] = json_str
    return entries






######

def create_new_animation():

    print("Select animation type:")
    print("1. Blink")
    print("2. FuseWave")
    choice = input("Enter choice (1 or 2): ")

    if choice == "1":
        schema = create_blink()
    elif choice == "2":
        schema = create_fuseWave()
    else:
        print("Invalid choice.")
        return


    return schema


def prompt_default():
    '''
    Prompt user for default animation parameters
    - R, G, B : Color which strip will light up
    - BPM : at what BPM we are blinking
    - beatPercentage : what percentage of the beat we are on
    '''
    
    # Prompt user for input
    name = input("Enter animation name: ")
    r = int(input("Enter red color value (0-255): "))
    g = int(input("Enter green color value (0-255): "))
    b = int(input("Enter blue color value (0-255): "))
    bpm = int(input("Enter BPM (Beats Per Minute): "))
    beat_percentage = float(input("Enter beat percentage (0-100): "))

    return name, r, g, b, bpm, beat_percentage


### Individual Animations #####
###############################

def create_blink():
    '''
    Blink
    Parameters 
        - Default Parameters ( RGB, BPM, beatPercentage)
    '''

    name, r, g, b, bpm, beat_percentage = prompt_default()    

    animation_JSON = {
        "name": name,
        "Animation" : "Blink",
        "r" : r,
        "g" : g,
        "b" : b,
        "BPM" : bpm,
        "beatPercentage" : beat_percentage
    }

    return animation_JSON



def create_fuseWave():
    '''
    FuseWave
    Parameters 
        - Default Parameters ( RGB, BPM, beatPercentage)
        - Chunk Size: How many LEDs to light up at once
    '''
    name, r, g, b, bpm, beat_percentage = prompt_default()
    chunk_size = int(input("Enter chunk size: "))

    animation_JSON = {
        "name" : name,
        "Animation" : "FuseWave",
        "r" : r,
        "g" : g,
        "b" : b,
        "BPM" : bpm,
        "beatPercentage" : beat_percentage,
        "chunkSize" : chunk_size
    }

    return animation_JSON