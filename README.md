
Critter API
==========
This is the API back-end for the critter app. It reading from the critter_devices and critter_events tables to get
information about specific devices

## Endpoint
All functions use the common endpoint https://api.banc.io

## Device
/critter/device/{device id}

### GET
Get data about a device

#### Response:
Code | Description 
--- | --- 
200| Success
404| Not Found
500| Server Error

If found, the following data will be handed back:
```
{
    "device_id": device_id,
    "device_name": device_name,
    "last_reported": last_reported_timestamp,
    "last_reported_voltage": last_reported_voltage
}
```

## Events
/critter/device/{device id}/events

### GET
Get all events associated to a particular device

#### Response:
Code | Description
--- | ---
200| Success
404| Not Found
500| Server Error

If found, the following data will be handed back:
```
{
    "device_id": device_id,
    "events": [
        {
            "event_type": event_type
            "event_timestamp": event_timestamp
        },
    ]
}
```


## Deployment

This project uses [zappa](https://github.com/Miserlou/Zappa) to deploy.

To deploy, make sure you have the correct aws credentials on your system and do the following (on mac or linux):

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
zappa deploy prod
```

This will deploy the lambda function and API Gateway to your AWS account.