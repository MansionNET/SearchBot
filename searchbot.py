#!/usr/bin/env python3
"""
MansionNet SearchBot
An IRC bot that provides private search functionality using the Hearch API
with privacy protection and rate limiting.
"""

import socket
import ssl
import time
import json
import base64
import requests
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional

class RateLimiter:
    def __init__(self, requests_per_minute: int, requests_per_day: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_window = deque()
        self.day_window = deque()
    
    def can_make_request(self) -> bool:
        now = datetime.now()
        while self.minute_window and self.minute_window[0] < now - timedelta(minutes=1):
            self.minute_window.popleft()
        while self.day_window and self.day_window[0] < now - timedelta(days=1):
            self.day_window.popleft()
        
        return (len(self.minute_window) < self.requests_per_minute and 
                len(self.day_window) < self.requests_per_day)
    
    def add_request(self):
        now = datetime.now()
        self.minute_window.append(now)
        self.day_window.append(now)

class SearchBot:
    def __init__(self):
        # IRC Configuration
        self.server = "irc.example.com"
        self.port = 6697  # SSL port
        self.nickname = "SearchBot"
        self.channels = ["#test_room"]
        
        # Rate Limiting - more conservative than MistralBot
        self.rate_limiter = RateLimiter(
            requests_per_minute=5,
            requests_per_day=500
        )
        
        # Store ongoing private searches
        self.active_searches = {}
        
        # SSL Configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def connect(self) -> bool:
        """Establish connection to the IRC server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.irc = self.ssl_context.wrap_socket(sock)
            
            print(f"Connecting to {self.server}:{self.port}...")
            self.irc.connect((self.server, self.port))
            
            self.send(f"NICK {self.nickname}")
            self.send(f"USER {self.nickname} 0 * :MansionNet Search Bot")
            
            buffer = ""
            while True:
                temp = self.irc.recv(2048).decode("UTF-8")
                buffer += temp
                
                if "PING" in buffer:
                    ping_token = buffer[buffer.find("PING"):].split()[1]
                    self.send(f"PONG {ping_token}")
                
                if "001" in buffer:  # RPL_WELCOME
                    for channel in self.channels:
                        self.send(f"JOIN {channel}")
                        time.sleep(1)
                    return True
                
                if "Closing Link" in buffer or "ERROR" in buffer:
                    return False
                
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False

    def send(self, message: str):
        """Send a raw message to the IRC server"""
        try:
            self.irc.send(bytes(f"{message}\r\n", "UTF-8"))
            print(f"Sent: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    def send_private_message(self, target: str, message: str):
        """Send a private message to a user"""
        try:
            # Split long messages to avoid truncation
            max_length = 400  # IRC message length limit with safety margin
            
            while message:
                if len(message) <= max_length:
                    self.send(f"PRIVMSG {target} :{message}")
                    break
                
                # Find a good breaking point
                split_point = message[:max_length].rfind(' ')
                if split_point == -1:
                    split_point = max_length
                
                self.send(f"PRIVMSG {target} :{message[:split_point]}")
                message = message[split_point:].lstrip()
                time.sleep(0.5)  # Avoid flooding
                
        except Exception as e:
            print(f"Error sending private message: {str(e)}")
            self.send(f"PRIVMSG {target} :Error: Message delivery failed.")

    def search_hearch(self, query: str) -> List[Dict]:
        """Perform a search using the Hearch API"""
        try:
            # Match exactly the config from the network request
            config = {
                "engines": {
                    "bing": {"enabled": True, "required": False, "requiredbyorigin": True, "preferred": False, "preferredbyorigin": False},
                    "brave": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": True, "preferredbyorigin": False},
                    "duckduckgo": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "etools": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "google": {"enabled": True, "required": False, "requiredbyorigin": True, "preferred": False, "preferredbyorigin": False},
                    "mojeek": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": True, "preferredbyorigin": False},
                    "presearch": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "qwant": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "startpage": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "swisscows": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False},
                    "yahoo": {"enabled": True, "required": False, "requiredbyorigin": False, "preferred": False, "preferredbyorigin": False}
                },
                "ranking": {
                    "rankexp": 0.5,
                    "rankmul": 1,
                    "rankconst": 0,
                    "rankscoremul": 1,
                    "rankscoreadd": 0,
                    "timesreturnedmul": 1,
                    "timesreturnedadd": 0,
                    "timesreturnedscoremul": 1,
                    "timesreturnedscoreadd": 0,
                    "engines": {
                        "bing": {"mul": 1.5, "add": 0},
                        "brave": {"mul": 1, "add": 0},
                        "duckduckgo": {"mul": 1.25, "add": 0},
                        "etools": {"mul": 1, "add": 0},
                        "google": {"mul": 1.5, "add": 0},
                        "mojeek": {"mul": 1, "add": 0},
                        "presearch": {"mul": 1.1, "add": 0},
                        "qwant": {"mul": 1.1, "add": 0},
                        "startpage": {"mul": 1.25, "add": 0},
                        "swisscows": {"mul": 1, "add": 0},
                        "yahoo": {"mul": 1.1, "add": 0}
                    }
                },
                "timings": {
                    "preferredtimeout": "500",
                    "hardtimeout": "1500"
                }
            }
            
            # Base64 encode the config
            config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
            
            # Build the URL with correct query parameters
            params = {
                'category': config_b64,
                'pages': '1',
                'q': query,
                'start': '1'
            }
            
            url = 'https://api.hearch.co/search/web'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Origin': 'https://hearch.co',
                'Referer': 'https://hearch.co/'
            }
            
            print(f"\nDebug - Making request to: {url}")
            print(f"Debug - Query: {query}")
            print(f"Debug - Full URL with params: {url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            print(f"Debug - Response status: {response.status_code}")
            print(f"Debug - Response headers: {dict(response.headers)}")
            print(f"Debug - Response content: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"Debug - Found {len(results)} results")
                return results[:5]
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return []
                        
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
                        
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

    def format_search_result(self, index: int, result: dict) -> str:
        """Format a single search result with IRC colors"""
        # IRC color codes
        BOLD = '\x02'          # Bold text
        COLOR = '\x03'         # Color indicator
        RESET = '\x0F'         # Reset formatting
        BLUE = '12'           # Blue for URLs
        GREEN = '03'          # Green for titles
        GRAY = '14'           # Gray for descriptions
        
        title = result.get('title', 'No title').strip()
        url = result.get('url', 'No URL').strip()
        desc = result.get('description', '').strip()
        
        # Clean up description (remove duplicate URLs and unnecessary text)
        desc = desc.replace(url, '')
        desc = ' '.join(desc.split())  # Normalize whitespace
        
        # Keep lengths reasonable but longer than before
        if len(title) > 100:
            title = title[:97] + "..."
        if len(url) > 100:
            url = url[:97] + "..."
        if len(desc) > 200:  # Allow longer descriptions
            desc = desc[:197] + "..."
        
        # Format result with colors
        result_line = (
            f"{index}. {COLOR}{GREEN}{title}{RESET} | "  # Green title
            f"{COLOR}{BLUE}{url}{RESET}"                 # Blue URL
        )
        
        if desc and len(desc) > 20:  # Only add if description is meaningful
            result_line += f" | {COLOR}{GRAY}{desc}{RESET}"  # Gray description
            
        return result_line

    def handle_private_message(self, sender: str, message: str):
        """Handle private messages and search commands"""
        try:
            if message.startswith("!search "):
                if not self.rate_limiter.can_make_request():
                    self.send_private_message(sender, "Rate limit exceeded. Please try again later.")
                    return
                
                query = message[8:].strip()
                if not query:
                    self.send_private_message(sender, "Usage: !search <query>")
                    return
                
                # Perform search and send results privately
                results = self.search_hearch(query)
                self.rate_limiter.add_request()
                
                if not results:
                    self.send_private_message(sender, "No results found.")
                    return
                
                # Send each result as a separate message
                for i, result in enumerate(results[:5], 1):
                    formatted_result = self.format_search_result(i, result)
                    self.send_private_message(sender, formatted_result)
                    time.sleep(0.5)  # Small delay between messages to prevent flooding
                
                # Add attribution message
                GRAY = '\x0314'  # IRC color code for gray
                BLUE = '\x0312'  # IRC color code for blue
                RESET = '\x0F'   # Reset formatting
                attribution = f"{GRAY}Search results powered by {BLUE}https://hearch.co/{GRAY} - Privacy-focused metasearch{RESET}"
                time.sleep(0.5)  # Small delay before attribution
                self.send_private_message(sender, attribution)
                
            elif message == "!help":
                help_msg = ("SearchBot Commands: "
                          "!search <query> - Search the web privately (results sent via PM) | "
                          "!help - Show this help message")
                self.send_private_message(sender, help_msg)
                
        except Exception as e:
            print(f"Error handling private message: {str(e)}")
            self.send_private_message(sender, "An error occurred processing your request.")

    def handle_channel_message(self, sender: str, channel: str, message: str):
        """Handle channel messages"""
        if message == "!help":
            help_msg = ("SearchBot: Use !search <query> in a private message to search privately. "
                       "Results will be sent to you directly.")
            self.send(f"PRIVMSG {channel} :{help_msg}")
        elif message.startswith("!search"):
            self.send(f"PRIVMSG {channel} :{sender}: To protect your privacy, please use search commands in a private message.")

    def run(self):
        """Main bot loop"""
        while True:
            try:
                if self.connect():
                    buffer = ""
                    
                    while True:
                        try:
                            buffer += self.irc.recv(2048).decode("UTF-8")
                            lines = buffer.split("\r\n")
                            buffer = lines.pop()
                            
                            for line in lines:
                                print(line)  # Debug output
                                
                                if line.startswith("PING"):
                                    ping_token = line.split()[1]
                                    self.send(f"PONG {ping_token}")
                                
                                if "PRIVMSG" in line:
                                    sender = line.split("!")[0][1:]
                                    try:
                                        msg_parts = line.split("PRIVMSG ", 1)[1]
                                        target, message = msg_parts.split(":", 1)
                                        target = target.strip()
                                        message = message.strip()
                                        
                                        # Handle private messages differently from channel messages
                                        if target == self.nickname:
                                            self.handle_private_message(sender, message)
                                        elif target in self.channels:
                                            self.handle_channel_message(sender, target, message)
                                            
                                    except IndexError:
                                        continue
                                        
                        except UnicodeDecodeError:
                            buffer = ""
                            continue
                            
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(30)
                continue

if __name__ == "__main__":
    bot = SearchBot()
    bot.run()
