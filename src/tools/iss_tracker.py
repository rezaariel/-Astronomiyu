import customtkinter as ctk
import requests
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

def open_iss_tracker(parent: ctk.CTk) -> None:
    win = ctk.CTkToplevel(parent)
    win.title("ISS Real-Time Tracker")
    win.geometry("400x450")
    win.attributes('-topmost', True)

    ctk.CTkLabel(win, text="ISS Rapid Telemetry", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
    
    lat, lon = get_auto_location()
    
    from astropy.coordinates import EarthLocation
    import astropy.units as u
    user_loc = EarthLocation.from_geodetic(lon*u.deg, lat*u.deg)
    
    ctk.CTkLabel(win, text=f"📍 Your Init: Lat {lat:.4f}, Lon {lon:.4f}", text_color="gray").pack()
    
    res_var = ctk.StringVar(value="Fetching Low Earth Orbit APIs...")
    ctk.CTkLabel(win, textvariable=res_var, font=ctk.CTkFont(size=16), justify="left").pack(pady=30)
    
    def fetch_iss():
        try:
            res = requests.get("http://api.open-notify.org/iss-now.json", timeout=5).json()
            iss_lat = float(res['iss_position']['latitude'])
            iss_lon = float(res['iss_position']['longitude'])
            
            iss_loc = EarthLocation.from_geodetic(iss_lon*u.deg, iss_lat*u.deg, height=400*u.km)
            
            # 3D Cartesian Euclidean Distance in km
            dx = user_loc.x - iss_loc.x
            dy = user_loc.y - iss_loc.y
            dz = user_loc.z - iss_loc.z
            dist_km = (dx**2 + dy**2 + dz**2)**0.5 / 1000.0
            
            # Simple geometric horizon approximation 
            above = "YES 🟢" if dist_km.value < 2200 else "NO 🔴"
            
            res_var.set(
                f"🛰️ ISS Latitude:  {iss_lat:.4f}°\n"
                f"🛰️ ISS Longitude: {iss_lon:.4f}°\n\n"
                f"📏 Relative Dist: {dist_km.value:.1f} km\n"
                f"🔭 Above Horizon:  {above}"
            )
        except Exception as e:
            res_var.set(f"API Error: {e}")
            
    fetch_iss()
    ctk.CTkButton(win, text="Refresh Telemetry", command=fetch_iss, height=40).pack(pady=10)
