"""Pure server-side location validation. Browser GPS is not proof against spoofing."""

import math


def finite_number(value, label, minimum, maximum):
    if isinstance(value, bool) or value is None or value == "":
        raise ValueError(f"{label} is required.")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a number.") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def coordinates(latitude, longitude):
    return (finite_number(latitude, "Latitude", -90, 90),
            finite_number(longitude, "Longitude", -180, 180))


def distance_metres(latitude, longitude, target_latitude, target_longitude):
    lat, lon = coordinates(latitude, longitude)
    target_lat, target_lon = coordinates(target_latitude, target_longitude)
    phi, target_phi = math.radians(lat), math.radians(target_lat)
    d_phi, d_lambda = target_phi - phi, math.radians(target_lon - lon)
    value = math.sin(d_phi / 2) ** 2 + math.cos(phi) * math.cos(target_phi) * math.sin(d_lambda / 2) ** 2
    return 6371008.8 * 2 * math.asin(math.sqrt(min(1, max(0, value))))


def verify_position(latitude, longitude, accuracy, location=None):
    """Classify a single sample; distance and radius are never accepted from a client."""
    if latitude is None and longitude is None:
        if accuracy is not None:
            raise ValueError("Accuracy requires coordinates.")
        return {"geo_status": "Location Unavailable", "distance_from_customer": None}
    lat, lon = coordinates(latitude, longitude)
    precision = finite_number(accuracy, "GPS accuracy", 0, 100000)
    distance = None
    if location:
        distance = distance_metres(lat, lon, location["latitude"], location["longitude"])
    if precision > 100:
        status = "Accuracy Too Low"
    elif location is None:
        status = "Not Checked"
    else:
        radius = finite_number(location["geofence_radius"], "Geofence radius", 1, 10000)
        status = "Within Radius" if distance <= radius else "Outside Radius"
    return {"geo_status": status, "distance_from_customer": distance}
