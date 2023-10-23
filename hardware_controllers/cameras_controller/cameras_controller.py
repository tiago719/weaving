"""
CamerasController is a fake controller to take pictures of fabric (or maybe some cute pets).
"""

import numpy as np
from PIL import Image
from time import sleep
from random import choice, uniform as random_uniform
from typing import List, Tuple
from pathlib import Path
from threading import Event, Lock

from . import LightType, CameraPosition
from .errors import PictureNotReadyError, PictureNotFoundError, CamerasNotReadyError

ONE_SECOND = 1


class CamerasController:
    """
    CamerasController simulates a camera set of cameras sensors using pets pictures.

    This class provides methods to trigger the cameras to capture the pictures, as well to collect them.

    Attributes
    ----------
    _trigger : Event
        Trigger event to inform if a trigger was triggered and not consumed.
    _trigger_lock : Lock
        Trigger event lock to guarantee that the trigger is thread safe.
    _DIAPHRAGM_OPENINGS : List[float]
        Possible diaphragm opening of these cameras' sensors.
    _ISOS : List[int]
        Possible ISO values of these cameras' sensors.
    _EXPOSITION_TIME_LOWER_LIMIT: float
        Minimum exposure time of these cameras' sensors.
    _EXPOSITION_TIME_UPPER_LIMIT: float
        Maximum exposure time of these cameras' sensors.

    Methods
    -------
    trigger()
        Trigger the cameras to capture the pictures.
    collect_pictures()
        Collect the pictures obtained with the trigger.
    _get_pictures()
        Gets the dataclass with the wanted pictures.
    _get_picture()
        Gets the dataclass with the wanted picture - only one camera.
    _create_picture_filepath()
        Creates the picture filepath using the light type and camera position information's.
    """

    _DIAPHRAGM_OPENINGS: List[float] = [2.8, 5, 5.6, 8, 11]
    _ISOS: List[int] = [50, 100, 200, 400, 800, 1600]
    _EXPOSITION_TIME_LOWER_LIMIT: float = 0.00125 * ONE_SECOND
    _EXPOSITION_TIME_UPPER_LIMIT: float = 2 * ONE_SECOND
    _CAPTURING_PICTURES_BASE_SLEEP_TIME: int = 4 * ONE_SECOND

    def __init__(self) -> None:
        self._cameras_ready = False
        self._cameras_ready_lock = Lock()
        self._trigger = Event()
        self._trigger_lock = Lock()

    def open_cameras(self) -> None:
        """
        Prepares de cameras to be ready to use.

        Returns
        -------
        NoneThi
        """

        with self._cameras_ready_lock:
            self._cameras_ready = True

    def _raise_on_cameras_not_ready(self) -> None:
        """
        Method that raises CamerasNotReadyError exception when cameras are not ready.

        Raises
        ------
        CamerasNotReadyError
            When cameras are not ready to be used.

        Returns
        -------
        None
        """

        with self._cameras_ready_lock:
            if not self._cameras_ready:
                raise CamerasNotReadyError('Cannot trigger cameras that are not ready to be used')

    def trigger(self) -> bool:
        """
        Trigger the cameras shutter to capture the pictures.

        Notes
        -----
        The trigger is a consumable, which means that to perform a second trigger, the pictures need to be collected.

        Raises
        ------
        CamerasNotReadyError
            When cameras are not ready to be used.

        Returns
        -------
        bool
            True if the trigger was performed successfully, False if the previous trigger was not yet cleaned.
        """

        self._raise_on_cameras_not_ready()

        with self._trigger_lock:
            if self._trigger.is_set():
                return False

            self._trigger.set()
            return True

    def collect_pictures(self,
                         light_type: LightType) -> Tuple[np.ndarray, float, float, int, np.ndarray, float, float, int]:
        """
        Collect pictures of all the cameras and return them.

        Notes
        -----
        Output order:
            (left_picture, left_picture_exposition_time, left_picture_diaphragm_opening, left_picture_iso_value,
             right_picture, right_picture_exposition_time, right_picture_diaphragm_opening, right_picture_iso_value)

        Parameters
        ----------
        light_type : LightType
            The light type that the client want to use.

        Raises
        ------
        PictureNotReadyError
            When cameras don't have any ready picture to return.
        CamerasNotReadyError
            When cameras are not ready to be used.

        Returns
        -------
        Tuple[np.ndarray, float, float, int, np.ndarray, float, float, int]
            Pictures and their metadata.
        """

        self._raise_on_cameras_not_ready()

        with self._trigger_lock:
            if not self._trigger.is_set():
                raise PictureNotReadyError('The trigger was not set!')

            pictures = self._get_pictures(light_type)
            sleep(self._calculate_capturing_sleep_time())
            self._trigger.clear()

            return pictures

    @staticmethod
    def _calculate_capturing_sleep_time() -> float:
        """
        Calculate a capturing sleep time to add some uncertainty to capture the pictures.

        Returns
        -------
        float
            Time to capture a picture.
        """

        dispersion_factor = 1
        sleep_uncertainty = random_uniform(-1, 1) * dispersion_factor
        effective_sleep_time = CamerasController._CAPTURING_PICTURES_BASE_SLEEP_TIME + sleep_uncertainty

        return effective_sleep_time

    def _get_pictures(self,
                      light_type: LightType) -> Tuple[np.ndarray, float, float, int, np.ndarray, float, float, int]:
        """
        Gets the dataclass with the wanted pictures.

        Parameters
        ----------
        light_type : LightType
            The light type that the client want to use.

        Returns
        -------
        Tuple[np.ndarray, float, float, int, np.ndarray, float, float, int]
            Pictures and their metadata.
        """

        left_picture = self._get_picture(light_type, CameraPosition.LEFT)
        right_picture = self._get_picture(light_type, CameraPosition.RIGHT)
        pictures = left_picture + right_picture

        return pictures

    def _get_picture(self, light_type: LightType,
                     camera_position: CameraPosition) -> Tuple[np.ndarray, float, float, int]:
        """
        Gets the dataclass with the wanted picture - only one camera.

        Parameters
        ----------
        light_type : LightType
            The light type that the client want to use.
        camera_position : CameraPosition
            The selected camera position of this picture.

        Returns
        -------
        Tuple[np.ndarray, float, float, int]
            Pictures and its metadata.
        """

        filepath = self._create_picture_filepath(light_type, camera_position)
        iso_value = choice(CamerasController._ISOS)
        diaphragm_opening = choice(CamerasController._DIAPHRAGM_OPENINGS)
        exposition_time = random_uniform(CamerasController._EXPOSITION_TIME_LOWER_LIMIT,
                                         CamerasController._EXPOSITION_TIME_UPPER_LIMIT)
        exposition_time = round(exposition_time, 2)
        decoded_picture = np.array(Image.open(filepath))

        return decoded_picture, exposition_time, diaphragm_opening, iso_value

    @staticmethod
    def _create_picture_filepath(light_type: LightType, camera_position: CameraPosition) -> Path:
        """
        Creates the picture filepath using the light type and camera position information's.

        Parameters
        ----------
        light_type : LightType
            The light type that the client want to use.
        camera_position : CameraPosition
            The selected camera position of this picture.

        Raises
        ------
        PictureNotFoundError
            When the picture was not found in the expected directory.

        Returns
        -------
        Path
            The filepath of the selected picture.
        """

        filename = f'{camera_position.value}_picture_{light_type.value}.jpg'
        filepath = Path(__file__).parent.resolve().joinpath('pictures').joinpath(filename)

        if not filepath.is_file():
            raise PictureNotFoundError(f'The picture was not found with the expected filepath {filepath}')

        return filepath
