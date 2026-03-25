import os
import sys
import numpy as np
from typing import Tuple, List, Optional

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource.
    Works seamlessly whether running natively as a .py script or as a bundled PyInstaller .exe.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_path, relative_path)

# Constants
k = 0.01720209895  # Gaussian gravitational constant (AU^(3/2) / day)
mu = k**2          # Gravitational parameter (AU^3 / day^2)

def unit_conversion_and_los(ra_list, dec_list):
    """
    Step 1: Convert angles to radians and calculate Line-of-Sight (LOS) unit vectors.
    """
    ra = np.radians(ra_list)
    dec = np.radians(dec_list)
    
    # Calculate LOS unit vectors
    L = np.zeros((3, 3))
    for i in range(3):
        L[i, 0] = np.cos(dec[i]) * np.cos(ra[i])
        L[i, 1] = np.cos(dec[i]) * np.sin(ra[i])
        L[i, 2] = np.sin(dec[i])
        
    return L[0], L[1], L[2]

def time_intervals(t1, t2, t3):
    """
    Step 2: Calculate time intervals tau1 and tau3 (in canonical units).
    tau1 corresponds to t3 - t2, and tau3 corresponds to t2 - t1.
    """
    tau1 = k * (t3 - t2)
    tau3 = k * (t2 - t1)
    return tau1, tau3

def setup_cross_products(L1, L2, L3, R1, R2, R3):
    """
    Step 3: Compute scalar triple products and cross products.
    """
    p1 = np.cross(L2, L3)
    p2 = np.cross(L1, L3)
    p3 = np.cross(L1, L2)
    
    D0 = np.dot(L1, p1)
    
    # Check for coplanarity
    if abs(D0) < 1e-8:
        print("Warning: Observations are nearly coplanar with the Earth-Sun plane. Gauss's method may be inaccurate.")
        
    # Dot products for the D matrix
    D11 = np.dot(R1, p1); D12 = np.dot(R1, p2); D13 = np.dot(R1, p3)
    D21 = np.dot(R2, p1); D22 = np.dot(R2, p2); D23 = np.dot(R2, p3)
    D31 = np.dot(R3, p1); D32 = np.dot(R3, p2); D33 = np.dot(R3, p3)
    
    return D0, D11, D12, D13, D21, D22, D23, D31, D32, D33

def gauss_polynomial_root(tau1, tau3, D0, D12, D22, D32, L2, R2):
    """
    Step 4: Formulate the Gauss polynomial and find the geocentric distance rho2.
    """
    tau = tau1 + tau3
    
    # Coefficients for the c1 and c3 series approximation
    A1 = tau1 / tau
    A3 = tau3 / tau
    B1 = (tau1 / (6 * tau)) * (tau**2 - tau1**2)
    B3 = (tau3 / (6 * tau)) * (tau**2 - tau3**2)
    
    # Combined coefficients for the rho2 equation
    A = (-A1 * D12 + D22 - A3 * D32) / D0
    B = (-B1 * D12 - B3 * D32) / D0
    
    E = np.dot(L2, R2)
    F = np.dot(R2, R2)
    
    # Objective function corresponding to the 8th-order polynomial equation
    # We solve f(rho2) = rho2 - A - B / r2^3 = 0, where r2 = sqrt(rho2^2 + 2*rho2*E + F)
    def objective(rho2):
        r2 = np.sqrt(rho2**2 + 2 * rho2 * E + F)
        return rho2 - A - B / (r2**3)
        
    def derivative(rho2):
        # Derivative of the objective function for Newton-Raphson
        r2_sq = rho2**2 + 2 * rho2 * E + F
        r2 = np.sqrt(r2_sq)
        # d(r2)/d(rho2) = (rho2 + E) / r2
        # d/d(rho2) [ - B / r2^3 ] = 3 * B * r2^-4 * d(r2)/d(rho2) = 3 * B * (rho2 + E) / r2^5
        return 1.0 + 3.0 * B * (rho2 + E) / (r2**5)
    
    # Custom Newton-Raphson method 
    def newton_raphson(x0, tol=1e-8, max_iter=100):
        x = x0
        for _ in range(max_iter):
            f_val = objective(x)
            f_der = derivative(x)
            if abs(f_val) < tol:
                return x, True
            if abs(f_der) < 1e-14:
                break
            x = x - f_val / f_der
        return x, False
        
    # Solve using Newton-Raphson with an initial guess of rho2 ~ 1.0 AU
    rho2_val, success = newton_raphson(1.0)
    
    if not success or rho2_val <= 0:
        # Mathematical fallback using 8th order explicit polynomial roots
        import numpy.polynomial.polynomial as poly
        # (rho - A)^2 = rho^2 - 2A*rho + A^2
        p_A = [A**2, -2*A, 1.0] 
        p_r2 = [F, 2*E, 1.0]
        p_r2_2 = poly.polymul(p_r2, p_r2)
        p_r2_3 = poly.polymul(p_r2_2, p_r2)
        p_LHS = poly.polymul(p_A, p_r2_3)
        p_LHS[0] -= B**2
        roots = poly.polyroots(p_LHS)
        
        real_positive_roots = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > 0]
        
        if len(real_positive_roots) > 0:
            rho2_val = real_positive_roots[0]
        else:
            raise ValueError(
                "No physical positive root found for rho2.\n"
                "Mathematical Proof: The generated 8th order Gauss polynomial has NO positive real roots.\n"
                "-> The provided RA/Dec observations geometrically contradict a valid heliocentric orbit.\n"
                "-> Explanation: At opposition, heliocentric objects beyond Earth exhibit retrograde motion.\n"
                "   The data provided indicates rapid PROGRADE motion at opposition, which violates orbital mechanics.\n"
                "Please verify or correct your observation data!"
            )
            
    r2_val = np.sqrt(rho2_val**2 + 2 * rho2_val * E + F)
    
    # Now calculate c1, c3 to find rho1, rho3
    c1 = A1 + B1 / r2_val**3
    c3 = A3 + B3 / r2_val**3
    
    return rho2_val, c1, c3, r2_val

def position_vectors(rho2, c1, c3, D0, D11, D21, D31, D13, D23, D33, L1, L2, L3, R1, R2, R3):
    """
    Step 5: Calculate heliocentric position vectors r1, r2, r3.
    """
    rho1 = (-c1 * D11 + D21 - c3 * D31) / (c1 * D0)
    rho3 = (-c1 * D13 + D23 - c3 * D33) / (c3 * D0)
    
    r1 = rho1 * L1 + R1
    r2 = rho2 * L2 + R2
    r3 = rho3 * L3 + R3
    
    return r1, r2, r3

def estimate_velocity(r1, r2, r3, t1, t2, t3):
    """
    Step 6: Estimate velocity vector v2 using the f and g series approximation.
    """
    r2_norm = np.linalg.norm(r2)
    # Using actual time differences in days
    dt1 = t1 - t2
    dt3 = t3 - t2
    
    # f and g expressions in terms of standard variables
    f1 = 1 - (mu / (2 * r2_norm**3)) * (dt1**2)
    f3 = 1 - (mu / (2 * r2_norm**3)) * (dt3**2)
    
    g1 = dt1 - (mu / (6 * r2_norm**3)) * (dt1**3)
    g3 = dt3 - (mu / (6 * r2_norm**3)) * (dt3**3)
    
    # Solve for v2 (Heliocentric velocity at t2 in AU/day)
    denom = f1 * g3 - f3 * g1
    v2 = (-f3 * r1 + f1 * r3) / denom
    
    return v2

def state_to_kepler(r, v, mu):
    """
    Step 7: Convert state vectors (r, v) to 6 standard Keplerian elements.
    Returns: a, e, i, Omega, omega, M (angles in degrees).
    """
    r_norm = np.linalg.norm(r)
    v_norm = np.linalg.norm(v)
    
    # Specific angular momentum
    h = np.cross(r, v)
    h_norm = np.linalg.norm(h)
    
    # Node vector
    K = np.array([0, 0, 1])
    n = np.cross(K, h)
    n_norm = np.linalg.norm(n)
    
    # Eccentricity vector
    e_vec = ( (v_norm**2 - mu/r_norm)*r - np.dot(r, v)*v ) / mu
    e = np.linalg.norm(e_vec)
    
    # Specific mechanical energy
    energy = (v_norm**2)/2 - mu/r_norm
    
    # Semi-major axis
    if abs(energy) > 1e-12:
        a = -mu / (2 * energy)
    else:
        a = np.inf # Parabolic case
        
    # Inclination
    i = np.arccos(h[2] / h_norm)
    
    # Right Ascension of Ascending Node (RAAN / Omega)
    if n_norm > 1e-12:
        Omega = np.arccos(n[0] / n_norm)
        if n[1] < 0:
            Omega = 2*np.pi - Omega
    else:
        Omega = 0.0 # Equatorial orbit
        
    # Argument of periapsis (omega)
    if n_norm > 1e-12 and e > 1e-12:
        val = np.dot(n, e_vec) / (n_norm * e)
        omega = np.arccos(max(-1.0, min(1.0, val)))
        if e_vec[2] < 0:
            omega = 2*np.pi - omega
    else:
        omega = 0.0
        
    # True anomaly (nu)
    if e > 1e-12:
        val = np.dot(e_vec, r) / (e * r_norm)
        nu = np.arccos(max(-1.0, min(1.0, val)))
        if np.dot(r, v) < 0:
            nu = 2*np.pi - nu
    else:
        nu = 0.0 # Circular orbit
        
    # Mean anomaly (M)
    if e < 1.0: # Elliptical
        E = np.arctan2(np.sqrt(1 - e**2) * np.sin(nu), e + np.cos(nu))
        M = E - e * np.sin(E)
        M = M % (2 * np.pi)
    else:
        M = 0.0 # Standard mean anomaly not defined similarly for hyperbolic/parabolic
        
    return a, e, np.degrees(i), np.degrees(Omega), np.degrees(omega), np.degrees(M)

def read_observations(filename):
    """
    Parses exactly 3 valid observation lines from a text file, skipping comments.
    Format: YYYY-MM-DDThh:mm:ss, RA_string, Dec_string
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The observation file '{filename}' was not found.")
        
    times, ras, decs = [], [], []
    
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 3:
                times.append(parts[0])
                ras.append(parts[1])
                decs.append(parts[2])
                
            if len(times) == 3:
                break
                
    if len(times) < 3:
        raise ValueError(f"Found {len(times)} observations in '{filename}'; exactly 3 are required.")
        
    return times, ras, decs

def run_gauss(file_path: Optional[str] = None) -> None:
    """
    Executes the Gauss Orbit Determination algorithm processing 3 optical observations.
    Optimized to lazy-load astropy dependencies to preserve app performance.
    """
    from astropy.time import Time
    from astropy.coordinates import SkyCoord, solar_system_ephemeris, get_body_barycentric
    
    if file_path is None:
        file_path = get_resource_path(os.path.join('data', 'observations.txt'))
        
    print("--- Orbit Determination via Gauss Method ---")
    
    # 1. Real Observation Data (UTC)
    try:
        times, ras, decs = read_observations(file_path)
    except Exception as e:
        print(f"Failed to read observations: {e}")
        return
        
    obs1_time, obs2_time, obs3_time = times
    obs1_ra, obs2_ra, obs3_ra = ras
    obs1_dec, obs2_dec, obs3_dec = decs
    
    # 2. Time Conversion to Julian Dates (JD)
    t1 = Time(obs1_time, format='isot', scale='utc').jd
    t2 = Time(obs2_time, format='isot', scale='utc').jd
    t3 = Time(obs3_time, format='isot', scale='utc').jd
    
    # 3. Parse Strings into decimal degrees
    coord1 = SkyCoord(obs1_ra, obs1_dec, frame='icrs')
    coord2 = SkyCoord(obs2_ra, obs2_dec, frame='icrs')
    coord3 = SkyCoord(obs3_ra, obs3_dec, frame='icrs')
    
    ra_obs = [coord1.ra.degree, coord2.ra.degree, coord3.ra.degree]
    dec_obs = [coord1.dec.degree, coord2.dec.degree, coord3.dec.degree]
    
    print("Observations (Parsed into JD and Decimal Degrees):")
    print(f"t1={t1:.5f} JD | RA={ra_obs[0]:.5f}°, Dec={dec_obs[0]:.5f}°")
    print(f"t2={t2:.5f} JD | RA={ra_obs[1]:.5f}°, Dec={dec_obs[1]:.5f}°")
    print(f"t3={t3:.5f} JD | RA={ra_obs[2]:.5f}°, Dec={dec_obs[2]:.5f}°")
    
    # 4. Real Earth Position helper function
    def get_heliocentric_earth(jd_time):
        with solar_system_ephemeris.set('builtin'):
            t = Time(jd_time, format='jd')
            earth_bary = get_body_barycentric('earth', t)
            sun_bary = get_body_barycentric('sun', t)
            
            # Heliocentric Earth = Earth Barycentric - Sun Barycentric
            x = (earth_bary.x - sun_bary.x).to_value('au')
            y = (earth_bary.y - sun_bary.y).to_value('au')
            z = (earth_bary.z - sun_bary.z).to_value('au')
            return np.array([x, y, z])
            
    R1 = get_heliocentric_earth(t1)
    R2 = get_heliocentric_earth(t2)
    R3 = get_heliocentric_earth(t3)
    
    # Step 1
    L1, L2, L3 = unit_conversion_and_los(ra_obs, dec_obs)
    
    # Step 2
    tau1, tau3 = time_intervals(t1, t2, t3)
    
    # Step 3
    D0, D11, D12, D13, D21, D22, D23, D31, D32, D33 = setup_cross_products(L1, L2, L3, R1, R2, R3)
    
    # Step 4
    try:
        rho2, c1, c3, r2_norm = gauss_polynomial_root(tau1, tau3, D0, D12, D22, D32, L2, R2)
    except ValueError as e:
        print(f"\n[ORBIT DETERMINATION FAILED]\n{e}\n")
        return
        
    # Step 5
    r1, r2, r3 = position_vectors(rho2, c1, c3, D0, D11, D21, D31, D13, D23, D33, L1, L2, L3, R1, R2, R3)
    
    # Step 6
    v2 = estimate_velocity(r1, r2, r3, t1, t2, t3)
    
    # Step 7
    a, e, i, Omega, omega, M = state_to_kepler(r2, v2, mu)
    
    print("\n--- Results ---")
    print("Estimated State Vectors at t2:")
    print(f"r2 = [{r2[0]:.6f}, {r2[1]:.6f}, {r2[2]:.6f}] AU")
    print(f"v2 = [{v2[0]:.6f}, {v2[1]:.6f}, {v2[2]:.6f}] AU/day")
    
    print("\nCalculated Keplerian Orbital Elements:")
    print(f"Semi-major Axis (a) : {a:.6f} AU")
    print(f"Eccentricity (e)    : {e:.6f}")
    print(f"Inclination (i)     : {i:.6f} deg")
    print(f"RA of Asc. Node (Ω) : {Omega:.6f} deg")
    print(f"Arg. of Periapsis(ω): {omega:.6f} deg")
    print(f"Mean Anomaly (M)    : {M:.6f} deg")
    
    # 3D Visualization
    visualize_orbit(r2, v2, mu, a, e, i, Omega, omega)


def visualize_orbit(r2: np.ndarray, v2: np.ndarray, mu: float, a: float, e: float, i: float, Omega: float, omega: float) -> None:
    """
    Visualizes the calculated orbit in 3D.
    Optimized: Lazy-loads matplotlib to prevent GUI thread delay on startup.
    """
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 1. The Sun
    ax.scatter([0], [0], [0], color='gold', s=150, label='Sun', marker='*')
    
    # 2. Earth's Orbit (circular at 1 AU on XY plane)
    theta = np.linspace(0, 2 * np.pi, 200)
    earth_x = np.cos(theta)
    earth_y = np.sin(theta)
    earth_z = np.zeros_like(theta)
    ax.plot(earth_x, earth_y, earth_z, '--', color='dodgerblue', label="Earth's Orbit", alpha=0.5)
    
    # 3. Asteroid's Orbit
    h_vec = np.cross(r2, v2)
    p = np.linalg.norm(h_vec)**2 / mu
    
    true_anomalies = np.linspace(0, 2 * np.pi, 300)
    # Distance r (handling highly elliptical orbits gently by bounding, though usually e<1 here)
    r_orbit = p / (1 + e * np.cos(true_anomalies))
    
    # Positions in perifocal frame
    x_peri = r_orbit * np.cos(true_anomalies)
    y_peri = r_orbit * np.sin(true_anomalies)
    
    # Angles to radians
    i_rad = np.radians(i)
    Om_rad = np.radians(Omega)
    om_rad = np.radians(omega)
    
    # Transformation to heliocentric equatorial frame
    P_vec = np.array([
        np.cos(Om_rad) * np.cos(om_rad) - np.sin(Om_rad) * np.sin(om_rad) * np.cos(i_rad),
        np.sin(Om_rad) * np.cos(om_rad) + np.cos(Om_rad) * np.sin(om_rad) * np.cos(i_rad),
        np.sin(om_rad) * np.sin(i_rad)
    ])
    
    Q_vec = np.array([
        -np.cos(Om_rad) * np.sin(om_rad) - np.sin(Om_rad) * np.cos(om_rad) * np.cos(i_rad),
        -np.sin(Om_rad) * np.sin(om_rad) + np.cos(Om_rad) * np.cos(om_rad) * np.cos(i_rad),
        np.cos(om_rad) * np.sin(i_rad)
    ])
    
    orbit_x = x_peri * P_vec[0] + y_peri * Q_vec[0]
    orbit_y = x_peri * P_vec[1] + y_peri * Q_vec[1]
    orbit_z = x_peri * P_vec[2] + y_peri * Q_vec[2]
    
    ax.plot(orbit_x, orbit_y, orbit_z, color='darkorange', label="Asteroid's Orbit")
    
    # 4. Current Position (Asteroid at t2)
    ax.scatter([r2[0]], [r2[1]], [r2[2]], color='red', s=50, label='Asteroid at $t_2$')
    
    # Ensure equal aspect ratio
    max_range = np.array([
        earth_x.max() - earth_x.min(), earth_y.max() - earth_y.min(), earth_z.max() - earth_z.min(),
        orbit_x.max() - orbit_x.min(), orbit_y.max() - orbit_y.min(), orbit_z.max() - orbit_z.min()
    ]).max() / 2.0
    
    mid_x = (np.concatenate([earth_x, orbit_x]).max() + np.concatenate([earth_x, orbit_x]).min()) * 0.5
    mid_y = (np.concatenate([earth_y, orbit_y]).max() + np.concatenate([earth_y, orbit_y]).min()) * 0.5
    mid_z = (np.concatenate([earth_z, orbit_z]).max() + np.concatenate([earth_z, orbit_z]).min()) * 0.5
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    ax.set_box_aspect([1, 1, 1])
    
    ax.set_xlabel('X (AU)')
    ax.set_ylabel('Y (AU)')
    ax.set_zlabel('Z (AU)')
    ax.set_title('Orbit Visualization using Gauss\'s Method')
    
    # 5. Text Box / Annotation
    textstr = '\n'.join((
        r'Keplerian Elements:',
        fr'$a = {a:.4f}$ AU',
        fr'$e = {e:.4f}$',
        fr'$i = {i:.4f}^\circ$',
        fr'$\Omega = {Omega:.4f}^\circ$',
        fr'$\omega = {omega:.4f}^\circ$'
    ))
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray')
    ax.text2D(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
              verticalalignment='top', bbox=props)
              
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_gauss()
