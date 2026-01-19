#!/usr/bin/env python3
"""
Test script for PNL card generation
This script allows you to test card generation without setting up Discord
"""

import os
import sys
from PIL import Image

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot import PNLCard, SUPPORTED_CHAINS
    import config
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("💡 Make sure you have installed all dependencies with: pip install -r requirements.txt")
    sys.exit(1)

def get_token_price_sync(chain: str = 'SOL'):
    """Get token price synchronously for testing"""
    import requests
    chain_info = SUPPORTED_CHAINS.get(chain.upper(), SUPPORTED_CHAINS['SOL'])
    token_id = chain_info['id']
    fallback_price = chain_info['fallback_price']

    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd')
        if response.status_code == 200:
            return response.json()[token_id]['usd']
        return fallback_price
    except:
        return fallback_price

def generate_sample_cards():
    """Generate sample PNL cards for testing"""

    # Sample trading data with different chains
    samples = [
        {
            'name': 'sol_profit',
            'username': 'CryptoHawk',
            'coin_name': 'BONK',
            'chain': 'SOL',
            'bought': 10.0,
            'sold': 15.0,
            'description': 'Profitable SOL trade'
        },
        {
            'name': 'sol_loss',
            'username': 'DiamondHands',
            'coin_name': 'WIF',
            'chain': 'SOL',
            'bought': 20.0,
            'sold': 12.0,
            'description': 'Loss-making SOL trade'
        },
        {
            'name': 'bnb_trade',
            'username': 'BNBWhale',
            'coin_name': 'PEPE',
            'chain': 'BNB',
            'bought': 5.0,
            'sold': 8.0,
            'description': 'BNB chain trade'
        }
    ]

    print("🎨 Generating sample PNL cards...")
    print("=" * 50)

    for i, sample in enumerate(samples, 1):
        try:
            chain = sample['chain']
            token_price = get_token_price_sync(chain)
            print(f"({i}/{len(samples)}) Creating {sample['description']}... ({chain} @ ${token_price:.2f})")

            # Create PNL card with custom background
            background_path = None
            if os.path.exists(config.BACKGROUNDS_FOLDER):
                for file in os.listdir(config.BACKGROUNDS_FOLDER):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')) and not file.startswith('.'):
                        background_path = f"{config.BACKGROUNDS_FOLDER}/{file}"
                        break

            pnl_card = PNLCard(
                username=sample['username'],
                coin_name=sample['coin_name'],
                bought_amount=sample['bought'],
                sold_amount=sample['sold'],
                token_price=token_price,
                chain=chain,
                background_path=background_path
            )
            
            # Generate the card image
            card_image = pnl_card.generate_card()

            # Save to file
            filename = f"sample_{sample['name']}.png"
            with open(filename, 'wb') as f:
                f.write(card_image.getvalue())

            # Display trade info
            print(f"   👤 User: {sample['username']}")
            print(f"   📊 {chain}: {sample['bought']:.1f} spent → {sample['sold']:.1f} received")
            # Format amount with K if >= 1000
            pnl_abs = abs(pnl_card.pnl_amount)
            pnl_formatted = f"{pnl_abs/1000:.1f}K" if pnl_abs >= 1000 else f"{pnl_abs:.1f}"
            # Format USD amount with K if >= 1000
            pnl_usd_abs = abs(pnl_card.pnl_usd)
            pnl_usd_formatted = f"{pnl_usd_abs/1000:.1f}K" if pnl_usd_abs >= 1000 else f"{pnl_usd_abs:.2f}"
            print(f"   💰 P&L: {'+' if pnl_card.is_profit else '-'}{pnl_formatted} {chain} (${pnl_usd_formatted})")
            print(f"   💾 Saved as: {filename}")
            print()

        except Exception as e:
            print(f"   ❌ Error creating {sample['description']}: {e}")
            print()

    print("✅ Sample generation complete!")
    print(f"📁 Check the current directory for sample_*.png files")

def test_custom_card():
    """Allow user to create a custom test card"""
    print("\n🎯 Create Your Own Test Card")
    print("-" * 40)

    try:
        # Get chain selection
        print("Available chains: SOL, BNB, ETH")
        chain = input("⛓️ Enter chain (default: SOL): ").strip().upper()
        if chain not in SUPPORTED_CHAINS:
            chain = 'SOL'

        token_price = get_token_price_sync(chain)
        print(f"🚀 Current {chain} price: ${token_price:.2f}")

        username = input("👤 Enter username (e.g., CryptoMaster): ").strip()
        if not username:
            username = "TestTrader"

        coin_name = input("🪙 Enter token name (e.g., BONK, PEPE): ").strip()
        if not coin_name:
            coin_name = "TOKEN"

        bought = input(f"💰 Enter {chain} spent (e.g., 50): ").strip()
        bought = float(bought) if bought else 50.0

        sold = input(f"💸 Enter {chain} received (e.g., 60): ").strip()
        sold = float(sold) if sold else 60.0

        print(f"\n🎨 Creating {username}'s {coin_name.upper()} PNL card on {chain}...")

        # Create and generate card with custom background
        background_path = None
        if os.path.exists(config.BACKGROUNDS_FOLDER):
            for file in os.listdir(config.BACKGROUNDS_FOLDER):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')) and not file.startswith('.'):
                    background_path = f"{config.BACKGROUNDS_FOLDER}/{file}"
                    break

        pnl_card = PNLCard(username, coin_name, bought, sold, token_price, chain, background_path)
        card_image = pnl_card.generate_card()

        # Save the card
        filename = f"custom_{username.lower()}_{coin_name.lower()}_pnl.png"
        with open(filename, 'wb') as f:
            f.write(card_image.getvalue())

        print(f"✅ Custom card created: {filename}")
        # Format amount with K if >= 1000
        pnl_abs = abs(pnl_card.pnl_amount)
        pnl_formatted = f"{pnl_abs/1000:.1f}K" if pnl_abs >= 1000 else f"{pnl_abs:.1f}"
        # Format USD amount with K if >= 1000
        pnl_usd_abs = abs(pnl_card.pnl_usd)
        pnl_usd_formatted = f"{pnl_usd_abs/1000:.1f}K" if pnl_usd_abs >= 1000 else f"{pnl_usd_abs:.2f}"
        print(f"📊 P&L: {'+' if pnl_card.is_profit else '-'}{pnl_formatted} {chain} (${pnl_usd_formatted})")

    except ValueError:
        print("❌ Invalid input. Please use numbers for amounts.")
    except KeyboardInterrupt:
        print("\n🛑 Cancelled by user")
    except Exception as e:
        print(f"❌ Error creating custom card: {e}")

def main():
    print("🚀 Custom PNL Card Generation Test")
    print("=" * 45)
    print("Generate cyberpunk-style trading reports with custom backgrounds!")
    
    while True:
        print("\nChoose an option:")
        print("1. Generate sample cards (3 examples)")
        print("2. Create custom test card")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            generate_sample_cards()
        elif choice == '2':
            test_custom_card()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 