import time
import logging
import threading
import numpy
from hardware_controllers.velocity_sensor_controller import VelocitySensorController
from hardware_controllers.cameras_controller import CamerasController
from hardware_controllers.cameras_controller.enumerators.light_type import LightType
from hardware_controllers.cameras_controller.errors import PictureNotReadyError
from api import Api
from utils import datetime_now


# Constants and Configuration
TRIGGER_INTERVAL = 1
# how many samples per second do we want to get
VELOCITY_SAMPLES_PER_SECOND = 66
TIME_INTERVAL = 1 / VELOCITY_SAMPLES_PER_SECOND
# data measures decimal places
DECIMAL_PLACES = 3
# cameras vertical view field
CAMERAS_VERTICAL_VIEW_FIELD = 25
# minimun camera frequency iterations
MINIMUN_CAMERA_FREQUENCY = 0.001

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Logging has been configured with the desired settings.")

# Wait for the API to become available
api = Api(logger)
while True:
    if api.ping():
        logger.info("API is available.")
        break
    else:
        logger.info("API is not yet available. Waiting for 5 seconds...")
        time.sleep(5)


def get_velocity_and_displacement(velocity_controller, time_interval):
    """
    Measure velocity and calculate displacement over a specific time interval.

    Args:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.
        time_interval (float): The time interval (in seconds) over which to measure velocity and calculate displacement.

    This function measures surface velocity, filters the data with a moving average to reduce noise, and calculates the
    displacement based on the velocity measurements.

    Parameters:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.
        time_interval (float): The time interval for measurement in seconds.

    Returns:
        tuple: A tuple containing velocity and displacement, both as floating-point values.

    """

    samples_number = time_interval * VELOCITY_SAMPLES_PER_SECOND
    # gather velocity values
    velocity_samples = []
    while len(velocity_samples) < samples_number:
        velocity_sample = velocity_controller.get_velocity()
        if velocity_sample is None:
            # TODO: velocity_sample should never be None
            break
        velocity_samples.append(velocity_sample)
        time.sleep(1 / VELOCITY_SAMPLES_PER_SECOND)

    # address noise with moving average
    filtered_velocity = moving_average(velocity_samples, window_size=3)
    # assume the last value in filtered_velocity is our velocity measure.
    # we want to send to the server the most recent velocity value 
    velocity_measure = round(filtered_velocity[-1], DECIMAL_PLACES)
    # calculate displacement
    displacement = calculate_displacement(filtered_velocity, time_interval)
    return velocity_measure, displacement
    

# Velocity measurement
def measure_velocity(velocity_controller):
    """
    Measure surface velocity and displacement over time.

    Args:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.

    This function continuously measures the surface velocity and displacement, logs the results, and sends the data to
    the server. It uses the provided velocity controller to collect data and continuously logs and sends updates.

    Parameters:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.
    """

    logger.info(f"Starting to measure velocity. Each measure will use {VELOCITY_SAMPLES_PER_SECOND} samples.")

    try:
        while True:  # TODO: define exit condition
            velocity, displacement = get_velocity_and_displacement(velocity_controller, 1)

            logger.info(f"Measured Velocity value: {velocity} Displacement value: {displacement}. Sending data to the server...")

            api.surface_movement(velocity, displacement)
    except Exception as e:
        logger.error(f'An exception occurred: {e}')
        

def moving_average(data, window_size):
    """
    Calculate the moving average of a data sequence.

    Args:
        data (list or numpy.ndarray): The input data sequence.
        window_size (int): The size of the moving average window.

    Returns:
        numpy.ndarray: An array containing the moving average values.

    This function calculates the moving average of a data sequence using a specified window size. The moving average
    smoothes the data by averaging values within a window of the specified size.

    If the input data sequence has fewer elements than the window size, the original data is returned, as there are
    insufficient data points to calculate the moving average.

    The function uses NumPy for efficient computation.
    """
    
    if len(data) < window_size:
        # Not enough data points to calculate the moving average.
        return data
    
    # Use NumPy to efficiently calculate the moving average.
    return numpy.convolve(data, numpy.ones(window_size) / window_size, mode='valid')


def calculate_displacement(velocity_data, time_interval):
    """
    Calculate the displacement of the surface based on velocity data.

    Args:
        velocity_data (list): A list of velocity measurements over time.
        time_interval (float): The time interval between velocity measurements.

    Returns:
        float: The calculated surface displacement.

    Raises:
        ValueError: If the input data is insufficient to perform the calculation.

    The displacement is computed using the trapezoidal rule, which estimates the area under the velocity curve.

    The function takes a list of velocity measurements over time and a time interval between measurements. It iterates
    through the velocity data, calculating the displacement increment for each pair of consecutive data points and
    summing them to obtain the total displacement.

    The result is rounded to the specified number of decimal places (DECIMAL_PLACES).

    If there are insufficient data points to calculate displacement, a ValueError is raised.

    Note: Make sure to set the DECIMAL_PLACES constant to the desired number of decimal places for rounding.
    """

    if len(velocity_data) < 2:
        raise ValueError("Insufficient data to calculate displacement.")

    displacement = 0
    for i in range(1, len(velocity_data)):
        displacement += 0.5 * (velocity_data[i - 1] + velocity_data[i]) * time_interval
    return round(displacement, DECIMAL_PLACES)


def find_optimal_frequency(velocity_controller):
    """
    Find the optimal triggering frequency for camera iterations.

    Args:
        velocity_controller (VelocitySensorController): An instance of the VelocitySensorController.

    Returns:
        float: The optimal triggering frequency in seconds.

    The function iterates to find the optimal triggering frequency for camera iterations based on displacement measurements.
    It starts with a default frequency of 1 second and progressively adjusts it to minimize displacement.

    If the calculated displacement falls within the acceptable range (CAMERAS_VERTICAL_VIEW_FIELD), the optimal frequency
    is found and returned.

    The frequency is adjusted by decreasing it by a fixed step (0.05 seconds by default) in each iteration.
    """

    frequency = 1  # start at 1 second

    while True:
        _, displacement = get_velocity_and_displacement(velocity_controller, frequency)
        # check if displacement is within the camera range
        if displacement <= CAMERAS_VERTICAL_VIEW_FIELD:
            return round(frequency, DECIMAL_PLACES)  # Found the optimal frequency
        
        # if displacement is not within the acceptable range, adjust the frequency
        frequency -= 0.05  # we can adjust the step size as needed

        # add a condition to prevent going below a minimum frequency
        if frequency < MINIMUN_CAMERA_FREQUENCY:
            return MINIMUN_CAMERA_FREQUENCY


def capture_images(velocity_controller):
    """
    Capture images from cameras, calculate relevant data, and send the data to the server.

    Args:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.

    This function captures images from cameras, calculates relevant data, including velocity and displacement,
    and sends the data to the server.

    Parameters:
        velocity_controller (VelocitySensorController): The controller for measuring surface velocity.
    """

    logger.info('Find the optimal triggering frequency for camera iterations.')
    frequency = find_optimal_frequency(velocity_controller)
    logger.info(f'Optimal triggering frequency of {frequency} seconds for camera iterations.')

    # Initialize the cameras controller
    cameras_controller = CamerasController()
    cameras_controller.open_cameras()

    last_capture_time = time.time()

    threads = []

    while True:  # TODO: define exit condition
        def get_light(light_type, camera_data, last_capture_time):
            velocity = velocity_controller.get_velocity()
            current_time = time.time()
            time_elapsed = current_time - last_capture_time
            last_capture_time = current_time
            displacement = (velocity * time_elapsed)
            return {
                'light': light_type,
                'creation_date': datetime_now(),
                'surface_velocity': velocity,
                'surface_displacement': displacement,
                'pictures': {
                    'left': {
                        'picture': camera_data[0],
                        'iso': camera_data[3],
                        'exposure_time': camera_data[1],
                        'diaphragm_opening': camera_data[2]
                    },
                    'right': {
                        'picture': camera_data[4],
                        'iso': camera_data[7],
                        'exposure_time': camera_data[5],
                        'diaphragm_opening': camera_data[6]
                    }
                }
            }
    
        try:
            lights = []
            # Capture images
            for light_type in [LightType.GREEN, LightType.BLUE]:
                cameras_controller.trigger()
                camera_data = cameras_controller.collect_pictures(light_type)
                lights.append(get_light(light_type, camera_data, last_capture_time))

            # use a separate thread to send data to the server, let's not block this one
            logger.info(f'Sendigs lights data to the server.')
            images_thread = threading.Thread(target=api.pictures_batch, args=(lights, ))
            images_thread.start()
            threads.append(images_thread)
        except PictureNotReadyError:
            logger.warning(f'Havent found images for all light types. Trying again in {frequency} seconds')
        finally:
            time.sleep(frequency)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    logger.info("Script execution started.")
    # Initialize the velocity controller
    velocity_controller = VelocitySensorController()
    velocity_controller.start_sensor()

    try:
        # Create and start threads
        velocity_thread = threading.Thread(target=measure_velocity, args=(velocity_controller, ))
        images_thread = threading.Thread(target=capture_images, args=(velocity_controller, ))

        velocity_thread.start()
        images_thread.start()

        # Wait for threads to complete
        velocity_thread.join()
        images_thread.join()
    except Exception as e:
        logger.error(f'An exception occurred: {e}')
    finally:
        logger.info("Script execution completed. Cleaning up the resources")
        velocity_controller.stop_sensor()
