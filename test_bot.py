import asyncio
from discord_bot import ApartmentBot
from config import DISCORD_TOKEN

async def test_bot():
    bot = ApartmentBot()
    
    try:
        await bot.login(DISCORD_TOKEN)
        print("Bot logged in successfully")
        
        while not bot.is_ready():
            await asyncio.sleep(0.1)
            
        print("Bot is ready - check the debug output above")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
