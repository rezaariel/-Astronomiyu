import customtkinter as ctk
import requests
import numpy as np
from typing import Tuple

def get_auto_location(parent_window: ctk.CTkToplevel) -> Tuple[float, float]:
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5).json()
        if res.get("loc"):
            lat, lon = res["loc"].split(',')
            return float(lat), float(lon)
    except:
        pass
    return -6.2000, 106.8166

def get_events(lat: float, lon: float) -> dict:
    from astropy.time import Time
    from astropy.coordinates import EarthLocation, get_sun, get_body, AltAz, solar_system_ephemeris
    import astropy.units as u

    loc = EarthLocation.from_geodetic(lon*u.deg, lat*u.deg)
    
    # 24 hour grid to find horizon zero-crossings
    now = Time.now()
    midnight = Time(f"{now.isot.split('T')[0]}T00:00:00")
    times = midnight + np.linspace(0, 24, 100) * u.hour
    
    altaz_frame = AltAz(obstime=times, location=loc)
    sun_alts = get_sun(times).transform_to(altaz_frame).alt.degree
    with solar_system_ephemeris.set('builtin'):
        moon_alts = get_body('moon', times, loc).transform_to(altaz_frame).alt.degree
    
    def find_crossing(alts):
        rises, sets = [], []
        for i in range(len(alts)-1):
            if alts[i] < 0 and alts[i+1] >= 0: rises.append(times[i])
            elif alts[i] > 0 and alts[i+1] <= 0: sets.append(times[i])
        return rises, sets

    sun_rises, sun_sets = find_crossing(sun_alts)
    moon_rises, moon_sets = find_crossing(moon_alts)
    
    # Precise Moon Illumination via Solar Elongation
    with solar_system_ephemeris.set('builtin'):
        moon_now = get_body('moon', now, loc)
    elongation = get_sun(now).separation(moon_now).degree
    illumination = 50 * (1 - np.cos(np.radians(elongation)))
    
    return {
        "sunrise": sun_rises[0].isot[11:16] if sun_rises else "N/A",
        "sunset": sun_sets[0].isot[11:16] if sun_sets else "N/A",
        "moonrise": moon_rises[0].isot[11:16] if moon_rises else "N/A",
        "moonset": moon_sets[0].isot[11:16] if moon_sets else "N/A",
        "illumination": illumination
    }

def open_obs_planner(parent: ctk.CTk) -> None:
    win = ctk.CTkToplevel(parent)
    win.title("Observation Planner")
    win.geometry("450x450")
    win.attributes('-topmost', True)

    ctk.CTkLabel(win, text="Daily Observation Planner", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
    
    lat, lon = get_auto_location(win)
    ctk.CTkLabel(win, text=f"📍 Location: Lat {lat:.4f}, Lon {lon:.4f}").pack()
    
    res_var = ctk.StringVar(value="Calculating today's ephemerides...\n(This requires compiling heavy astropy mechanics)")
    ctk.CTkLabel(win, textvariable=res_var, font=ctk.CTkFont(size=16), justify="left").pack(pady=40)
    
    def calc():
        try:
            ev = get_events(lat, lon)
            res_var.set(
                f"🌅 Sunrise: {ev['sunrise']} UTC\n"
                f"🌇 Sunset:  {ev['sunset']} UTC\n\n"
                f"🌒 Moonrise: {ev['moonrise']} UTC\n"
                f"🌘 Moonset:  {ev['moonset']} UTC\n\n"
                f"🌖 Moon Illumination: {ev['illumination']:.1f}%"
            )
        except Exception as e:
            res_var.set(f"Calculation Error: {e}")
            
    win.after(100, calc)  # Allow UI to open before freezing for math
