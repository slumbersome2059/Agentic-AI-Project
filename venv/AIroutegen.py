from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
def geocode_postcode(postcode, country="UK"):
    """Converts a postcode to (latitude, longitude) coordinates."""
    geolocator = Nominatim(user_agent="running_route_generator")
    try:
        location = geolocator.geocode(f"{postcode}, {country}")
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None
def gen_proj_Graph(start_coords, target_distance_km):
    graph_radius = (target_distance_km * 1000) / 2 
    G = ox.graph_from_point(start_coords, dist=graph_radius, network_type='walk', simplify=True)
        # Project the graph to a local CRS to get distances in meters
    G_proj = ox.project_graph(G)
    return G_proj
def get_start_node(start_coords, G_proj):    
    start_node = ox.nearest_nodes(G_proj, start_coords[1], start_coords[0])
    return start_node
def get_neighbours(current_node, G_proj):
    return list(G_proj.neighbors(current_node))
def get_distance_between_two_nodes(G_proj, current_node, next_node):
    return G_proj.get_edge_data(current_node, next_node)[0].get('length', 0)
def get_shortest_path(G_proj, start_node, end_node):
    return nx.shortest_path(G_proj, source=start_node, target=end_node, weight='length')