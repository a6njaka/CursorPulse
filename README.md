# Cursor Pulse

A customizable mouse cursor enhancement tool that adds visual feedback for clicks and drags, perfect for tutorials, presentations, or screen recordings.

![Cursor Pulse Screenshot](./screenshot.png) <!-- Replace with your actual screenshot file -->

## Features

- Visual circle around mouse cursor
- Customizable colors for different click types
- Adjustable sizes and animation durations
- Toggle visibility with hotkey (Ctrl+Shift+M by default)
- System tray integration
- Configuration GUI for easy customization


## Download Pre-Compiled Version
For users without Python, download the latest standalone executable:<br>
[Download Cursor Pulse v1.0.0](https://github.com/a6njaka/CursorPulse/releases/download/v1.0.0/CursorPulse_v1.0.0.exe) (right-click → "Save link as")<br>
SHA-256 Checksum: `5201042903c537828b75cc0515caf243324541e5d24a00079d5323813a0d09be` (verify integrity)*

## Installation

1. Clone the repository:
   git clone https://github.com/a6njaka/CursorPulse.git
   cd CursorPulse
   
2. Install required dependencies:
	pip install -r requirements.txt

## Usage
Run the application:
	python CursorPulse.py
	
Right-click the system tray icon to access menu
Use the configuration window to customize appearance
Toggle visibility with Ctrl+Shift+M


## Requirements
Python 3.6+

Windows OS (for proper transparency effects)

Packages: tkinter, pyautogui, pynput, keyboard, pystray, Pillow

## Contributing
Contributions are welcome! Please open an issue or pull request for any improvements.

## License
This project is licensed under [GPL-3.0](LICENSE).  
Key points:
- You may use, modify, and distribute this software
- **All derivative works must remain under GPL-3.0**
- You must provide source code with distributions
- No warranty is provided