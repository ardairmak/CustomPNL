import discord
from discord.ext import commands
from discord import app_commands
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
from typing import Optional
import config
import aiohttp
from aiohttp import web
import requests
import asyncio

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

# Theme configurations
THEMES = {
    'cyberpunk': {
        'background': 'backgrounds/background.jpg',
        'fonts': {
            'title': ('fonts/ShareTechMono-Regular.ttf', 24),
            'large': ('fonts/ShareTechMono-Regular.ttf', 24),
            'medium': ('fonts/ShareTechMono-Regular.ttf', 24),
            'small': ('fonts/ShareTechMono-Regular.ttf', 24),
        },
        'colors': {
            'profit': (0, 255, 255),
            'loss': (255, 50, 50),
            'text': (255, 255, 255),
            'muted': (120, 120, 120),
            'accent': (0, 255, 255),
        }
    },
    'jjk': {
        'background': 'backgrounds/jjk.webp',
        'fonts': {
            'title': ('fonts/PressStart2P.ttf', 32),
            'large': ('fonts/VT323-Regular.ttf', 85),
            'medium': ('fonts/VT323-Regular.ttf', 42),
            'small': ('fonts/VT323-Regular.ttf', 34),
        },
        'colors': {
            'profit': (255, 220, 50),
            'loss': (255, 50, 50),
            'text': (255, 255, 255),
            'muted': (150, 150, 150),
            'accent': (255, 120, 0),
        }
    },
    'toji': {
        'background': 'backgrounds/toji.jpg',
        'fonts': {
            'title': ('fonts/PressStart2P.ttf', 32),
            'large': ('fonts/VT323-Regular.ttf', 85),
            'medium': ('fonts/VT323-Regular.ttf', 42),
            'small': ('fonts/VT323-Regular.ttf', 34),
        },
        'colors': {
            'profit': (255, 190, 60),      # Amber gold (matches lights)
            'loss': (180, 50, 50),          # Dark red
            'text': (255, 240, 220),        # Warm cream white
            'muted': (160, 140, 110),       # Muted brown/tan
            'accent': (255, 170, 50),       # Golden amber
        }
    }
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
                    fallback_response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd')
                    if fallback_response.status_code == 200:
                        return fallback_response.json()[token_id]['usd']
                    else:
                        return fallback_price
    except Exception as e:
        print(f"Error fetching {chain} price: {e}")
        return fallback_price


class PNLCard:
    def __init__(self, username: str, coin_name: str, bought_amount: float, sold_amount: float,
                 token_price: float, chain: str = 'SOL', theme: str = 'cyberpunk'):
        self.username = username
        self.coin_name = coin_name.upper()
        self.chain = chain.upper()
        self.bought_amount = bought_amount
        self.sold_amount = sold_amount
        self.token_price = token_price
        self.theme = theme.lower() if theme.lower() in THEMES else 'cyberpunk'
        self.theme_config = THEMES[self.theme]

        # Calculate values
        self.bought_usd = bought_amount * token_price
        self.sold_usd = sold_amount * token_price
        self.pnl_amount = sold_amount - bought_amount
        self.pnl_usd = self.pnl_amount * token_price
        self.is_profit = self.pnl_amount > 0
        self.multiplier = sold_amount / bought_amount if bought_amount > 0 else 0

    def generate_card(self) -> io.BytesIO:
        """Generate the PNL card based on theme"""
        if self.theme in ['jjk', 'toji']:
            return self._generate_jjk_card()
        else:
            return self._generate_cyberpunk_card()

    def _generate_cyberpunk_card(self) -> io.BytesIO:
        """Generate cyberpunk themed card"""
        width, height = config.DEFAULT_CARD_WIDTH, config.DEFAULT_CARD_HEIGHT

        # Load background
        bg_path = self.theme_config['background']
        try:
            if os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                bg_img = self._create_cyberpunk_background(width, height)
        except:
            bg_img = self._create_cyberpunk_background(width, height)

        draw = ImageDraw.Draw(bg_img)

        # Load fonts
        fonts = self.theme_config['fonts']
        colors = self.theme_config['colors']

        try:
            label_font = ImageFont.truetype(fonts['medium'][0], fonts['medium'][1])
            value_font = ImageFont.truetype(fonts['medium'][0], fonts['medium'][1])
            small_font = ImageFont.truetype(fonts['small'][0], fonts['small'][1])
            large_font = ImageFont.truetype(fonts['large'][0], fonts['large'][1])
        except:
            label_font = value_font = small_font = large_font = ImageFont.load_default()

        # Draw corner brackets
        self._draw_corner_brackets(draw, width, height, colors['accent'])

        # Positions
        left_x = 100
        y_coin, y_profit, y_profit_usd = 130, 192, 225
        y_bought, y_bought_usd = 287, 320
        y_sold, y_sold_usd = 382, 415
        y_user, y_bottom = 472, 505

        # Coin name
        draw.text((left_x, y_coin), f"> {self.coin_name}", fill=colors['text'], font=label_font)

        # Profit/Loss
        pnl_formatted = f"{abs(self.pnl_amount)/1000:.1f}K" if abs(self.pnl_amount) >= 1000 else f"{abs(self.pnl_amount):.1f}"
        profit_text = f"PROFIT: +{pnl_formatted} {self.chain}" if self.is_profit else f"LOSS: -{pnl_formatted} {self.chain}"
        profit_color = colors['profit'] if self.is_profit else colors['loss']
        draw.text((left_x, y_profit), profit_text, fill=profit_color, font=large_font)

        pnl_usd_formatted = f"{abs(self.pnl_usd)/1000:.1f}K" if abs(self.pnl_usd) >= 1000 else f"{abs(self.pnl_usd):.1f}"
        draw.text((left_x, y_profit_usd), f"> ${pnl_usd_formatted}", fill=colors['accent'], font=small_font)

        # Bought
        draw.text((left_x, y_bought), f"BOUGHT: {self.bought_amount:.1f} {self.chain}", fill=colors['muted'], font=value_font)
        bought_usd_formatted = f"{self.bought_usd/1000:.1f}K" if self.bought_usd >= 1000 else f"{self.bought_usd:.1f}"
        draw.text((left_x, y_bought_usd), f"> ${bought_usd_formatted}", fill=(44,44,44), font=small_font)

        # Sold
        draw.text((left_x, y_sold), f"SOLD: {self.sold_amount:.1f} {self.chain}", fill=colors['muted'], font=value_font)
        sold_usd_formatted = f"{self.sold_usd/1000:.1f}K" if self.sold_usd >= 1000 else f"{self.sold_usd:.1f}"
        draw.text((left_x, y_sold_usd), f"> ${sold_usd_formatted}", fill=(44,44,44), font=small_font)

        # User
        draw.text((left_x, y_user), f"USER: {self.username.upper()}", fill=colors['muted'], font=value_font)
        draw.text((left_x, y_bottom), f"> {self.chain}", fill=(44,44,44), font=small_font)

        output = io.BytesIO()
        bg_img.save(output, format='PNG')
        output.seek(0)
        return output

    def _generate_jjk_card(self) -> io.BytesIO:
        """Generate JJK/fire themed card with retro terminal style"""
        width, height = config.DEFAULT_CARD_WIDTH, config.DEFAULT_CARD_HEIGHT

        # Load background
        bg_path = self.theme_config['background']
        try:
            if os.path.exists(bg_path):
                bg_img = Image.open(bg_path).convert("RGBA")
                bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                bg_img = Image.new('RGBA', (width, height), (30, 20, 10, 255))
        except:
            bg_img = Image.new('RGBA', (width, height), (30, 20, 10, 255))

        overlay = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Load fonts
        fonts = self.theme_config['fonts']
        colors = self.theme_config['colors']

        try:
            font_title = ImageFont.truetype(fonts['title'][0], fonts['title'][1])
            font_big = ImageFont.truetype(fonts['large'][0], fonts['large'][1])
            font_med = ImageFont.truetype(fonts['medium'][0], fonts['medium'][1])
            font_small = ImageFont.truetype(fonts['small'][0], fonts['small'][1])
        except:
            font_title = font_big = font_med = font_small = ImageFont.load_default()

        # Dark panel
        draw.rectangle([0, 0, 300, height], fill=(0, 0, 0, 240))
        for i in range(300, 420):
            alpha = int(240 * (1 - (i - 300) / 120))
            draw.line([(i, 0), (i, height)], fill=(0, 0, 0, alpha))

        # Coin name with glow
        coin_text = f"${self.coin_name}"
        glow_layer = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        for offset in range(8, 0, -2):
            glow_draw.text((45-offset, 35-offset), coin_text, font=font_title, fill=(255, 150, 0, 40))
            glow_draw.text((45+offset, 35+offset), coin_text, font=font_title, fill=(255, 150, 0, 40))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4))
        overlay = Image.alpha_composite(overlay, glow_layer)
        draw = ImageDraw.Draw(overlay)
        draw.text((45, 35), coin_text, font=font_title, fill=colors['text'])

        # Multiplier with glow
        mult_text = f"{self.multiplier:.1f}X"
        mult_color = colors['profit'] if self.is_profit else colors['loss']
        glow2 = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
        glow2_draw = ImageDraw.Draw(glow2)
        glow2_draw.text((45, 85), mult_text, font=font_big, fill=(*mult_color[:3], 60))
        glow2 = glow2.filter(ImageFilter.GaussianBlur(10))
        overlay = Image.alpha_composite(overlay, glow2)
        draw = ImageDraw.Draw(overlay)
        draw.text((45, 90), mult_text, font=font_big, fill=mult_color)

        # Profit USD
        profit_sign = "+" if self.is_profit else "-"
        usd_formatted = f"{profit_sign}${abs(self.pnl_usd)/1000:.1f}K" if abs(self.pnl_usd) >= 1000 else f"{profit_sign}${abs(self.pnl_usd):,.0f}"
        draw.text((45, 180), usd_formatted, font=font_med, fill=colors['accent'])

        # Stats
        draw.text((35, 255), "> INVESTED", font=font_small, fill=colors['muted'])
        draw.text((220, 255), f"{self.bought_amount:.1f} {self.chain}", font=font_small, fill=colors['text'])

        draw.text((35, 310), "> RETURNED", font=font_small, fill=colors['muted'])
        draw.text((220, 310), f"{self.sold_amount:.1f} {self.chain}", font=font_small, fill=colors['text'])

        draw.text((35, 365), "> PROFIT", font=font_small, fill=colors['muted'])
        pnl_formatted = f"{profit_sign}{abs(self.pnl_amount)/1000:.1f}K" if abs(self.pnl_amount) >= 1000 else f"{profit_sign}{abs(self.pnl_amount):.1f}"
        draw.text((220, 365), f"{pnl_formatted} {self.chain}", font=font_small, fill=mult_color)

        # Username with cursor
        draw.text((35, 450), f"@{self.username.upper()}", font=font_med, fill=colors['accent'])
        cursor_x = 35 + len(f"@{self.username.upper()}") * 21
        draw.rectangle([cursor_x, 455, cursor_x + 18, 490], fill=colors['accent'])

        # Decorative corners
        acc = colors['accent'] + (200,)
        draw.line([(18, 18), (75, 18)], fill=acc, width=3)
        draw.line([(18, 18), (18, 75)], fill=acc, width=3)
        draw.line([(18, 650), (75, 650)], fill=acc, width=3)
        draw.line([(18, 593), (18, 650)], fill=acc, width=3)

        # Scanlines
        for y in range(0, height, 4):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, 20))

        result = Image.alpha_composite(bg_img, overlay)
        output = io.BytesIO()
        result.convert('RGB').save(output, format='PNG')
        output.seek(0)
        return output

    def _create_cyberpunk_background(self, width: int, height: int) -> Image.Image:
        """Create a cyberpunk-themed background"""
        img = Image.new('RGB', (width, height), color=(15, 25, 35))
        draw = ImageDraw.Draw(img)

        grid_color = (25, 35, 45)
        for x in range(0, width, 40):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)

        accent_color = (0, 100, 120)
        draw.rectangle([10, 10, width-10, height-10], outline=accent_color, width=2)

        return img

    def _draw_corner_brackets(self, draw, width: int, height: int, color):
        """Draw corner brackets"""
        bracket_size, bracket_width = 30, 3

        draw.line([(20, 20), (20 + bracket_size, 20)], fill=color, width=bracket_width)
        draw.line([(20, 20), (20, 20 + bracket_size)], fill=color, width=bracket_width)
        draw.line([(width - 20, 20), (width - 20 - bracket_size, 20)], fill=color, width=bracket_width)
        draw.line([(width - 20, 20), (width - 20, 20 + bracket_size)], fill=color, width=bracket_width)
        draw.line([(20, height - 20), (20 + bracket_size, height - 20)], fill=color, width=bracket_width)
        draw.line([(20, height - 20), (20, height - 20 - bracket_size)], fill=color, width=bracket_width)
        draw.line([(width - 20, height - 20), (width - 20 - bracket_size, height - 20)], fill=color, width=bracket_width)
        draw.line([(width - 20, height - 20), (width - 20, height - 20 - bracket_size)], fill=color, width=bracket_width)


@bot.event
async def on_ready():
    print(f'{bot.user} has landed on the trading seas!')

    if not os.path.exists(config.BACKGROUNDS_FOLDER):
        os.makedirs(config.BACKGROUNDS_FOLDER)

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
    chain='The blockchain/native token (default: SOL)',
    theme='Card theme style (default: cyberpunk)'
)
@app_commands.choices(
    chain=[
        app_commands.Choice(name='Solana (SOL)', value='SOL'),
        app_commands.Choice(name='BNB Chain (BNB)', value='BNB'),
        app_commands.Choice(name='Ethereum (ETH)', value='ETH'),
    ],
    theme=[
        app_commands.Choice(name='Cyberpunk (Teal)', value='cyberpunk'),
        app_commands.Choice(name='JJK (Fire)', value='jjk'),
        app_commands.Choice(name='Toji (Amber)', value='toji'),
    ]
)
async def slash_pnl(interaction: discord.Interaction, username: str, coin_name: str,
                    bought_amount: float, sold_amount: float,
                    chain: app_commands.Choice[str] = None,
                    theme: app_commands.Choice[str] = None):
    """Create a PNL card with direct input"""
    try:
        await interaction.response.defer(ephemeral=True)

        chain_value = chain.value if chain else 'SOL'
        theme_value = theme.value if theme else 'cyberpunk'

        token_price = await get_token_price(chain_value)

        pnl_card = PNLCard(username, coin_name, bought_amount, sold_amount,
                          token_price, chain_value, theme_value)
        card_image = pnl_card.generate_card()

        discord_file = discord.File(card_image, filename=f"{username}_{coin_name.lower()}_pnl.png")

        embed = discord.Embed(
            title="🔒 Private Trading Report",
            description="This PNL card is only visible to you!",
            color=0x00ff00 if pnl_card.is_profit else 0xff0000
        )
        embed.add_field(name="Trader", value=username, inline=True)
        embed.add_field(name=f"{chain_value} Price", value=f"${token_price:.2f}", inline=True)
        embed.add_field(name="Multiplier", value=f"{pnl_card.multiplier:.1f}X", inline=True)

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
        description="Create custom trading reports with multiple themes!",
        color=0x00FFFF
    )

    embed.add_field(
        name="/pnl",
        value="Create a **private** custom PNL card\nParameters:\n• username: Your trader name\n• coin_name: Token traded (BONK, PEPE, etc.)\n• bought_amount: Native tokens spent\n• sold_amount: Native tokens received\n• chain: SOL, BNB, or ETH\n• theme: cyberpunk, jjk, or toji",
        inline=False
    )

    embed.add_field(
        name="Themes",
        value="🌐 **Cyberpunk** - Teal/cyan futuristic style\n🔥 **JJK** - Fire/orange retro terminal style\n✨ **Toji** - Amber/gold tunnel style",
        inline=False
    )

    embed.add_field(
        name="Features",
        value="✅ Private PNL cards (only you see them)\n✅ Multi-chain support (SOL, BNB, ETH)\n✅ Real-time price via CoinGecko\n✅ Auto multiplier calculation\n✅ Multiple themes",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name='pnl')
async def legacy_pnl(ctx):
    """Legacy command - redirect to slash command"""
    embed = discord.Embed(
        title="🔄 Command Updated!",
        description="This bot now uses **Slash Commands**!\n\nUse `/pnl` instead of `!pnl`",
        color=0xFFDD00
    )
    await ctx.send(embed=embed)


@bot.command(name='info')
async def legacy_info(ctx):
    """Legacy command - redirect to slash command"""
    embed = discord.Embed(
        title="🔄 Command Updated!",
        description="Use `/info` instead of `!info`",
        color=0xFFDD00
    )
    await ctx.send(embed=embed)


# Keep-alive web server for Replit
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def run_webserver():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("🌐 Keep-alive server running on port 8080")

@bot.event
async def on_connect():
    bot.loop.create_task(run_webserver())

if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        print("❌ Please set DISCORD_TOKEN in your .env file")
        print("💡 Create a .env file with: DISCORD_TOKEN=your_bot_token_here")
    else:
        bot.run(config.DISCORD_TOKEN)
