import unittest

from reckon_crm.utils.geo import coordinates, distance_metres, verify_position


class GeofenceTests(unittest.TestCase):
    def test_known_distances_and_zero_coordinates(self):
        self.assertEqual(distance_metres(0, 0, 0, 0), 0)
        self.assertAlmostEqual(distance_metres(0, 0, 0, 1), 111195.08, places=1)
        self.assertAlmostEqual(distance_metres(0, 179.999, 0, -179.999), 222.39, places=1)

    def test_invalid_and_nonfinite_inputs_rejected(self):
        for lat, lon in [(91, 0), (0, 181), (float("nan"), 0), (0, float("inf")), (None, 0), (True, 0), ("", 0)]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(ValueError):
                coordinates(lat, lon)

    def test_classification_does_not_claim_verification_without_target_or_sample(self):
        target = {"latitude": 0, "longitude": 0, "geofence_radius": 100}
        self.assertEqual(verify_position(0, 0, 5, target)["geo_status"], "Within Radius")
        self.assertEqual(verify_position(0, 0.01, 5, target)["geo_status"], "Outside Radius")
        self.assertEqual(verify_position(0, 0, 101, target)["geo_status"], "Accuracy Too Low")
        self.assertEqual(verify_position(None, None, None, target)["geo_status"], "Location Unavailable")
        self.assertEqual(verify_position(0, 0, 5)["geo_status"], "Not Checked")
        for sample in [(0, 0, -1), (0, None, 5), (None, None, 5), (0, 0, None)]:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                verify_position(*sample, target)
