# /usr/bin/env python

''' To run this app, run the following two commands in a respective cmd prompt '''
# twilio phone-numbers:update "+13202811005" --sms-url="http://localhost:5000/sms"
# python3 run.py


from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    """Respond to incoming messages with a friendly SMS."""
    # Start our response
    resp = MessagingResponse()

    print(resp.value())

    # Add a message
    resp.message("Ahoy! Thanks so much for your message.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
