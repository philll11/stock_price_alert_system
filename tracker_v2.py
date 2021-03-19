#!/usr/bin/env python3

import time
import requests
import boto3
import yaml
import logging
import sys
import coloredlogs
import yfinance as yf
from slack import WebClient
from slack.errors import SlackApiError
import argparse

class StockTracker:
    def __init__(self, configFile="config.yml"): 
        self.config = dict()
        self.stocks = dict()
        self.LOG = self.setupLog()
        self.LOG_LEVELS =  {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
        self.slackAlerts = list()
        self.snsAlerts = list()
        self.setupConfig(configFile)
        self.LOG.debug("app config: " + str(self.config))

    def askYahoo(self, symbol):
        """ 
        Asks google what price the symbol is at
        @param symbol string of stock symbol
        @return float decimal value of stock price
        """
        ticker = yf.Ticker(symbol.upper())
        self.LOG.info("Current price of " + str(symbol) + " is: " + str(ticker.info['regularMarketPrice']) )
        #self.LOG.debug(ticker)
        return ticker.info['regularMarketPrice']

    def askBitstamp(self, symbol): 
        """ 
        Asks bitstamp what price the symbol is at
        @param symbol string of stock symbol
        @return float decimal value of stock price
        """
        BITSTAMP_API = 'https://www.bitstamp.net/api/v2/ticker/' + symbol.lower() + '/'
        self.LOG.info('Calling BitStamp API for ' + str(symbol.lower()))
        try:
            response = requests.get(BITSTAMP_API)
            response = response.json()
            asking_price = float(response['ask'])
        except requests.RequestException as e:
            self.LOG.error("Exception calling Bitstamp: " + str(e))
        self.LOG.info("Current price of " + str(symbol) + " is: " + str(asking_price) )
        return asking_price

    def getStockPrice(self, symbol):
        """ 
        Function to call Bitstamp or Yahoo and get return current stock price 
        @param symbol string of stock symbol
        @return the current stock price
        """
        lookupType = self.stocks[symbol]['Type']
        if lookupType == "yahoo":
            return self.askYahoo(symbol)
        elif lookupType == "bitstamp":
            return self.askBitstamp(symbol)
        else:
            self.LOG.critical("Symbol " + str(symbol) + " has no defined stock type!")
            return 0.00
    

    def sendSNSAlert(self, msg):
        client = boto3.client('sns','us-east-1')
        if self.snsAlerts != None:
            for PHONE_NUM in self.snsAlerts:
                self.LOG.info('Sending SNS Alert to ' + str(PHONE_NUM))
                client.publish(PhoneNumber=PHONE_NUM, Message=msg)

    def sendSlackAlert(self, msg):
        for alert in self.slackAlerts:
            self.LOG.info("Sending slack alert to: " + str(alert['Endpoint']))
            slackClient = WebClient(token=alert['BotToken'])
            endpoint = alert['Endpoint']       
            try:
                response = slackClient.chat_postMessage(channel=endpoint,text=msg)
            except SlackApiError as e:
                self.LOG.error("Slack API Error: " + str(e))
                

    def setupLog(self, logLevel=logging.DEBUG): # TBC Change default to INFO
        """ 
        Sets up logging.
        @param level The logger level you wish to set, DEBUG by default
        @return The logging object you need to log stuffs
        """        
        log = logging.getLogger(__name__)
        log.setLevel(logLevel) 
        ch = logging.StreamHandler()
        ch.setLevel(logLevel)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        fh = logging.FileHandler("stockTracker.log")
        fh.setLevel(logLevel)
        log.addHandler(ch)
        log.addHandler(fh)
        coloredlogs.install(level=logLevel, logger=log)
        return log

    def setupConfig(self, fileName="config.yml"):
        
        with open(fileName, 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)['stockTracker']
            except yaml.YAMLError as ex:
                self.LOG.error("Error loading config file.  YAML may be improperly formatted: " + str(ex))
            except IOError as ex:
                self.LOG.error("Error loading config file.  File may not exist. " + str(ex)) 
 
        appConfig = self.config['ApplicationConfig']
        self.slackAlerts = list() # [ { 'webhookURL': '', 'endpoint': ''  }, ... ]
        self.snsAlerts = list() # [ phoneNumber, phoneNumber, ... ]
        for configObject in appConfig:
            self.LOG.debug("config object: " + str(configObject))
            if configObject == "SlackAlert":
                self.LOG.info("Loading Slack Alerts")
                self.slackAlerts = appConfig[configObject]
                self.LOG.debug("slack alerts loaded: " + str(self.slackAlerts))

            elif configObject == "SNSAlert":
                self.LOG.info("Loading SNS Alerts")    
                self.snsAlerts = appConfig[configObject]
                self.LOG.debug("sns alerts loaded: " + str(self.snsAlerts))
                
            elif configObject == "LogLevel":
                self.LOG.info("Setting log level from config file")
                newLogLevel = appConfig[configObject].lower()
                newLogLevel = self.LOG_LEVELS[newLogLevel]
                self.LOG.setLevel( newLogLevel )
                
            else:
                print("Skipping an invalid configuration node in ApplicationConfig object")

        for configObject in self.config:
            if configObject != 'ApplicationConfig':
                
                
                self.stocks[configObject] = self.config[configObject]
                
    def sleep(self, seconds):
        self.LOG.info("Sleeping for " + str(seconds) + " seconds")
        time.sleep(seconds)

        
    def start(self):
        self.LOG.debug(self.stocks)
        for symbol in self.stocks:
            self.LOG.info("Querying for Symbol: " + symbol)
            asking_price = self.getStockPrice( symbol )
            alarm = False # Do we need to send an Alert?
            self.LOG.debug(self.stocks[symbol])
            if self.stocks[symbol]['Lowest'] and asking_price < self.stocks[symbol]['Lowest']:
                message = "(" + symbol + ") Rate is at $" + str(float(asking_price)) + ". Lowest bound: <$" + str(self.stocks[symbol]['Lowest']) + " threshold breached"
                alarm = True
            if self.stocks[symbol]['Low'] and asking_price < self.stocks[symbol]['Low']:
                message = "(" + symbol + ") Rate is at $" + str(float(asking_price)) + ". Low bound: <$" + str(self.stocks[symbol]['Low']) + " threshold breached"
                alarm = True
            if self.stocks[symbol]['Highest'] and asking_price > self.stocks[symbol]['Highest']:
                message = "(" + symbol + ") Rate is at $" + str(float(asking_price)) + ". Highest bound: >$" + str(self.stocks[symbol]['Highest']) + " threshold breached"
                alarm = True
            if self.stocks[symbol]['High'] and asking_price > self.stocks[symbol]['High']:
                message = "(" + symbol + ") Rate is at $" + str(float(asking_price)) + ". High bound: >$" + str(self.stocks[symbol]['High']) + " threshold breached"
                alarm = True
                
            if alarm:
                self.sendSNSAlert( message )
                self.sendSlackAlert( message )
                self.LOG.warning( message )

def main():
    parser = argparse.ArgumentParser(description="Tracks stock prices!")
    parser.add_argument('--config', help="defines an alertnate configuration file.  Default is config.yml", type=str)
    parser.add_argument('--sleep', help="amount of seconds to sleep between loops, if `--loop` is enabled.", type=int)
    parser.add_argument('--loop', help="causes the program to stay in an infinite loop.  requires a `--sleep` parameter", action="store_true")
    
    args = parser.parse_args()

    if args.config:
        thisConfig = args.config
    else:
        thisConfig = "config.yml"

    if args.loop == True:
        thisLoop = True
    else:
        thisLoop = False
    

    if args.sleep:
        thisSleep = args.sleep
    else:
        thisSleep = 0
        
    st = StockTracker(thisConfig)
    #log = st.setupLog()

    if thisLoop:
        while True:
            st.start()
            st.sleep(thisSleep)
        
    else:
        st.start()        
if __name__ == "__main__":
    main()

