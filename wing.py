from typing import List, Tuple
from geomdl import BSpline
from geomdl import utilities as utils
import numpy as np
import plotly.graph_objs as go

# Type aliases for better readability
AirfoilPoint = Tuple[float, float, float]
PlanformSection = Tuple[float, float, float]

def scale_and_sweep_airfoil(
    airfoil: List[AirfoilPoint],
    chord: float,
    sweep_angle: float,
    span_pos: float
) -> List[AirfoilPoint]:
    """
    Scales and sweeps the airfoil profile based on the chord length, sweep angle, and span position.
   
    Args:
        airfoil: List of (x, y, z) tuples representing the airfoil profile.
        chord: Chord length of the wing section.
        sweep_angle: Sweep angle of the wing section in degrees.
        span_pos: Span position of the wing section.

    Returns:
        List of (x, y, z) tuples representing the swept and scaled airfoil profile.
    """
    # Scale the airfoil points based on the chord length
    scaled_airfoil = [[x * chord, y * chord, 0] for x, y, z in airfoil]
   
    # Calculate the sweep distance
    sweep_dist = span_pos * np.tan(np.radians(sweep_angle))
   
    # Apply the sweep offset
    swept_airfoil = [[x + sweep_dist, y, z + span_pos] for x, y, z in scaled_airfoil]
   
    return swept_airfoil

def generate_wing_geometry(
    airfoil: List[AirfoilPoint],
    planform: List[PlanformSection]
) -> List[List[AirfoilPoint]]:
    """
    Generates the wing geometry by scaling and sweeping airfoil sections according to the planform.
   
    Args:
        airfoil: List of (x, y, z) tuples representing the base airfoil profile.
        planform: List of tuples defining each wing section with span position, chord length, and sweep angle.
   
    Returns:
        List of airfoil profiles for each section of the wing.
    """
    wing_sections = []
    for span_pos, chord, sweep_angle in planform:
        section = scale_and_sweep_airfoil(airfoil, chord, sweep_angle, span_pos)
        wing_sections.append(section)
   
    return wing_sections

def create_nurbs_surface_from_sections(
    wing_sections: List[List[AirfoilPoint]]
) -> BSpline.Surface:
    """
    Creates a NURBS surface from the provided wing sections.

    Args:
        wing_sections: List of airfoil profiles, each representing a wing section.
   
    Returns:
        A BSpline.Surface object representing the NURBS surface.
   
    Raises:
        ValueError: If the number of control points is less than the degree of the surface + 1.
    """
    surface = BSpline.Surface()

    num_u = len(wing_sections[0])  # Number of points in each airfoil section
    num_v = len(wing_sections)     # Number of airfoil sections

    # Ensure sufficient number of control points
    if num_u < 4 or num_v < 4:
        raise ValueError("Not enough control points. Need at least degree + 1 in each direction.")

    # Set degrees (ensure degrees are less than the number of control points)
    surface.degree_u = min(num_u - 1, 3)  # Ensure degree <= num_control_points - 1
    surface.degree_v = min(num_v - 1, 3)

    # Define control points grid from airfoil sections
    control_points = []
    for i in range(num_u):  # For each point on an airfoil curve
        row = []
        for j in range(num_v):  # Across all airfoil sections
            row.append(wing_sections[j][i])
        control_points.append(row)

    # Flatten control points for geomdl format
    surface.ctrlpts2d = control_points

    # Generate knot vectors
    surface.knotvector_u = utils.generate_knot_vector(surface.degree_u, len(control_points))
    surface.knotvector_v = utils.generate_knot_vector(surface.degree_v, len(wing_sections))

    return surface

def nurbs_to_plotly_mesh(
    nurbs_surface: BSpline.Surface,
    num_u: int = 50,
    num_v: int = 50
) -> go.Surface:
    """
    Converts a NURBS surface to Plotly mesh data for visualization.
   
    Args:
        nurbs_surface: The NURBS surface to be converted.
        num_u: Number of points to evaluate in the u direction.
        num_v: Number of points to evaluate in the v direction.
   
    Returns:
        A Plotly `Surface` object for visualization.
    """
    # Evaluate surface points in a grid (u, v)
    surface_points = nurbs_surface.evalpts
   
    # Extract X, Y, Z coordinates from the surface points
    x_vals = []
    y_vals = []
    z_vals = []
   
    for pt in surface_points:
        x_vals.append(pt[0])
        y_vals.append(pt[1])
        z_vals.append(pt[2])
   
    # Convert the points to a structured grid for plotting
    x_grid = np.array(x_vals).reshape((num_u, num_v))
    y_grid = np.array(y_vals).reshape((num_u, num_v))
    z_grid = np.array(z_vals).reshape((num_u, num_v))
   
    # Create Plotly mesh3d object
    mesh = go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale='Viridis', opacity=0.7)
    return mesh

# Example usage
airfoil_points: List[AirfoilPoint] = [
    [1.0, 0.0, 0.0], [0.9, 0.05, 0.0], [0.8, 0.08, 0.0], [0.7, 0.10, 0.0],
    [0.6, 0.08, 0.0], [0.5, 0.06, 0.0], [0.4, 0.04, 0.0], [0.3, 0.02, 0.0],
    [0.2, 0.01, 0.0], [0.1, 0.0, 0.0], [0.0, 0.0, 0.0]
]

planform: List[PlanformSection] = [
    [0, 1.5, 0],   # Root: span=0, chord=1.5, sweep angle=0 degrees
    [5, 1.0, 5],   # Mid: span=5, chord=1.0, sweep angle=5 degrees
    [7, 1.0, 5],   # Mid: span=5, chord=1.0, sweep angle=5 degrees
    [10, 0.5, 10]  # Tip: span=10, chord=0.5, sweep angle=10 degrees
]

# Generate the wing geometry (airfoil sections)
wing_sections = generate_wing_geometry(airfoil_points, planform)

# Create the NURBS surface from the wing sections
nurbs_surface = create_nurbs_surface_from_sections(wing_sections)

# Convert NURBS surface to Plotly mesh
nurbs_mesh = nurbs_to_plotly_mesh(nurbs_surface)

# Set up the 3D plot layout
layout = go.Layout(
    scene=dict(
        xaxis=dict(title='X (Sweep)'),
        yaxis=dict(title='Y (Chord)'),
        zaxis=dict(title='Z (Span)')
    ),
    title="NURBS-Based 3D Wing Geometry"
)

# Create the figure and plot
fig = go.Figure(data=[nurbs_mesh], layout=layout)
fig.show()
