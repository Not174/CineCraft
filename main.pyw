import os
import webview
from app import CineCraftAPI

def main():
    api = CineCraftAPI()
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(current_dir, 'ui', 'index.html')
    icon_path = os.path.join(current_dir, 'staff.ico')

    # Create the window
    window = webview.create_window(
        'CineCraft - Modern Video Toolkit',
        url=ui_path,
        js_api=api,
        width=850,
        height=720,
        min_size=(800, 650),
        background_color='#000000'
    )
    
    # Give the API access to the window object (for dialogs and JS evaluation)
    api.set_window(window)
    
    # Start the app
    webview.start()

if __name__ == '__main__':
    main()
