#!bin/bash

sudo ln -sf $HOME/acoupi/src/acoupi/services/heartbeat.service /usr/lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable heartbeat.service
sudo systemctl start heartbeat.service
systemctl status heartbeat.service
