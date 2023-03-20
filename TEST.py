# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
# Twilio credentials
TWILIO_ACCOUNT_SID = 'AC3d04ca0450dbaa53d8584db2b1c3086c'
TWILIO_AUTH_TOKEN = '74f78a9eba3f7b9a25f063bde6a413e3'
TWILIO_PHONE_NUMBER = '+15076973994'
# TWILIO_PHONE_NUMBER = '+15005550006'

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

message = client.messages.create(
                              body='Hi there',
                              from_='+15076973994',
                              to='+1604 445 9123'
                          )

print(message.sid)