# Komu - Chatbot

## Introduction

This chatbot helps answer questions about information, regulations, and policies of NCC company.

## Installation and deployment:

1. Copy .env.example to .env and fill it with your api key.

2. Open a terminal. Navigate to the directory containing chatbot_service.sh.

3. Run the following command to execute chatbot_service.sh:

```bash
./chatbot_service.sh
```

Note:
Before running the above command, you may need to grant execute permission to chatbot_service.sh using the `chmod +x chatbot_service.sh` command.

4. After running chatbot_service.sh, the server will be started on port 1400 with the endpoint http://localhost:1400.

5. To check status or stop the service, you can use the sudo systemctl stop command:

Check status the service

```bash
sudo systemctl status your_service.service
```

Stop the service

```bash
sudo systemctl stop your_service.service
```
