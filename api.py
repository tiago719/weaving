import requests
from utils import base64_encode_image


class Api:
    def __init__(self, logger):
        self.logger = logger

    @property
    def proto(self):
        return 'http'
    
    @property
    def host(self):
        return '127.0.0.1'
    
    @property
    def port(self):
        return 5000
    
    @property
    def url(self):
        return f'{self.proto}://{self.host}:{self.port}'

    def ping(self):
        url = self.url + '/ping'
        try:
            response = requests.get(url)
            return response.status_code == 204
        except Exception:
            return False
        
    def surface_movement(self, velocity, displacement):
        url = self.url + '/fabric_movement'
        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                data={'velocity': velocity, 'displacement': displacement}
            )
            return response.status_code == 201
        except Exception as e:
            self.logger.error(f'An exception occurred: {e}')
        
    def pictures_batch(self, lights):
        url = self.url + '/pictures_batch'
        # encode images using base64 before sending them to the server
        for light in lights:
            light['pictures']['left']['picture'] = base64_encode_image(light['pictures']['left']['picture'])
            light['pictures']['right']['picture'] = base64_encode_image(light['pictures']['right']['picture'])

        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                data={'lights': lights}
            )
            return response.status_code == 201
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.error(f'An exception occurred: {e}')
        