#!/bin/bash
python3 -m venv venv

source venv/bin/activate

pip3 install -r requirements.txt

current_directory=$(pwd)
echo "[Unit]" > chatbot.service
echo "Description= Chatbot Komu Service" >> chatbot.service
echo "[Service]" >> chatbot.service
echo "User=root" >> chatbot.service
echo "EnvironmentFile=$current_directory/.env" >> chatbot.service
echo "WorkingDirectory=$current_directory" >> chatbot.service
echo "ExecStart=$current_directory/venv/bin/uvicorn main:app --host 0.0.0.0 --port 1400 --workers 4" >> chatbot.service
echo "Restart=always" >> chatbot.service
echo "RestartSec=3" >> chatbot.service
echo "[Install]" >> chatbot.service
echo "WantedBy=multi-user.target" >> chatbot.service

sudo cp chatbot.service /etc/systemd/system/

# Reload the service files to include the new service
sudo systemctl daemon-reload

# Start your service
sudo systemctl start chatbot.service

# To enable your service on every reboot
sudo systemctl enable chatbot.service