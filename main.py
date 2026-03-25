import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys

# Clean absolute package imports routing into src architecture
from src.tools.gauss_orbit import run_gauss, get_resource_path
from src.tools.realtime_coords import open_coordinate_tracker

class AstronomiyuApp(ctk.CTk):
    """
    Main application GUI for Astronomiyu.
    Serves as the central hub connecting all celestial mechanics and astrodynamics sub-programs.
    """
    def __init__(self) -> None:
        super().__init__()

        # Setup Window
        self.title("Astronomiyu")
        self.geometry("500x450")
        
        # Configure Custom Window Icon
        try:
            icon_path = get_resource_path(os.path.join("data", "icon.ico"))
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not load application icon ({e})")
        
        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self, 
            text="Welcome to Astronomiyu", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(40, 0))

        # Subtitle Label
        self.subtitle_label = ctk.CTkLabel(
            self, 
            text="Your Central Hub for Celestial Mechanics", 
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(5, 30))

        # Gauss Button
        self.gauss_button = ctk.CTkButton(
            self, 
            text="Gauss Orbit Determination", 
            command=self.launch_gauss,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        self.gauss_button.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Coordinate Tracker Button
        self.coords_button = ctk.CTkButton(
            self, 
            text="Real-Time Celestial Tracker", 
            command=self.launch_tracker,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        self.coords_button.grid(row=3, column=0, padx=20, pady=(0, 40))

    def launch_tracker(self) -> None:
        """Launches the Real-Time Celestial Coordinate Tracker sub-program."""
        open_coordinate_tracker(self)

    def launch_gauss(self) -> None:
        """Opens a file dialog and launches the Gauss Orbit Determination module."""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Observations File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if file_path:
            try:
                # Run the Gauss Orbit script with the selected file path
                run_gauss(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to run Gauss Determination:\n{e}")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    app = AstronomiyuApp()
    app.mainloop()
