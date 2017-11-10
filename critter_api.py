from api_version import version as api_version
import time
import json
import boto3
from boto3.dynamodb.conditions import Key
import requests

from flask import Flask, request, session, g, url_for, Response, request, jsonify

particle_api_url = 'https://api.particle.io'

# create our app
app = Flask(__name__)

# enable CORS on everything
from flask_cors import CORS
CORS(app)

# helper function to get the current time in millis()
current_milli_time = lambda: int(round(time.time() * 1000))

#functions to manage database connections
app.config.update(dict(
    TABLE_NAME='baby_pool'
))

#default return type to JSON, since this is really what we use
class JSONResponse(Response):
    default_mimetype = 'application/json'

# will return 400 when called
@app.errorhandler(400)
def bad_request(error=None):
        """
        Handle 400 cases
        :param error: String, the error to return
        :return:
        """
        message = {
            'status': 400,
            'error': 'BadRequest: ' + request.url,
            "message": error if error is not None else '',
        }
        resp = jsonify(message)
        resp.status_code = 400

        return resp

# will return 404 when called
@app.errorhandler(404)
def not_found(error=None):
        """
        Handle 404 cases
        :param error: String, the error to return
        :return:
        """
        message = {
            'status': 404,
            'error': 'NotFound: ' + request.url,
            "message": error if error is not None else '',
        }
        resp = jsonify(message)
        resp.status_code = 404

        return resp

# will return 500 when called
@app.errorhandler(500)
def internal_error(error=None):
        """
        Handle 500 cases
        :param error: String, the error to return
        :return:
        """
        message = {
            'status': 500,
            'error': 'ServerError: ' + request.url,
            "message": error if error is not None else '',
        }
        resp = jsonify(message)
        resp.status_code = 500

        return resp

# Routes
# ------------------------------------------------------------------------------
@app.route('/critter/version')
def version():
    return json.dumps({'version': api_version})

@app.route('/critter/devices')
def devices():
    try:
        params = get_payload(request)
        token = params['token']
    except Exception as ex:
        return bad_request()

    try:
        devices = []
        response = requests.get(particle_api_url+'/v1/devices?access_token='+token)
        for particle_device in response.json():

            # it must be named properly or there is no point in continuing
            if not particle_device['name'].startswith("critter"):
                continue

            # get the device from the dynamo table
            dynamodb = boto3.resource('dynamodb')
            events_table = dynamodb.Table("critter_devices")
            record = events_table.get_item(Key={"device_id": particle_device['id']})

            # if not found, continue
            if "Item" not in record:
                continue

            # otherwise, add it to the list
            device = record["Item"]
            if 'last_reported_voltage' in device:
                device['last_reported_voltage'] = float(device['last_reported_voltage'])

            device['online'] = particle_device['connected']
            devices.append(device)

        return JSONResponse(json.dumps(devices))
    except Exception as ex:
        return internal_error(ex.message)

@app.route('/critter/device/<string:device_id>')
def device(device_id):
    try:
        # get the device from the dynamo table
        dynamodb = boto3.resource('dynamodb')
        events_table = dynamodb.Table("critter_devices")
        record = events_table.get_item(Key={"device_id": device_id})

        # if not found, return a 404
        if "Item" not in record:
            return not_found("device does not exist")

        # otherwise, convert it and send it out the door
        device = record["Item"]
        if 'last_reported_voltage' in device:
            device['last_reported_voltage'] = float(device['last_reported_voltage'])

        return JSONResponse(json.dumps(device))
    except Exception as ex:
        return internal_error(ex.message)

@app.route('/critter/device/<string:device_id>/events')
def device_events(device_id):
    try:
        # get the device from the dynamo table
        dynamodb = boto3.resource('dynamodb')
        events_table = dynamodb.Table("critter_events")
        record = events_table.query(KeyConditionExpression=Key('device_id').eq(device_id))

        # if not found, return a 404
        if "Items" not in record or len(record["Items"]) == 0:
            return not_found("device does not exist")

        # otherwise, construct the response and send it
        response = {"device_id": device_id, "events": []}
        for event in record['Items']:
            response["events"].append({"event_type": event["event_type"], "event_timestamp": event["timestamp"]})

        return JSONResponse(json.dumps(response))
    except Exception as ex:
        return internal_error(ex.message)

# Helper functions
# ------------------------------------------------------------------------------
def get_payload(request):

    if request.method == 'POST':
        # if POST, the data may be in the data array as json or form, depending on how it was handed in
        # Postman seems to hand it in as json while others seem to hand it in through form data
        data = request.get_json(force=True, silent=True)
        return data if data is not None else request.form
    else:
        return request.args

def sort_responses(items):
    return sorted(items, key=lambda item: item['submitted_int']['N'], reverse=True)

def convert_scan_responses(items):
    parsed_items = []
    for item in items:
        parsed_items.append(convert_scan_response(item))

    return parsed_items

def convert_scan_response(item):
    obj = {}
    for key in item.keys():
        obj[key] = item[key][item[key].keys()[0]]
    return obj



# Main
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run()