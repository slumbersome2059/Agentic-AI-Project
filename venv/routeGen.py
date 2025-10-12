# 1. Import necessary libraries
import os
import random
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from flask import Flask, request, jsonify
from flask_cors import CORS
import scipy
# 3. Initialize Flask App and enable CORS
app = Flask(__name__)
CORS(app)

# Configure osmnx to cache data
#ox.config(use_cache=True, log_console=True)

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

# 6. Define the API route for route generation
@app.route('/api/generate-route', methods=['POST'])
def generate_route():
    """
    Receives postcode and distance, generates a route using osmnx,
    and returns it as a JSON object.
    """
    try:
        data = request.get_json()
        postcode = data.get('postcode')
        target_distance_km = float(data.get('distance', 0))

        if not postcode or not target_distance_km:
            return jsonify({"error": "Postcode and distance are required."}), 400

        print(f"Starting route generation for {postcode} and {target_distance_km}km.")

        # Step 1: Geocode the postcode to get starting coordinates
        start_coords = geocode_postcode(postcode)
        if not start_coords:
            return jsonify({"error": "Could not geocode postcode. Please check if it is valid."}), 400
        
        print(f"Geocoded {postcode} to {start_coords}")

        # Step 2: Download the street network graph for the area
        # We download a larger area to ensure we can create a route of the desired length.
        # The distance is in meters for osmnx.
        graph_radius = (target_distance_km * 1000) / 2 
        G = ox.graph_from_point(start_coords, dist=graph_radius, network_type='walk', simplify=True)
        # Project the graph to a local CRS to get distances in meters
        G_proj = ox.project_graph(G)
        
        start_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
        
        
        # Step 3: Generate the route using a random walk and shortest path back
        # This is a simplified algorithm to find a roughly circular route.
        
        path = [start_node]
        current_distance = 0
        
        # Go out for about 60-70% of the target distance
        val = random.uniform(0.6, 0.7)
        outbound_target = target_distance_km * 1000 * (val)
        
        while current_distance < outbound_target:
            current_node = path[-1]
            neighbors = list(G_proj.neighbors(current_node))
            
            # Avoid simple backtracking
            if len(path) > 1 and len(neighbors) > 1:
                neighbors.remove(path[-2])
            
            if not neighbors:
                break # Dead end
            
            # Choose the next node
            next_node = random.choice(neighbors)
            
            # Add edge length to current distance
            edge_length = G_proj.get_edge_data(current_node, next_node)[0].get('length', 0)
            current_distance += edge_length
            path.append(next_node)

        mid_point_node = path[-1]
        
        # Step 4: Find the shortest path back to the start
        try:
            return_path = nx.shortest_path(G_proj, source=mid_point_node, target=start_node, weight='length')
            sl = nx.shortest_path_length(G_proj, source=mid_point_node, target=start_node, weight='length')
            print("Shortest length is " + str(sl))
            print("total length " + str(val*target_distance_km*1000 + sl))
            full_path_nodes = path + return_path[1:] # Combine without duplicating the midpoint
        except nx.NetworkXNoPath:
            # If no path back is found, just use the outbound path
            print("Warning: No path found back to start. Using outbound path only.")
            full_path_nodes = path

        # Step 5: Convert node IDs back to lat/lon coordinates
        route_coords = []
        for node_id in full_path_nodes:
            node_data = G.nodes[node_id]
            route_coords.append([node_data['y'], node_data['x']])
        
            
        print(f"Generated route with {len(route_coords)} points.")
        
        return jsonify({"route": route_coords})

    except Exception as e:
        print(f"An error occurred during route generation: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# 7. Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5002)

