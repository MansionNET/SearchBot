# SearchBot

An IRC bot that provides private search functionality using the Hearch API, designed for privacy and easy deployment.

## Features

- Privacy-focused search using Hearch's metasearch API
- Private messaging for search results to protect user privacy
- Color-coded, well-formatted search results
- Rate limiting to prevent abuse
- Automatic service management via systemd
- Easy deployment and configuration

## Installation

### Prerequisites

- Python 3.8 or higher
- pip
- virtualenv
- systemd (for service management)

### Basic Installation

1. Clone the repository:
```bash
git clone https://github.com/MansionNET/searchbot.git
cd searchbot
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### Setting Up as a Service

1. Create the systemd service file:
```bash
sudo nano /etc/systemd/system/searchbot.service
```

2. Add the following content (modify paths as needed):
```ini
[Unit]
Description=MansionNet SearchBot
After=network.target

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/path/to/searchbot
Environment=PATH=/path/to/searchbot/venv/bin
ExecStart=/path/to/searchbot/venv/bin/python searchbot.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

3. Make the bot executable:
```bash
chmod +x searchbot.py
```

4. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable searchbot
sudo systemctl start searchbot
```

## Usage

### User Commands

The bot supports the following commands:

- `!search <query>`: Performs a private web search
- `!help`: Shows available commands and usage information

Examples:
```
/msg SearchBot !search python tutorial
/msg SearchBot !help
```

### Service Management

Control the bot service using standard systemd commands:

```bash
# Check status
sudo systemctl status searchbot

# View logs
sudo journalctl -u searchbot -f

# Stop the bot
sudo systemctl stop searchbot

# Restart the bot
sudo systemctl restart searchbot
```

## Configuration

### IRC Settings

Edit `searchbot.py` to modify these settings:

```python
self.server = "irc.inthemansion.com"
self.port = 6697  # SSL port
self.nickname = "SearchBot"
self.channels = ["#test_room"]  # Add more channels as needed
```

### Rate Limiting

Rate limiting can be adjusted in the `RateLimiter` class:

```python
self.rate_limiter = RateLimiter(
    requests_per_minute=5,
    requests_per_day=500
)
```

## Technical Details

### Result Formatting

Search results are formatted with IRC color codes for better readability:
- Titles in green
- URLs in blue
- Descriptions in gray

Example output:
```
1. Welcome to Python.org | https://www.python.org | The mission of the Python Software Foundation...
Search results powered by https://hearch.co/ - Privacy-focused metasearch
```

### API Integration

The bot uses the Hearch API for searching, with proper rate limiting and error handling. Each request includes:
- Base64 encoded configuration
- Multiple search engine support
- Result ranking and scoring
- Custom timeout settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to [Hearch](https://hearch.co/) for providing the search API
- Thanks to the MansionNet IRC community
- Icons by [icon8](https://icons8.com)
