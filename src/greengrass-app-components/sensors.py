
# SPDX-License-Identifier: MIT-0

import os
import sys
import time
from datetime import datetime
import RPi.GPIO as GPIO


from invoke import run


# Ultrasonic Sensor initialization
GPIO_TRIGGER = 17
GPIO_ECHO = 27

# Set the GPIO Mode
GPIO.setmode(GPIO.BCM)

# Set the GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)



def get_image_full_path(path: str, name: str) -> None:
    return os.path.join(path, name)


class Sensors:
    def __init__(
        self,
        location: str,
        post_code: str,
        bucket: str,
        local_garbage_path: str,
        image_name: str = "waste_image.jpg",
    ):

        # Initilize veriables
        self._sensor_deployed_location = location
        self._sensor_deployed_post_code = post_code
        self._local_path = local_garbage_path
        self._image_name = image_name
        self._bucket = bucket
        self._local_image_full_path = get_image_full_path(
            local_garbage_path, image_name
        )

        # Camera initialization
        self._clip_duration_in_msec = 1000
        self._shutter_speed_in_micro_secs = 20000


    def getUniqImageKey(self, waste_image_timestamp: float) -> None:

        key = f"waste_image_{waste_image_timestamp}.jpg"
        destination_path = os.path.join(
            self._sensor_deployed_location, self._sensor_deployed_post_code, key
        )
        print("Destination Path:",destination_path)
        return destination_path

    def build_waste_distance_stats(
        self, distance: float, waste_image_timestamp: float
    ) -> None:


        uniq_key = f"waste_image_{waste_image_timestamp}.jpg"

        destination_path = os.path.join(
            self._sensor_deployed_location, self._sensor_deployed_post_code, uniq_key
        )
        s3_uri = f"s3://{self._bucket}/{destination_path}"


        timestamp = time.time()

        event = {
            "timestamp": timestamp,
            "sensor_id": os.getenv("AWS_IOT_THING_NAME"),
            "thingname": os.getenv("AWS_IOT_THING_NAME"),
            "sensorvalue": distance,
            "s3_image_uri": s3_uri,
            "location": self._sensor_deployed_location,
            "postcode": self._sensor_deployed_post_code,
            "latitude": 51.579677,
            "longitude": -0.335836,
            "country": "Singapore",
            "city": "Singapore",
        }

        return event


    def measure_distance(self) -> None:
        # Set Trigger to HIGH
        GPIO.output(GPIO_TRIGGER, True)

        # Set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGER, False)

        StartTime = time.time()
        StopTime = time.time()

        # Save StartTime
        while GPIO.input(GPIO_ECHO) == 0:
            StartTime = time.time()

        # Save time of arrival
        while GPIO.input(GPIO_ECHO) == 1:
            StopTime = time.time()

        # Time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # Multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2
        return distance


    def trigger_camera(self, shutter_speed: int, clip_duration: int) -> None:
        filename = f"{self._local_path}/{self._image_name}"
        print("Filename:",filename)
        cmd = f"libcamera-jpeg --width 800 --height 600 --nopreview -o {filename} -t {clip_duration} --shutter {shutter_speed}"
        run(cmd, hide=True)
        # return latest camera image timestamp
        statinfo = os.stat(filename)
        return statinfo.st_mtime
