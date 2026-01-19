import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
from typing import Optional
import config
import aiohttp
import requests

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

# Supported chains with their CoinGecko IDs and display symbols
SUPPORTED_CHAINS = {
    'SOL': {'id': 'solana', 'symbol': 'SOL', 'fallback_price': 100.0},
    'BNB': {'id': 'binancecoin', 'symbol': 'BNB', 'fallback_price': 300.0},
    'ETH': {'id': 'ethereum', 'symbol': 'ETH', 'fallback_price': 2000.0},
}

async def get_token_price(chain: str = 'SOL'):
    """Get current token price from CoinGecko API"""
    chain_info = SUPPORTED_CHAINS.get(chain.upper(), SUPPORTED_CHAINS['SOL'])
    token_id = chain_info['id']
    fallback_price = chain_info['fallback_price']

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd') as response:
                if response.status == 200:
                    data = await response.json()
                    return data[token_id]['usd']
                else:
                    # Fallback to synchronous request
                    fallback_response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd')
                    if fallback_response.status_code == 200:
                        return fallback_response.json()[token_id]['usd']
                    else:
                        return fallback_price
    except Exception as e:
        print(f"Error fetching {chain} price: {e}")
        return fallback_price

class PNLCard:
    def __init__(self, username: str, coin_name: str, bought_amount: float, sold_amount: float, token_price: float, chain: str = 'SOL', background_path: str = None):
        self.username = username
        self.coin_name = coin_name.upper()
        self.chain = chain.upper()
        self.bought_amount = bought_amount
        self.sold_amount = sold_amount
        self.token_price = token_price
        self.background_path = background_path or f"{config.BACKGROUNDS_FOLDER}/default.jpg"

        # Calculate dollar values
        self.bought_usd = bought_amount * token_price
        self.sold_usd = sold_amount * token_price

        # Calculate profit/loss in both native token and USD
        self.pnl_amount = sold_amount - bought_amount
        self.pnl_usd = self.pnl_amount * token_price
        self.is_profit = self.pnl_amount > 0
        
    def generate_card(self) -> io.BytesIO:
        """Generate the futuristic PNL card image"""
        # Create base image
        width, height = config.DEFAULT_CARD_WIDTH, config.DEFAULT_CARD_HEIGHT
        
        # Try to load custom background image, otherwise create default
        try:
            if os.path.exists(self.background_path):
                bg_img = Image.open(self.background_path)
                bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                # Create default cyberpunk background
                bg_img = self.create_cyberpunk_background(width, height)
        except:
            bg_img = self.create_cyberpunk_background(width, height)
        
        draw = ImageDraw.Draw(bg_img)
        
        # Load fonts with fallbacks
        try:
            primary_font = config.FONTS['primary_font']
            header_font = ImageFont.truetype(primary_font, config.FONTS['sizes']['header'])
            label_font = ImageFont.truetype(primary_font, config.FONTS['sizes']['label'])
            value_font = ImageFont.truetype(primary_font, config.FONTS['sizes']['value'])
            small_font = ImageFont.truetype(primary_font, config.FONTS['sizes']['small'])
            large_font = ImageFont.truetype(primary_font, config.FONTS['sizes']['large'])
        except:
            # Fallback to default fonts if custom font fails
            header_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            large_font = ImageFont.load_default()
        
        # Colors - bright for first 2 sections, pale for rest
        cyan = (0, 255, 255)          # Bright cyan for coin name and profit
        white = (255, 255, 255)       # Bright white for coin name and profit
        pale_gray = (120, 120, 120)   # Pale gray for other sections  
        gray = (150, 150, 150)        # Regular gray for USD values
        green = (0, 255, 100)         # Bright green for profit
        red = (255, 50, 50)
        ocean_blue = (30, 60, 120) 
        dolar = (44,44,44)
        
        # Draw corner brackets
        self.draw_corner_brackets(draw, width, height, cyan)
        
        
        # Left side info
        left_x = 100
        
        # Y positions for easy adjustment
        y_coin = 130
        y_profit = 192
        y_profit_usd = 225
        y_bought = 287
        y_bought_usd = 320
        y_sold = 382
        y_sold_usd = 415
        y_user = 472
        y_bottom = 505
        
        # Coin name (replacing "> NO")
        draw.text((left_x, y_coin), f"> {self.coin_name}", fill=white, font=label_font)
        
        # Profit/Loss section (bright)
        pnl_abs = abs(self.pnl_amount)
        if pnl_abs >= 1000:
            pnl_formatted = f"{pnl_abs/1000:.1f}K"
        else:
            pnl_formatted = f"{pnl_abs:.1f}"

        profit_text = f"PROFIT: +{pnl_formatted} {self.chain}" if self.is_profit else f"LOSS: -{pnl_formatted} {self.chain}"
        profit_color = cyan if self.is_profit else red
        draw.text((left_x, y_profit), profit_text, fill=profit_color, font=large_font)
        # Format profit USD value
        pnl_usd_abs = abs(self.pnl_usd)
        pnl_usd_formatted = f"{pnl_usd_abs/1000:.1f}K" if pnl_usd_abs >= 1000 else f"{pnl_usd_abs:.1f}"
        draw.text((left_x, y_profit_usd), f"> ${pnl_usd_formatted}", fill=cyan, font=small_font)
        
        # Bought section (pale)
        draw.text((left_x, y_bought), f"BOUGHT: {self.bought_amount:.1f} {self.chain}", fill=pale_gray, font=value_font)
        # Format bought USD value
        bought_usd_formatted = f"{self.bought_usd/1000:.1f}K" if self.bought_usd >= 1000 else f"{self.bought_usd:.1f}"
        draw.text((left_x, y_bought_usd), f"> ${bought_usd_formatted}", fill=dolar, font=small_font)

        # Sold section (pale)
        draw.text((left_x, y_sold), f"SOLD: {self.sold_amount:.1f} {self.chain}", fill=pale_gray, font=value_font)
        # Format sold USD value
        sold_usd_formatted = f"{self.sold_usd/1000:.1f}K" if self.sold_usd >= 1000 else f"{self.sold_usd:.1f}"
        draw.text((left_x, y_sold_usd), f"> ${sold_usd_formatted}", fill=dolar, font=small_font)
        
        
        # User section (pale)
        draw.text((left_x, y_user), f"USER: {self.username.upper()}", fill=pale_gray, font=value_font)
        draw.text((left_x, y_bottom), "> SRCL", fill=dolar, font=small_font)
        
        # Bottom text
        
        # Convert to bytes
        output = io.BytesIO()
        bg_img.save(output, format='PNG')
        output.seek(0)
        
        return output
    
    def create_cyberpunk_background(self, width: int, height: int) -> Image.Image:
        """Create a cyberpunk-themed background"""
        # Create dark background with gradient effect
        img = Image.new('RGB', (width, height), color=(15, 25, 35))  # Dark blue-gray
        draw = ImageDraw.Draw(img)
        
        # Add subtle grid pattern
        grid_color = (25, 35, 45)
        for x in range(0, width, 40):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        # Add cyan accents
        accent_color = (0, 100, 120)
        draw.rectangle([10, 10, width-10, height-10], outline=accent_color, width=2)
        
        return img
    
    def draw_corner_brackets(self, draw, width: int, height: int, color):
        """Draw cyberpunk corner brackets"""
        bracket_size = 30
        bracket_width = 3
        
        # Top-left bracket
        draw.line([(20, 20), (20 + bracket_size, 20)], fill=color, width=bracket_width)
        draw.line([(20, 20), (20, 20 + bracket_size)], fill=color, width=bracket_width)
        
        # Top-right bracket  
        draw.line([(width - 20, 20), (width - 20 - bracket_size, 20)], fill=color, width=bracket_width)
        draw.line([(width - 20, 20), (width - 20, 20 + bracket_size)], fill=color, width=bracket_width)
        
        # Bottom-left bracket
        draw.line([(20, height - 20), (20 + bracket_size, height - 20)], fill=color, width=bracket_width)
        draw.line([(20, height - 20), (20, height - 20 - bracket_size)], fill=color, width=bracket_width)
        
        # Bottom-right bracket
        draw.line([(width - 20, height - 20), (width - 20 - bracket_size, height - 20)], fill=color, width=bracket_width)
        draw.line([(width - 20, height - 20), (width - 20, height - 20 - bracket_size)], fill=color, width=bracket_width)

@bot.event
async def on_ready():
    print(f'{bot.user} has landed on the trading seas!')
    
    # Create backgrounds directory if it doesn't exist
    if not os.path.exists(config.BACKGROUNDS_FOLDER):
        os.makedirs(config.BACKGROUNDS_FOLDER)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'⚡ Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'❌ Failed to sync slash commands: {e}')

@bot.tree.command(name='pnl', description='Create a custom PNL trading card')
@app_commands.describe(
    username='Your username/trader name',
    coin_name='The coin/token you traded (e.g., BONK, PEPE, WIF)',
    bought_amount='How much of the native token you spent',
    sold_amount='How much of the native token you received',
    chain='The blockchain/native token (default: SOL)'
)
@app_commands.choices(chain=[
    app_commands.Choice(name='Solana (SOL)', value='SOL'),
    app_commands.Choice(name='BNB Chain (BNB)', value='BNB'),
    app_commands.Choice(name='Ethereum (ETH)', value='ETH'),
])
async def slash_pnl(interaction: discord.Interaction, username: str, coin_name: str, bought_amount: float, sold_amount: float, chain: app_commands.Choice[str] = None):
    """Create a PNL card with direct input"""

    try:
        # Acknowledge the interaction first (ephemeral = private)
        await interaction.response.defer(ephemeral=True)

        # Get chain value (default to SOL)
        chain_value = chain.value if chain else 'SOL'

        # Fetch current token price for the selected chain
        token_price = await get_token_price(chain_value)

        # Create PNL card with custom background
        # Look for any image file in backgrounds folder
        background_path = None
        if os.path.exists(config.BACKGROUNDS_FOLDER):
            for file in os.listdir(config.BACKGROUNDS_FOLDER):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')) and not file.startswith('.'):
                    background_path = f"{config.BACKGROUNDS_FOLDER}/{file}"
                    break

        pnl_card = PNLCard(username, coin_name, bought_amount, sold_amount, token_price, chain_value, background_path)
        card_image = pnl_card.generate_card()

        # Create Discord file
        discord_file = discord.File(card_image, filename=f"{username}_{coin_name.lower()}_pnl.png")

        # Send the card with embed (ephemeral = private)
        embed = discord.Embed(
            title="🔒 Private Trading Report",
            description="This PNL card is only visible to you!",
            color=0x00ff00 if pnl_card.is_profit else 0xff0000
        )
        embed.add_field(name="Trader", value=username, inline=True)
        embed.add_field(name=f"{chain_value} Price", value=f"${token_price:.2f}", inline=True)
        # Format P&L for Discord embed
        pnl_abs = abs(pnl_card.pnl_amount)
        pnl_formatted = f"{pnl_abs/1000:.1f}K" if pnl_abs >= 1000 else f"{pnl_abs:.1f}"
        pnl_usd_abs = abs(pnl_card.pnl_usd)
        pnl_usd_formatted = f"{pnl_usd_abs/1000:.1f}K" if pnl_usd_abs >= 1000 else f"{pnl_usd_abs:.2f}"
        embed.add_field(name="P&L", value=f"{'+' if pnl_card.is_profit else '-'}{pnl_formatted} {chain_value} (${pnl_usd_formatted})", inline=False)

        await interaction.followup.send(embed=embed, file=discord_file, ephemeral=True)

    except ValueError:
        await interaction.followup.send("❌ Invalid input! Please use numbers for coin amounts.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error creating PNL card: {str(e)}", ephemeral=True)

@bot.tree.command(name='info', description='Show information about the PNL Card Bot')
async def slash_info(interaction: discord.Interaction):
    """Show help for custom PNL commands"""
    embed = discord.Embed(
        title="🚀 Custom PNL Card Bot",
        description="Create custom trading reports with futuristic cyberpunk design!",
        color=0x00FFFF
    )
    
    embed.add_field(
        name="/pnl",
        value="Create a **private** custom PNL card with direct input\nParameters:\n• username: Your trader name\n• coin_name: Token you traded (BONK, PEPE, etc.)\n• bought_amount: Native tokens spent\n• sold_amount: Native tokens received\n• chain: SOL, BNB, or ETH (default: SOL)",
        inline=False
    )
    
    embed.add_field(
        name="Features",
        value="✅ **Private PNL cards** (only you can see them)\n✅ Multi-chain support (SOL, BNB, ETH)\n✅ Real-time price via CoinGecko API\n✅ Automatic USD conversion\n✅ Custom backgrounds and themes",
        inline=False
    )
    
    embed.add_field(
        name="Example Usage",
        value="Use `/pnl username:CryptoTrader coin_name:SOL bought_amount:100 sold_amount:75`\nBot will fetch current SOL price and generate your **private** custom card!",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Legacy commands for transition help
@bot.command(name='pnl')
async def legacy_pnl(ctx):
    """Legacy command - redirect to slash command"""
    embed = discord.Embed(
        title="🔄 Command Updated!",
        description="This bot now uses **Slash Commands**!\n\nInstead of `!pnl`, please use `/pnl`",
        color=0xFFDD00
    )
    embed.add_field(
        name="New Usage",
        value="Type `/pnl` and fill in the parameters:\n• username\n• coin_name\n• bought_amount\n• sold_amount",
        inline=False
    )
    embed.add_field(
        name="Example",
        value="`/pnl username:CryptoTrader coin_name:SOL bought_amount:100 sold_amount:75`",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='info')
async def legacy_info(ctx):
    """Legacy command - redirect to slash command"""
    embed = discord.Embed(
        title="🔄 Command Updated!",
        description="This bot now uses **Slash Commands**!\n\nInstead of `!info`, please use `/info`",
        color=0xFFDD00
    )
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        print("❌ Please set DISCORD_TOKEN in your .env file")
        print("💡 Create a .env file with: DISCORD_TOKEN=your_bot_token_here")
    else:
        bot.run(config.DISCORD_TOKEN) 