import customtkinter as ctk
import requests
import numpy as np
from typing import Tuple

def get_auto_location() -> Tuple[float, float]:
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5).json()
        if res.get("loc"):
            lat, lon = res["loc"].split(',')
            return float(lat), float(lon)
    except:
        pass
    return -6.2000, 106.8166

def open_skymap(parent: ctk.CTk) -> None:
    win = ctk.CTkToplevel(parent)
    win.title("Interactive Local Sky Map")
    win.geometry("650x750")
    win.attributes('-topmost', True)
    
    ctk.CTkLabel(win, text="🌟 Live Local Sky Map", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
    
    lat, lon = get_auto_location()
    ctk.CTkLabel(win, text=f"📍 Location Detection: Lat {lat:.4f}, Lon {lon:.4f}").pack()
    
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    # Intialize Figure
    fig = plt.figure(figsize=(6, 6), facecolor='#0A0A1A')
    ax = fig.add_subplot(111, polar=True, facecolor='#0A0A1A')
    
    # Configure Polar Math (Center is Zenith (Alt=90), Edge is Horizon (Alt=0))
    ax.set_theta_zero_location('N') # North is top
    ax.set_theta_direction(-1) # Clockwise mapping
    ax.set_ylim(0, 90) # Radius corresponds to (90 - Altitude)
    ax.set_rgrids([30, 60, 90], labels=['60°', '30°', '0° (Horizon)'], angle=45, color='gray')
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], 
                      labels=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                      color='white')
    ax.tick_params(axis='y', colors='gray', pad=10)
    ax.tick_params(axis='x', colors='white')
    ax.spines['polar'].set_color('#1c1c3c')
    
    # Embed into Tkinter GUI
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    # Info status
    info_label = ctk.CTkLabel(win, text="Initializing SkyMap engine...")
    info_label.pack(pady=(5, 5))

    def draw_sky():
        ax.clear()
        
        # Re-apply polar constraints after clearing
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_rgrids([30, 60, 90], labels=['60°', '30°', '0° (Horizon)'], angle=22.5, color='gray')
        ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], 
                          labels=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], color='white')
        ax.tick_params(axis='y', colors='gray')
        ax.tick_params(axis='x', colors='white')
        
        info_label.configure(text="Calculating Astropy coordinates...")
        win.update()

        try:
            from astropy.time import Time
            from astropy.coordinates import EarthLocation, get_body, AltAz, solar_system_ephemeris
            import astropy.units as u

            user_loc = EarthLocation.from_geodetic(lon*u.deg, lat*u.deg)
            now = Time.now()
            altaz_frame = AltAz(obstime=now, location=user_loc)
            
            targets = {
                'sun': ('#FFFF00', 'Sun'),
                'moon': ('#FFFFFF', 'Moon'),
                'mercury': ('#B5B5B5', 'Mercury'),
                'venus': ('#EEBB88', 'Venus'),
                'mars': ('#FF4400', 'Mars'),
                'jupiter': ('#CCAA66', 'Jupiter'),
                'saturn': ('#EAD6B8', 'Saturn')
            }
            
            visible_count = 0
            with solar_system_ephemeris.set('builtin'):
                for body_id, (color, name) in targets.items():
                    # Calculate vector
                    body_pos = get_body(body_id, now, user_loc)
                    altaz = body_pos.transform_to(altaz_frame)
                    
                    alt = altaz.alt.degree
                    az = altaz.az.degree
                    
                    if alt > 0:
                        # Mathematical Mapping -> Center=90, Edge=0
                        r = 90 - alt
                        theta = np.radians(az)
                        
                        # Plot marker
                        ax.plot(theta, r, marker='o', color=color, markersize=10, markeredgecolor='white', label=name)
                        # Plot text slightly below the marker
                        ax.text(theta, r + 5, name, color='white', ha='center', va='top', fontsize=10)
                        visible_count += 1
            
            canvas.draw()
            info_label.configure(text=f"Live Sky Map Computed! ({visible_count} targets above your horizon)")
        except Exception as e:
            info_label.configure(text=f"Astrophysics Error: {e}")

    ctk.CTkButton(win, text="Refresh Sky Map", command=draw_sky, height=40).pack(pady=10)
    
    # Auto-initialize Sky Map
    win.after(100, draw_sky)
