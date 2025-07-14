import json
import urllib.request
import urllib.error
import boto3
import os

ssm = boto3.client('ssm')

def lambda_handler(event, context):
    print("==== RAW EVENT ====")
    print(json.dumps(event, indent=2))

    parameter_name = os.environ.get("WEBHOOK_PARAM_NAME", "/rocketchat/webhook_url")

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        url = response['Parameter']['Value']
    except Exception as e:
        print(f"SSM fetch error: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"SSM parameter fetch error: {str(e)}"
        }

    headers = {"Content-Type": "application/json"}

    for record in event.get('Records', []):
        try:
            raw_message = record['Sns']['Message']

            # Unwrap double-encoded SNS message if needed
            try:
                sns_message = json.loads(raw_message)
                if isinstance(sns_message, str):
                    sns_message = json.loads(sns_message)
            except Exception as decode_err:
                print(f"Error decoding SNS message: {decode_err}")
                continue

            dimensions = sns_message.get('Trigger', {}).get('Dimensions', [])

            print("==== Received Dimensions ====")
            print(json.dumps(dimensions, indent=2))

            # Use lowercase keys as-is
            path = next((d['value'] for d in dimensions if d.get('name', '').lower() == 'path'), 'unknown')
            instance_id = next((d['value'] for d in dimensions if d.get('name', '').lower() == 'instanceid'), 'unknown')
            fstype = next((d['value'] for d in dimensions if d.get('name', '').lower() == 'fstype'), 'unknown')

            # Extract other fields
            alarm_name = sns_message.get('AlarmName', 'UnknownAlarm')
            new_state = sns_message.get('NewStateValue', 'UNKNOWN')
            reason = sns_message.get('NewStateReason', 'No reason provided.')

            # Compose message with full context
            message = (
                f"*Disk Alarm Triggered*\n"
                f"`{alarm_name}` is now in state: *{new_state}*\n"
                f"🔹 Volume: `{path}`\n"
                f"🔹 Instance ID: `{instance_id}`\n"
                f"🔹 Filesystem: `{fstype}`\n"
                f"🔹 Reason: {reason}"
            )

            payload = {
                "text": message
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return {
                    "statusCode": response.getcode(),
                    "body": "Rocket.Chat notified: Disk alarm"
                }

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            continue

    return {
        "statusCode": 200,
        "body": "No valid SNS records processed or all failed."
    }