import math

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in meters.
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    
    # Radius of earth in kilometers is 6371
    # Convert to meters
    r = 6371000 
    return c * r

def is_within_geofence(user_lat: float, user_lon: float, building_lat: float, building_lon: float, radius: float, accuracy: float = 0.0) -> tuple[bool, float]:
    """
    Checks if a user is within the geofence of a building.
    Returns (is_valid: bool, distance_in_meters: float).
    Allows tolerance based on GPS accuracy.
    """
    distance = calculate_haversine_distance(user_lat, user_lon, building_lat, building_lon)
    # The condition includes accuracy to be forgiving to weak GPS signals.
    is_valid = distance <= (radius + accuracy)
    return is_valid, distance

