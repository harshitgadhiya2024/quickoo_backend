import googlemaps
import polyline
import time
from datetime import datetime
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

API_KEY = 'AIzaSyB-Z1yfO79TH2uuDT9-fu-0YmHCRL_B9IA'
gmaps = googlemaps.Client(key=API_KEY)

class MapsIntegration:

    def __init__(self):
        pass

    def get_directions(self, from_location, to_location, waypoints=None, mode="driving", alternatives=False):
        """
        Get directions between from and to.

        Args:
            from_location: String or (lat, lng) tuple, representing the start point
            destination: String or (lat, lng) tuple, representing the end point
            waypoints: List of waypoints (strings or (lat, lng) tuples)
            mode: String, one of "driving", "walking", "bicycling", "transit"
            alternatives: Boolean, whether to return more than one route

        Returns:
            Dictionary containing route information
        """
        try:
            # Additional parameters for the API request
            params = {
                'origin': from_location,
                'destination': to_location,
                'mode': mode,
                'alternatives': alternatives
            }

            # Add waypoints if provided
            if waypoints:
                params['waypoints'] = waypoints

            # Make the API request
            directions_result = gmaps.directions(**params)

            if not directions_result:
                return None

            # Process the results
            routes = []
            for route in directions_result:
                route_info = {
                    'summary': route['summary'],
                    'distance_text': route['legs'][0]['distance']['text'],
                    'distance_meters': route['legs'][0]['distance']['value'],
                    'duration_text': route['legs'][0]['duration']['text'],
                    'duration_seconds': route['legs'][0]['duration']['value'],
                    'start_address': route['legs'][0]['start_address'],
                    'end_address': route['legs'][0]['end_address'],
                    'steps': [],
                    'polyline': route['overview_polyline']['points']  # Store the encoded polyline
                }

                # Extract steps information
                for step in route['legs'][0]['steps']:
                    step_info = {
                        'distance_text': step['distance']['text'],
                        'duration_text': step['duration']['text'],
                        'instructions': step['html_instructions'],
                        'start_location': step['start_location'],
                        'end_location': step['end_location']
                    }
                    route_info['steps'].append(step_info)

                routes.append(route_info)

            return routes
        except Exception as e:
            print(f"Error getting directions: {e}")
            return None

    def find_cities_along_route(self, from_location, to_location, sample_points=10):
        """
        Find major cities along the route between from_location and to_location.
        
        Args:
            from_location: String or (lat, lng) tuple, representing the start point
            to_location: String or (lat, lng) tuple, representing the end point
            sample_points: Number of points to sample along the route
            
        Returns:
            List of dictionaries containing city information and distances
        """
        try:
            # Get the route
            routes = self.get_directions(from_location, to_location)
            if not routes:
                return None
                
            # Get the polyline from the first route
            encoded_polyline = routes[0]['polyline']
            path = polyline.decode(encoded_polyline)
            
            # Sample points along the route
            total_points = len(path)
            step_size = max(1, total_points // sample_points)
            sampled_path = [path[i] for i in range(0, total_points, step_size)]
            
            # Add the destination if it's not already in the sampled path
            if path[-1] not in sampled_path:
                sampled_path.append(path[-1])
            
            cities = []
            # For each point, perform reverse geocoding to find the nearest city
            for i, point in enumerate(sampled_path):
                if i == 0:  # Skip the starting point
                    continue
                    
                # Using reverse geocoding to get address information
                reverse_geocode_result = gmaps.reverse_geocode((point[0], point[1]), result_type='locality')
                
                city_info = None
                # Process the reverse geocode results
                for result in reverse_geocode_result:
                    for component in result['address_components']:
                        if 'locality' in component['types']:
                            city_name = component['long_name']
                            # Check if this city is already in our list
                            if not any(city['city_name'] == city_name for city in cities):
                                # Calculate the distance from the start
                                distance_from_start = self.calculate_distance_along_route(path, 0, i * step_size)
                                
                                city_info = {
                                    'city_name': city_name,
                                    'location': (point[0], point[1]),
                                    'distance_from_start_km': distance_from_start,
                                    'address': result['formatted_address']
                                }
                                cities.append(city_info)
                                break
                    if city_info:
                        break
                        
                # If no city was found, use the Places API to find nearby cities
                if not city_info:
                    places_result = gmaps.places_nearby(
                        location=(point[0], point[1]),
                        radius=10000,  # 10km radius
                        type='locality'
                    )
                    
                    if places_result['results']:
                        place = places_result['results'][0]
                        city_name = place['name']
                        # Check if this city is already in our list
                        if not any(city['city_name'] == city_name for city in cities):
                            # Calculate the distance from the start
                            distance_from_start = self.calculate_distance_along_route(path, 0, i * step_size)
                            
                            city_info = {
                                'city_name': city_name,
                                'location': (place['geometry']['location']['lat'], place['geometry']['location']['lng']),
                                'distance_from_start_km': distance_from_start,
                                'address': place.get('vicinity', 'Unknown')
                            }
                            cities.append(city_info)
                
                # Add a delay to avoid hitting API rate limits
                time.sleep(0.2)
                
            return cities
            
        except Exception as e:
            print(f"Error finding cities along route: {e}")
            return None
    
    def calculate_distance_along_route(self, path, start_idx, end_idx):
        """
        Calculate the distance along a route between two indices.
        
        Args:
            path: List of (lat, lng) tuples
            start_idx: Starting index in the path
            end_idx: Ending index in the path
            
        Returns:
            Distance in kilometers
        """
        total_distance = 0
        for i in range(start_idx, min(end_idx, len(path) - 1)):
            total_distance += self.haversine_distance(path[i], path[i + 1])
        return total_distance
    
    def haversine_distance(self, point1, point2):
        """
        Calculate the great circle distance between two points on the earth.
        
        Args:
            point1: (lat, lng) tuple for point 1
            point2: (lat, lng) tuple for point 2
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convert coordinates to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance


