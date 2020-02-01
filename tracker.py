import requests
from bs4 import BeautifulSoup
import boto3

url = "https://www.coingecko.com/en/coins/ripple"

my_number = '+64274556736'

higher_bound = 0.48
highest_bound = 0.50
lower_bound = 0.32
lowest_bound = 0.29

message_sent = False

client = boto3.client('sns', 'us-east-1')

while not message_sent:
    response = requests.get(url)
    if response.status_code == 200:
        print('Response 200')

        
        page = BeautifulSoup(response.content, "html.parser")
        span = page.find(name="span", attrs={"class":"no-wrap"})
        xrp_rate = float(span.text.split('$')[1])

        message_sent = False

        if xrp_rate < lowest_bound:
            message = "Rate is at $" + str(xrp_rate) + ". Lowest bound: <$" + lowest_bound + " threshold breached"
            message_sent = True
        if xrp_rate < lower_bound:
            message = "Rate is at $" + str(xrp_rate) + ". Lowser bound: <$" + lower_bound + " threshold breached"
            message_sent = True
        
        if xrp_rate > highest_bound:
            message = "Rate is at $" + str(xrp_rate) + ". Highest bound: >$" + highest_bound + " threshold breached"
            message_sent = True            
        if xrp_rate > higher_bound:
            message = "Rate is at $" + str(xrp_rate) + ". Higher bound: >$" + higher_bound + " threshold breached"
            message_sent = True

        if message_sent:
            client.publish(PhoneNumber=my_number, Message=message)
        message_sent = True
    else:
        print("Status code " + response.status_code)
        break;

