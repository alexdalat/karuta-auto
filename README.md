# karuta-auto
Automation for the popular discord bot game Karuta.

It uses OCR to capture card details, retrieves their info from the bot, and makes the best choice on which card to grab.

This project got me hundreds of high wishlist cards (with low quickness and tougnness, granted) throughout quarantine. Intended to be used in a private server.


## Features

* **Automated Drops:** Periodically executes drop commands to generate cards.
* **OCR Analysis:** Uses OpenCV and Tesseract to read character names and series from card images.
* **Value Assessment:** Automatically looks up card wishlist counts using the lookup command.
* **Smart Claiming:** Prioritizes grabbing cards with the highest wishlist value, provided they meet the minimum threshold.
* **Routine Tasks:** Automates daily rewards and resource management commands.

## Prerequisites

* Python 3.8+
* **Tesseract OCR**


## Installation

1. Clone the repository.
2. Install the required Python dependencies:
```bash
pip install discord.py pyyaml opencv-python pytesseract numpy pandas matplotlib waiting
```

## Disclaimer

This software is for educational purposes. Automating user accounts (self-botting) is against the Discord Terms of Service and may result in account termination. Use at your own risk.
