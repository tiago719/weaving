# Surface Movement Measurement System

This repository contains Python code for a surface movement measurement system. The system is designed to measure the surface velocity and displacement of a moving object, capture images using cameras, and send data to a server. The code is intended for use with specific hardware controllers and sensors.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Functionality](#functionality)
- [Running Tests](#running-tests)

## Prerequisites

Before using this code, ensure that you have the following prerequisites in place:

- Python 3.7 or later
- The necessary hardware components, including velocity sensors and cameras - they are in the repository
- A running server with an API to receive and process data from this system
- Python libraries and packages mentioned in the code (you can find all of them in requirements.txt)

## Installation

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/your-username/surface-movement-system.git
   cd surface-movement-system
   ```

2. Install the required Python libraries. You can use pip for this:

    ```
    pip install -r requirements.txt
## Usage
To use the system, follow these steps:

1. Run the main script main.py. This script initializes the velocity sensor, starts measuring surface velocity, and captures images.

    ```
    python main.py
2. The system will continuously measure surface velocity and displacement, log the results, and send the data to the server via the configured API.

3. Images are captured using cameras and relevant data is collected. This data, including surface velocity, displacement, and image details, is sent to the server.

4. The system will keep running unless you define an exit condition in the code.

## Functionality
This code offers the following functionalities:

- Velocity Measurement: The system continuously measures surface velocity, applies a moving average filter to reduce noise, and calculates displacement based on velocity measurements.
- Camera Image Capture: Images are captured using cameras. The code specifies an optimal frequency for camera iterations to minimize displacement.
- Data Transmission: Data, including surface velocity, displacement, and image details, is sent to the server via the API.
- Threading: The code uses multithreading to efficiently perform velocity measurements, image capture, and data transmission.

## Running Tests

To ensure the correctness of the Surface Movement System, you can run a suite of tests that validate the functionality of the code. We use the `unittest` framework to write and run these tests.

1. Open a terminal or command prompt.

2. Navigate to the directory containing your Surface Movement System code.

3. Run the following command to execute the tests:

   ```bash
   python -m unittest discover