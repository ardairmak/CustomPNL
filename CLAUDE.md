# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CustomPNL is a Discord bot that generates custom Solana PNL (Profit and Loss) trading cards. Users invoke slash commands to create private, ephemeral image cards showing their trading performance. Supports custom backgrounds and fonts for various visual themes.

## Commands

### Run the bot
```bash
python run_bot.py
```

### Test card generation without Discord
```bash
python test_card_generation.py
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Architecture

**Entry Points:**
- `run_bot.py` - Main entry point with dependency/environment validation
- `bot.py` - Discord bot logic, can also be run directly
- `test_card_generation.py` - Standalone testing utility for card generation

**Core Components:**
- `bot.py` contains the `PNLCard` class which handles all image generation using PIL/Pillow
- `config.py` holds all configuration: colors, fonts, image dimensions, Discord token loading
- `get_token_price(chain)` async function fetches real-time token price from CoinGecko API with fallback

**Data Flow:**
1. User executes `/pnl` slash command with username, coin_name, bought_amount, sold_amount, and optionally chain (SOL/BNB/ETH)
2. Bot fetches current native token price from CoinGecko
3. `PNLCard` calculates PNL values and renders a PNG image in memory (BytesIO)
4. Response is sent as ephemeral (private) Discord message with embedded image

**Multi-chain Support:**
- Supported chains defined in `SUPPORTED_CHAINS` dict in `bot.py`
- Each chain has: CoinGecko ID, display symbol, fallback price
- Default chain is SOL

**Discord Integration:**
- Uses modern `app_commands` API for slash commands
- All responses are ephemeral (only visible to command user)
- Legacy prefix commands (`!pnl`, `!info`) redirect users to slash commands

**Image Generation:**
- Card size: 1188x668 pixels
- Custom backgrounds from `backgrounds/` folder, falls back to generated cyberpunk background
- Custom fonts from `fonts/` folder (ShareTechMono primary)
- Color coding: cyan/white for profit, red for loss, gray for neutral elements

## Environment Setup

Requires a `.env` file with:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

## Key Patterns

- Async operations for Discord commands and HTTP requests
- Synchronous fallback for API calls if async fails
- In-memory image generation (no temp files)
- K-formatting for large numbers (1000+ becomes 1.0K)
