# AddOn development

https://developers.home-assistant.io/docs/add-ons/testing/

## Setup the environment

- Follow the instructions to download and install the [Remote Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VS Code extension:

  To get started, follow these steps:

  1. Install [VS Code](https://code.visualstudio.com/) or VS Code Insiders and the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

  2. Install and configure Docker for your operating system. Enable the [Windows WSL2 back-end](https://aka.ms/vscode-remote/containers/docker-wsl2).

## Testing the Add-On locally with the Dev Container

- When VS Code has opened your folder in the container (which can take some time for the first run) you'll need to run the task (Terminal -> Run Task) 'Start Home Assistant', which will bootstrap Supervisor and Home Assistant.

- You'll then be able to access the normal onboarding process via the Home Assistant instance at http://localhost:7123/.

- The add-on(s) found in your root folder will automatically be found in the Local Add-ons repository.

## Create and activate a virtual environment

Create the environment:
```
python -m venv .venv
```

Activate it:
```
.\.venv\Scripts\activate
```

If VS Code not automatically detects it:
Ctrl + Shift + P → Python: Select Interpreter → ./.venv/bin/python
