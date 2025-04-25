import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
import os
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class RouteValidator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.routes = {}
        
    def add_route(self, route_id, from_city, to_city, via_cities):
        """Add a route with waypoints to the validator."""
        # Combine all cities in the correct order
        all_points = [from_city] + via_cities + [to_city]
        self.routes[route_id] = {
            'from': from_city,
            'to': to_city,
            'via': via_cities,
            'all_points': all_points,
            'geocoded_path': None  # Will be populated when needed
        }
    
    def geocode_address(self, address):
        """Convert address to geocoordinates using Google Places API."""
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            'input': address,
            'inputtype': 'textquery',
            'fields': 'formatted_address,geometry',
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] != 'OK' or not data.get('candidates'):
            return None, None
        
        result = data['candidates'][0]
        lat = result['geometry']['location']['lat']
        lng = result['geometry']['location']['lng']
        formatted_address = result['formatted_address']
        
        return (lat, lng), formatted_address
    
    def get_directions(self, origin, destination, waypoints=None):
        """Get directions between points using Google Directions API."""
        url = "https://maps.googleapis.com/maps/api/directions/json"
        
        params = {
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'key': self.api_key
        }
        
        if waypoints:
            waypoint_str = "|".join([f"{wp[0]},{wp[1]}" for wp in waypoints])
            params['waypoints'] = waypoint_str
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] != 'OK':
            return None
        
        # Extract the polyline points from the response
        points = []
        for leg in data['routes'][0]['legs']:
            for step in leg['steps']:
                points.extend(polyline.decode(step['polyline']['points']))
        
        return points
    
    def haversine_distance(self, point1, point2):
        """Calculate the great-circle distance between two points in kilometers."""
        # Convert decimal degrees to radians
        lat1, lon1 = radians(point1[0]), radians(point1[1])
        lat2, lon2 = radians(point2[0]), radians(point2[1])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = 6371 * c  # Earth radius is 6371 km
        
        return distance
    
    def point_to_path_distance(self, point, path):
        """Calculate minimum distance from a point to a path."""
        min_distance = float('inf')
        for path_point in path:
            distance = self.haversine_distance(point, path_point)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def ensure_route_geocoded(self, route_id):
        """Make sure the route has geocoded path information."""
        route = self.routes.get(route_id)
        if not route:
            return False
        
        if not route['geocoded_path']:
            # Geocode all points
            waypoints = []
            for city in route['all_points']:
                coords, _ = self.geocode_address(city)
                if not coords:
                    return False
                waypoints.append(coords)
            
            # Get route path from Directions API
            origin = waypoints[0]
            destination = waypoints[-1]
            middle_waypoints = waypoints[1:-1] if len(waypoints) > 2 else None
            
            path = self.get_directions(origin, destination, middle_waypoints)
            if not path:
                return False
            
            route['geocoded_path'] = path
            
        return True
    
    def validate_user_trip(self, pickup_address, drop_address, max_distance_km=30):
        """
        Validate if a user's pickup and drop points are on any of the defined routes.
        max_distance_km: Maximum allowed distance from the route (in kilometers)
        """
        # Geocode user input
        pickup_coords, formatted_pickup = self.geocode_address(pickup_address)
        drop_coords, formatted_drop = self.geocode_address(drop_address)
        
        if not pickup_coords or not drop_coords:
            print("coming in here")
            return {
                'valid': False,
                'error': 'Could not geocode one or both addresses',
                'pickup_coords': pickup_coords,
                'drop_coords': drop_coords
            }
        
        # Check each route
        valid_routes = []
        for route_id, route in self.routes.items():
            if not self.ensure_route_geocoded(route_id):
                continue
            
            # Calculate distances from points to route
            pickup_distance = self.point_to_path_distance(pickup_coords, route['geocoded_path'])
            drop_distance = self.point_to_path_distance(drop_coords, route['geocoded_path'])
            
            if pickup_distance <= max_distance_km and drop_distance <= max_distance_km:
                valid_routes.append({
                    'route_id': route_id,
                    'from': route['from'],
                    'to': route['to'],
                    'pickup_distance_km': round(pickup_distance, 2),
                    'drop_distance_km': round(drop_distance, 2)
                })
        
        return {
            'valid': len(valid_routes) > 0,
            'pickup_address': formatted_pickup,
            'drop_address': formatted_drop,
            'pickup_coords': pickup_coords,
            'drop_coords': drop_coords,
            'matching_routes': valid_routes
        }

# Example usage
def main():
    # You need to get a Google API key with Places API and Directions API enabled
    validator = RouteValidator("AIzaSyB-Z1yfO79TH2uuDT9-fu-0YmHCRL_B9IA")
    
    # Add the route from your example
    validator.add_route(
        route_id="ahmedabad_junagadh",
        from_city="Ahmedabad, Gujarat, India",
        to_city="Junagadh, Gujarat, India",
        via_cities=["Lathi, Gujarat, India", "Dhasa, Gujarat, India", 
                    "Amreli, Gujarat, India", "Dhari, Gujarat, India", "Bilkha, Gujarat, India"]
    )
    
    # Test with user input
    pickup = "Ahmedabad, Gujarat, India"
    drop = "lakhapadar, Gujarat, India"
    
    result = validator.validate_user_trip(pickup, drop)
    
    if result['valid']:
        print(f"✅ Valid trip! The journey from {result['pickup_address']} to {result['drop_address']} is along these routes:")
        for route in result['matching_routes']:
            print(f"  - Route from {route['from']} to {route['to']}")
            print(f"    (Pickup is {route['pickup_distance_km']}km from route, Drop is {route['drop_distance_km']}km from route)")
    else:
        print(f"❌ Invalid trip. The journey from {result.get('pickup_address', pickup)} to {result.get('drop_address', drop)} doesn't match any defined routes.")
        if 'error' in result:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()