


import server
import animation_handler
import socket


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
    key_animation_mappings = animation_handler.parse_json_entries()

    return




###### MAIN MENU###########
###########################
def display_current_mappings():

    pass



def create_new_mapping():

    key = input("Enter key to bind animation to: ")

    #TODO check if this key is already bound to

    schema = animation_handler.create_new_animation()

    #TODO check if schema is valid

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
    print("3. Start Server")
    print("4. Exit")


    while True:
        user_input = input("Please Enter your Choice ")

        if user_input == "1":
            display_current_mappings()
        elif user_input == "2":
            create_new_mapping()
        elif user_input == "3":
            server.start_server()
        elif user_input == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

#######################################


##### CONTROLLER #################
##################################

def run_controller():

    #Continuously read keyboard

    #If key input has binding

        #print animation name
        #send json to server to send



    pass




####MAIN ########################
################################

if __name__ == "__main__":

    # Welcome Menu
    print("Welcome to the Rave Controller App!")

    # Display current IP address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Current IP address: {ip_address}")

    # Prompt for which port to use, default to 5000
    port_input = input("Enter port to use (default 5000): ")
    try:
        port = int(port_input) if port_input.strip() else 5000
    except ValueError:
        print("Invalid port. Using default 5000.")
        port = 5000
    print(f"Using port: {port}")


    #Set things up
    load_key_mappings()



    #Display Menu
    display_menu()


    #ctrl -c to exit 

