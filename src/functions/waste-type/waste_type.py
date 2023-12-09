import datetime
import json
import time
import boto3
#import paho.mqtt.client as mqtt

def get_event_date(event):
    if "timestamp" in event[0]:
        mytimestamp = datetime.datetime.fromtimestamp(event[0]["timestamp"])
    else:
        mytimestamp = datetime.datetime.fromtimestamp(time.time())
    return mytimestamp.strftime("%Y%m%d")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")

# client = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv5)
# client.on_connect = on_connect

# client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
# client.username_pw_set("cciot", "Cciot@2023")
# client.connect("186077b180d64afd9c220eddfe25bffd.s2.eu.hivemq.cloud", 8883)

def publish_result(iot_client, result):
    iot_client.publish(
        topic="Waste/Detect",
        qos=1,
        payload=str(result)
    )

def lambda_handler(event, context):
    if len(event) > 0 and "s3_image_uri" in event[0]:
        print(event)
        bucket_url = event[0]["s3_image_uri"]
        output = bucket_url.split("/", 3)
        bucket = output[2]
        photo = output[3]
        client = boto3.client("rekognition")
        iot_client = boto3.client('iot-data')

        try:
            time.sleep(5)
            response = client.detect_labels(
                Image={"S3Object": {"Bucket": bucket, "Name": photo}}, MaxLabels=10
            )
        except Exception as ex:
            print(ex)
            event[0]["sorted_waste"] = []
            event[0]["organic_waste"] = 0
            event[0]["solid_waste"] = 0
            event[0]["hazardous_waste"] = 0
            event[0]["other_waste"] = 0
            return event

        labels = response["Labels"]
        sorted_waste_items = [label["Name"] for label in labels]
        organic_waste_detected = any(label["Name"] in  ["orange", "bread", "banana", "orange peel", "apple", "onion","vegetable", "potato", "tomato", "eggplant", "aubergine", "Food", "Peel", "banana peel", "peel"] for label in labels)

        event[0]["sorted_waste"] = sorted_waste_items
        event[0]["organic_waste"] = int(organic_waste_detected)
        event[0]["solid_waste"] = int(not organic_waste_detected)
        event[0]["hazardous_waste"] = 0
        event[0]["other_waste"] = 0
        event[0]["event_date"] = get_event_date(event)

        publish_result(iot_client, 1 if organic_waste_detected else 2)
        #client.publish("Waste/Detect", str(1 if organic_waste_detected else 2), qos=1)
        print(event)
    else:
        sorted_waste_items = []
        event[0]["sorted_waste"] = sorted_waste_items
        event[0]["organic_waste"] = 0
        event[0]["solid_waste"] = 0
        event[0]["hazardous_waste"] = 0
        event[0]["other_waste"] = 0
        event[0]["event_date"] = get_event_date(event)
    return event