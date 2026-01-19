# Discord PNL Card Bot

## Overview
A Discord bot that generates custom PNL (Profit and Loss) trading cards with multiple themes. Users can create personalized trading report images showing their crypto trading results.

## Project Structure
- `bot.py` - Main bot code with slash commands and card generation
- `config.py` - Configuration settings (token, card dimensions, colors)
- `run_bot.py` - Alternative launcher with dependency checks
- `backgrounds/` - Background images for card themes
- `fonts/` - Custom fonts for card text rendering

## Features
- `/pnl` - Create private PNL cards with custom inputs
- `/info` - Show bot information and help
- Multi-chain support: SOL, BNB, ETH
- Real-time price fetching via CoinGecko API
- Two themes: Cyberpunk (teal) and JJK (fire/retro)

## Setup
- Python 3.11
- Dependencies: discord.py, Pillow, python-dotenv, aiohttp, requests
- Required secret: `DISCORD_TOKEN`

## Running
The bot runs via the "Discord Bot" workflow using `python bot.py`
