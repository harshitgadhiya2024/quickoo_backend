import googlemaps
import polyline
import time
from datetime import datetime
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

API_KEY = 'AIzaSyB-Z1yfO79TH2uuDT9-fu-0YmHCRL_B9IA'
gmaps = googlemaps.Client(key=API_KEY)

class mapsIntergation():

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
                    'steps': []
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

