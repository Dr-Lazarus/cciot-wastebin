import os
import random
import sys
import time
from datetime import datetime

from image_stream import ImageStream
from mqtt_publisher import MqttPublisher
from sensors import Sensors


def monitor_waste_bin():
    current_distance = 0.0
    waste_image_timestamp = 0
    consecutive_measurements = 0  # Counter for consecutive measurements

    while True:
        try:
            current_distance = sensors.measure_distance()
            if current_distance <= 14.0:
                consecutive_measurements += 1
            else:
                consecutive_measurements = 0  # Reset counter if measurement is not less than 15.0

            if consecutive_measurements >= 3:
                # Take waste photo
                waste_image_timestamp = sensors.trigger_camera(
                    sensors._shutter_speed_in_micro_secs, sensors._clip_duration_in_msec
                )
                event = sensors.build_waste_distance_stats(
                    current_distance, waste_image_timestamp
                )

                # Push waste image first to cloud in readiness for waste sorting analysis
                destination_path = sensors.getUniqImageKey(waste_image_timestamp)
                uploader.upload(destination_path, sensors._local_image_full_path)
                print(f"Published Image to: {destination_path}")

                # Publish waste distance data to IoT core
                publisher.publish(event)
                print(f"Published distance data : {event}")

                # Reset the counter after capturing the image
                consecutive_measurements = 0
                time.sleep(30)  # To ensure that images are not captured constantly and only once every 30 seconds

        except Exception as e:
            # Catch I/O exception to ignore and continue
            print(e)
            continue


def main() -> None:
    try:
        monitor_waste_bin()
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    try:

        # Initialize Sensors
        temp_local_image_path = os.getcwd()
        cloud_bucket_name = os.getenv("TRASH_BUCKET")
        image_name = "waste_image.jpg"
        location = "Greenhill"
        post_code = "HA11AA"

        sensors = Sensors(
            location, post_code, cloud_bucket_name, temp_local_image_path, image_name
        )

        # Initialize Stream manager client
        local_stream_name = "ab3-image-upload"
        uploader = ImageStream(local_stream_name, cloud_bucket_name)

        # Initialize MQTT client
        mqtt_topic = "smart/trash_bin"
        publisher = MqttPublisher(mqtt_topic)

        # Start sensor reading app
        main()
    except Exception as ex:
        print(ex)
        raise
