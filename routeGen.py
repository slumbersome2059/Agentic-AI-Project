"""
This script creates a Flask web application for generating random running routes.

It provides a single API endpoint `/api/generate-route` that accepts a user's
postcode and a desired running distance. The application then uses the osmnx
and NetworkX libraries to fetch a street map of the area, generates a roughly
circular route of the specified length, and returns the route as a list of
latitude/longitude coordinates. It also uses the Gemini API to generate
turn-by-turn directions for the route.
"""

# 1. Import necessary libraries
import os
import random
from typing import List, Tuple, Optional, Dict

import networkx as nx
import osmnx as ox
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from geopy.geocoders import Nominatim
from networkx import MultiDiGraph
import google.generativeai as genai


# 3. Initialize Flask App and enable CORS
app: Flask = Flask(__name__)
CORS(app)

# Configure osmnx to cache data
#ox.config(use_cache=True, log_console=True)


def geocode_postcode(postcode: str, country: str = "UK") -> Optional[Tuple[float, float]]:
    """
    Converts a postcode to (latitude, longitude) coordinates.

    Args:
        postcode: The postcode string to geocode.
        country: The country where the postcode is located. Defaults to "UK".

    Returns:
        A tuple containing the latitude and longitude, or None if
        geocoding fails.
    """
    geolocator = Nominatim(user_agent="running_route_generator")
    try:
        location = geolocator.geocode(f"{postcode}, {country}")
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None


# 6. Define the API route for route generation
@app.route('/api/generate-route', methods=['POST'])
def generate_route() -> Response:
    """
    Receives postcode and distance, generates a route, and returns it as JSON.

    This Flask route handles POST requests. It expects a JSON payload with
    'postcode' and 'distance' keys. It uses osmnx to generate a walking route
    that starts and ends near the given postcode and is approximately the
    target distance.

    Returns:
        A Flask Response object containing the route coordinates in JSON format,
        or an error message if the process fails.
    """
    try:
        data: dict = request.get_json()
        postcode: Optional[str] = data.get('postcode')
        target_distance_km: float = float(data.get('distance', 0))

        if not postcode or not target_distance_km:
            return jsonify({"error": "Postcode and distance are required."}), 400

        print(f"Starting route generation for {postcode} and {target_distance_km}km.")

        # Step 1: Geocode the postcode to get starting coordinates
        start_coords: Optional[Tuple[float, float]] = geocode_postcode(postcode)
        if not start_coords:
            return jsonify({"error": "Could not geocode postcode. Please check if it is valid."}), 400

        print(f"Geocoded {postcode} to {start_coords}")

        # Step 2: Download the street network graph for the area
        # We download a larger area to ensure we can create a route of the desired length.
        graph_radius: float = (target_distance_km * 1000) / 2
        G: MultiDiGraph = ox.graph_from_point(start_coords, dist=graph_radius, network_type='walk', simplify=True)
        # Project the graph to a local CRS to get distances in meters
        G_proj: MultiDiGraph = ox.project_graph(G)

        start_node: int = ox.nearest_nodes(G, start_coords[1], start_coords[0])

        # Step 3: Generate the route using a random walk and shortest path back
        path: List[int] = [start_node]
        current_distance: float = 0.0

        # Go out for about 60-70% of the target distance
        val: float = random.uniform(0.6, 0.7)
        outbound_target: float = target_distance_km * 1000 * val

        while current_distance < outbound_target:
            current_node: int = path[-1]
            neighbors: List[int] = list(G_proj.neighbors(current_node))

            # Avoid simple backtracking
            if len(path) > 1 and len(neighbors) > 1:
                neighbors.remove(path[-2])

            if not neighbors:
                break  # Dead end

            next_node: int = random.choice(neighbors)

            # Add edge length to current distance
            edge_length: float = G_proj.get_edge_data(current_node, next_node)[0].get('length', 0)
            current_distance += edge_length
            path.append(next_node)

        mid_point_node: int = path[-1]

        # Step 4: Find the shortest path back to the start
        try:
            return_path: List[int] = nx.shortest_path(G_proj, source=mid_point_node, target=start_node, weight='length')
            sl: float = nx.shortest_path_length(G_proj, source=mid_point_node, target=start_node, weight='length')
            print("Shortest length is " + str(sl))
            print("total length " + str(val * target_distance_km * 1000 + sl))
            full_path_nodes: List[int] = path + return_path[1:]  # Combine without duplicating the midpoint
        except nx.NetworkXNoPath:
            # If no path back is found, just use the outbound path
            print("Warning: No path found back to start. Using outbound path only.")
            full_path_nodes = path

        # Step 5: Convert node IDs back to lat/lon coordinates
        route_coords: List[List[float]] = []
        streetNames: Dict[Tuple[float, float], str] = {}
        start: bool = True
        prev_node_id: Optional[int] = None
        for node_id in full_path_nodes:
            node_data: dict = G.nodes[node_id]
            route_coords.append([node_data['y'], node_data['x']])
            if not start and prev_node_id is not None:
                edge_data = G.get_edge_data(prev_node_id, node_id)
                street_name = edge_data[0].get('name', 'unnamed street') if edge_data else 'unnamed street'
                streetNames[tuple(route_coords[-2])] = street_name
            else:
                start = False
            prev_node_id = node_id

        print(f"Generated route with {len(route_coords)} points.")

        # Generating directions
        def get_street_name(latLongCoords: List[float]) -> str:
            """
            Finds the street name for a given latitude and longitude coordinate.

            Args:
                latLongCoords: A list containing latitude and longitude.

            Returns:
                The name of the street at the given coordinates.
            """
            return streetNames.get(tuple(latLongCoords), "Unknown Street")

        genai.configure(api_key=${{secrets.GEMINI_API_KEY}})
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            tools=[get_street_name],
            system_instruction=(
                "You should give your answer in one shot trying to be as helpful as possible. Don't ask further questions. "
                "You are a bot that gives directions to get from one latitude, longitude coordinate to another. "
                "You should always use the get_street_name tool to get the street name of a coordinate. "
                "Add which direction you should take to change street. "
                "Try to add how many metres there are until you need to change direction."
            )
        )
        prompt: str = "Give me directions for a route based on the following coords: " + str(route_coords)
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(prompt)

        print(response.text)
        return jsonify({"route": route_coords, "directions": response.text})

    except Exception as e:
        print(f"An error occurred during route generation: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# 7. Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5002)