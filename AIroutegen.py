from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
from typing import Optional, Tuple, List, Union
import google.generativeai as genai
import os

# Define a type alias for node IDs for clarity, as they can be ints or strings
NodeType = Union[int, str]



def geocode_postcode(postcode: str, country: str = "UK") -> Optional[Tuple[float, float]]:
    """
    Converts a postcode to (latitude, longitude) coordinates.

    Args:
        postcode: The postcode string to be geocoded.
        country: The country associated with the postcode. Defaults to "UK".

    Returns:
        A tuple containing the latitude and longitude, or None if the
        postcode could not be geocoded.
    """
    print("USEd")
    geolocator = Nominatim(user_agent="running_route_generator")
    try:
        location = geolocator.geocode(f"{postcode}, {country}")
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def gen_proj_Graph(start_coords: Tuple[float, float], target_distance_km: float) -> nx.MultiDiGraph:
    """
    Generates a projected walkable street network graph from a starting point.

    The graph is built within a radius derived from the target distance,
    ensuring enough area is covered for route calculation. It is projected
    to a local CRS to allow for accurate distance measurements in meters.

    Args:
        start_coords: A tuple of (latitude, longitude) for the center point.
        target_distance_km: The target distance for a potential route, used to
                           determine the radius of the graph to download.

    Returns:
        A projected NetworkX MultiDiGraph.
    """
    # Calculate radius for the graph download (half the target distance)
    graph_radius = (target_distance_km * 1000) / 2
    G = ox.graph_from_point(start_coords, dist=graph_radius, network_type='walk', simplify=True)
    # Project the graph to a local CRS to get distances in meters
    G_proj = ox.project_graph(G)
    return G_proj

def get_start_node(start_coords: Tuple[float, float], G_proj: nx.MultiDiGraph) -> NodeType:
    """
    Finds the nearest graph node to a given (latitude, longitude) point.

    Args:
        start_coords: A tuple of (latitude, longitude).
        G_proj: A projected NetworkX graph.

    Returns:
        The ID of the nearest node in the graph.
    """
    # Note: osmnx expects (y, x) which corresponds to (latitude, longitude)
    start_node = ox.nearest_nodes(G_proj, X=start_coords[1], Y=start_coords[0])
    return start_node

def get_neighbours(current_node: NodeType, G_proj: nx.MultiDiGraph) -> List[NodeType]:
    """
    Retrieves a list of neighboring nodes for a given node in the graph.

    Args:
        current_node: The ID of the node whose neighbors are to be found.
        G_proj: The NetworkX graph.

    Returns:
        A list of node IDs that are neighbors of the current_node.
    """
    return list(G_proj.neighbors(current_node))

def get_distance_between_two_nodes(G_proj: nx.MultiDiGraph, node1: NodeType, node2: NodeType) -> float:
    """
    Calculates the street distance (edge length) between two connected nodes.

    Args:
        G_proj: The projected NetworkX graph containing the nodes and edges.
        node1: The ID of the first node.
        node2: The ID of the second node.

    Returns:
        The length of the edge in meters. Returns 0 if no edge is found.
    """
    # Use .get() for safety, though an edge should exist if nodes are neighbors
    edge_data = G_proj.get_edge_data(node1, node2)
    # In a MultiDiGraph, there can be multiple edges; we take the first one.
    return edge_data[0].get('length', 0)

def get_shortest_path(G_proj: nx.MultiDiGraph, start_node: NodeType, end_node: NodeType) -> List[NodeType]:
    """
    Finds the shortest path between two nodes in the graph.

    The path is calculated using the 'length' attribute of the edges as the weight.

    Args:
        G_proj: The projected NetworkX graph.
        start_node: The ID of the starting node for the path.
        end_node: The ID of the ending node for the path.

    Returns:
        A list of node IDs representing the shortest path from start to end.
    """
    return nx.shortest_path(G_proj, source=start_node, target=end_node, weight='length')
def add(a:int, b:int) -> int:
    "Adds two nums together"
    return a + b
def subtract(a:int, b:int) -> int:
    "Adds two nums together"
    return a - b
genai.configure(api_key=${{secrets.GEMINI_API_KEY}})
model = genai.GenerativeModel(
    'gemini-2.5-flash-lite',
    tools = [geocode_postcode, gen_proj_Graph, get_distance_between_two_nodes, get_shortest_path, get_neighbours, get_distance_between_two_nodes, get_start_node]
    )
#prompt = "Add 423 and 400 together"
prompt = "Give me a runnning route of 5km that starts and finishes at CB21DQ " \
"Give the latitude and longitudes of the start of the roads. Try and make it so that the root is a loop" \
"so that you don't run back on the same road again"
chat = model.start_chat(enable_automatic_function_calling=True)
response = chat.send_message(prompt)
print(response.text)