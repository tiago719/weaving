import unittest
import numpy
from main import (
    get_velocity_and_displacement,
    moving_average,
    calculate_displacement,
    find_optimal_frequency,
)


class MockVelocityController:
    def __init__(self, velocities):
        self.velocities = velocities
        self.current_index = 0

    def get_velocity(self):
        if self.current_index < len(self.velocities):
            velocity = self.velocities[self.current_index]
            self.current_index += 1
            return velocity


class TestSurfaceMovementSystem(unittest.TestCase):
    def test_moving_average(self):
        data = numpy.array([1, 2, 3, 4, 5])
        window_size = 3
        result = moving_average(data, window_size)
        expected = numpy.array([2.0, 3.0, 4.0])
        self.assertTrue(numpy.allclose(result, expected))

    def test_calculate_displacement(self):
        velocity_data = [0.1, 0.2, 0.3, 0.4]
        time_interval = 1
        displacement = calculate_displacement(velocity_data, time_interval)
        self.assertAlmostEqual(displacement, 0.75, places=3)

    def test_get_velocity_and_displacement(self):
        # Test with a known set of velocities
        velocity_controller = MockVelocityController(numpy.array([0.1, 0.2, 0.3, 0.4, 0.5]))
        time_interval = 1
        velocity, displacement = get_velocity_and_displacement(velocity_controller, time_interval)
        self.assertEqual(velocity, 0.4)  # The last velocity value
        self.assertAlmostEqual(displacement, 0.6, places=3)  # Calculated displacement

    def test_find_optimal_frequency(self):
        velocity_controller = MockVelocityController(numpy.array([0.1, 0.2, 0.3, 0.4]))
        optimal_frequency = find_optimal_frequency(velocity_controller)
        self.assertAlmostEqual(optimal_frequency, 1, places=3)  # Calculated optimal frequency


if __name__ == "__main__":
    unittest.main()