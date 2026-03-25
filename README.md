# Astronomiyu 🌌

**Astronomiyu** is a modern, modular desktop application serving as a central hub for celestial mechanics and astrodynamics. Built in Python with a sleek, dark-themed `customtkinter` interface, it brings complex astronomical computations elegantly to your desktop!

## ✨ Features

* **Gauss's Orbit Determination**: Calculate the six classical Keplerian orbital elements (Semi-major Axis, Eccentricity, Inclination, RAAN, Argument of Periapsis, Mean Anomaly) from just three optical RA/Dec observations and generate stunning, mathematically robust 3D orbit visualizations using `matplotlib`.
* **Real-Time Celestial Tracker**: Automatically detects your geographical location using IP data and tracks the real-time Altitude, Azimuth, Right Ascension, and Declination of major solar system bodies using precision `astropy` ephemerides.
* **⚡ Ultra-Lightweight Lazy Loading**: Re-engineered core architecture. Giant scientific libraries (`astropy`, `matplotlib`) are completely removed from the global scope and are lazy-loaded dynamically in memory ONLY when actively computing. This reduces the application's idle memory footprint by up to 80% and ensures instant GUI startup times!
* **📦 Production Ready**: Fully typed (`typing`), logically isolated into `src/` and `data/` modules, and cleanly executable natively or bundled.

## 🚀 How to Install and Run

### For End Users (Standalone App - No Python Required!)
You can run Astronomiyu instantly on your Windows machine without touching any code!
1. Head over to the **[Releases](../../releases)** section on the right side of this GitHub repository.
2. Download the latest `Astronomiyu.exe` file.
3. Make sure to place your `observations.txt` file in the same directory if you intend to use the Gauss Orbit Determination feature.
4. Simply double-click `Astronomiyu.exe` to launch the application.

*(Note: Windows SmartScreen might initially flag the file since it's a new, unsigned application. Click "More Info" -> "Run anyway".)*

### For Developers 
To run Astronomiyu from source:
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/astronomiyu.git
   cd astronomiyu
   ```
2. Install the required core dependencies:
   ```bash
   pip install customtkinter astropy matplotlib numpy requests
   ```
3. Boot up the main GUI hub:
   ```bash
   python astronomiyu.py
   ```
