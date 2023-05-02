#!/bin/sh

#Install Mongo db server  
apt-get install mongodb -y
systemctl start mongod # Start mongo db server 
systemctl enable mongod # enable mongo db service

pip3 install pymongo # Install Mongo db driver
pip3 install pytz
