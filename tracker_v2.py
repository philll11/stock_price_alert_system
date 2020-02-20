import time
import requests
import boto3

HIGHEST_BOUND = 0.45
HIGH_BOUND = 0.40
LOW_BOUND = 0.23
LOWEST_BOUND = 0.20

PHONE_NUM = '+64274556736'
BITSTAMP_API = 'https://www.bitstamp.net/api/v2/ticker/xrpusd/'

print('Creating AWS client connection.')

CLIENT = boto3.client('sns','us-east-1')

print('Calling initial API request.')
response = requests.get(BITSTAMP_API)
message_sent = False

print('Running tracker...')
while 1:
    if response.status_code == 200:
        
        response = response.json()
        asking_price = float(response['ask'])

        if asking_price < LOWEST_BOUND:
            message = "Rate is at $" + str(asking_price) + ". Lowest bound: <$" + str(LOWEST_BOUND) + " threshold breached"
            message_sent = True
        if asking_price < LOW_BOUND:
            message = "Rate is at $" + str(asking_price) + ". Low bound: <$" + str(LOW_BOUND) + " threshold breached"
            message_sent = True

        if asking_price > HIGHEST_BOUND:
            message = "Rate is at $" + str(asking_price) + ". Highest bound: >$" + str(HIGHEST_BOUND) + " threshold breached"
            message_sent = True
        if asking_price > HIGH_BOUND:
            message = "Rate is at $" + str(asking_price) + ". High bound: >$" + str(HIGH_BOUND) + " threshold breached"
            message_sent = True

        if message_sent:
            CLIENT.publish(PhoneNumber=PHONE_NUM, Message=message)
            print('Message sent. Will update in 1 hour')
            time.sleep(3600)
            message_sent = False

        time.sleep(30)
        response = requests.get(BITSTAMP_API)
    else:
        print(response.status_code)
        with open('error_log.txt', 'a') as f:            
            f.write('Error: '+str(response.status_code))
            f.write('\n')            
            f.write(response.reason)
            f.write('\n')            
            f.write(str(response.raise_for_status()))
            f.write('\n')
            f.write(response.headers['Date'])
            f.write('\n')
            f.write('#--------------------------------------------------#')
        print(response.headers['Date'])
        
        time.sleep(1800)
        print('Error received. Will update in 30 minutes\n')




