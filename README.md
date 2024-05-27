# Komu - Chatbot

## Introduction

This chatbot helps answer questions about information, regulations, and policies of NCC company.

## Installation and deployment:

1. Copy .env.example to .env and fill it with your api key.

2. Open a terminal. Navigate to the directory containing chatbot_service.sh.

3. Run the following command to execute chatbot_service.sh:

```bash
./chatbot_service.sh -p 1500 -host 0.0.0.0
```

-p and -host are optional parameters to set up the port and server for the application. If not provided, the default port is 1500 and the default host is 0.0.0.0.

Note:
Before running the above command, you may need to grant execute permission to chatbot_service.sh using the `chmod +x chatbot_service.sh` command.

4. After running chatbot_service.sh, the server will be started.

5. To check status or stop the service, you can use the sudo systemctl stop command:

Check status the service

```bash
sudo systemctl status chatbot.service
```

Stop the service

```bash
sudo systemctl stop chatbot.service
```

- If you wish to add new information data to the project, follow these steps:

1. Run your service.
2. Ensure that the new data files, in .docx format, are placed within the /data directory of the project.
3. The service will automatically restart. The system will process the new data files and update the internal database.
