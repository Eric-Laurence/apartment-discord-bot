import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from config import DISCORD_TOKEN, DISCORD_CHANNEL_ID, STATUS_CHANNEL_ID, PING_USERS

class ApartmentBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def on_ready(self):
        print(f'Bot logged in as {self.user}')
        print(f'Bot is in {len(self.guilds)} guilds')
        for guild in self.guilds:
            print(f'  - {guild.name} (ID: {guild.id})')
            if guild.id == 996300166606901339:
                print(f'    Found target server! Channels: {len(guild.channels)}')
                for channel in guild.channels:
                    if channel.id == DISCORD_CHANNEL_ID:
                        print(f'    Found target channel: {channel.name}')

    async def send_apartment_update(self, floor_plans, changes_detected, availability_opened=False, complete_table=False):
        try:
            # status message
            status_channel = await self.fetch_channel(STATUS_CHANNEL_ID)
            if status_channel:
                if changes_detected:
                    if availability_opened:
                        status_msg = "🚨 Check completed - APARTMENT AVAILABLE!"
                    else:
                        status_msg = "🏠 Check completed - Changes detected"
                else:
                    status_msg = "✅ Check completed - No changes detected"
                
                await status_channel.send(status_msg)
            
            if not changes_detected:
                print("No changes detected - only sent status message")
                return
            
            channel = await self.fetch_channel(DISCORD_CHANNEL_ID)
            if not channel:
                print(f"Could not access channel with ID {DISCORD_CHANNEL_ID}")
                return

            embed = discord.Embed(
                title="🏠 Apartment Update Detected!",
                description="Floor plan changes found at Ariel Court Apartments",
                color=0xff6b35,
                timestamp=datetime.now()
            )

            if floor_plans:
                rents = [int(''.join(filter(str.isdigit, plan.get('rent', '$0')))) for plan in floor_plans if plan.get('rent')]
                min_rent = min(rents) if rents else 0
                max_rent = max(rents) if rents else 0
                
                embed.add_field(
                    name="📊 Summary",
                    value=f"**{len(floor_plans)}** plans available\n**${min_rent:,} - ${max_rent:,}** price range",
                    inline=False
                )

                rows = []
                
                if complete_table:
                    col_widths = [4, 3, 4, 4, 4, 4]
                    headers = ['Plan', 'Type', 'Bath', 'SqFt', 'Rent', 'Avail']
                    
                    for plan in floor_plans:
                        name = plan.get('name', '')[:10]
                        plan_type = 'Studio' if plan.get('bedrooms') == 'Studio' else '1BR'
                        bath = plan.get('bathrooms', '1')
                        sqft = plan.get('sqft', '—')
                        rent = plan.get('rent', '—').replace('$', '').replace(',', '')
                        availability = plan.get('availability', 'Contact')
                        if 'contact' in availability.lower():
                            availability = 'Contact'
                        elif availability.lower().startswith('availability'):
                            availability = availability.replace('Availability', '').strip()
                        
                        row = [name, plan_type, bath, sqft, f"${rent}", availability]
                        rows.append(row)
                        
                        for i, cell in enumerate(row):
                            col_widths[i] = max(col_widths[i], len(str(cell)))
                else:
                    # compact table
                    col_widths = [4, 4, 4, 4]
                    headers = ['Plan', 'SqFt', 'Rent', 'Avail']
                    
                    for plan in floor_plans:
                        name = plan.get('name', '')[:10]
                        sqft = plan.get('sqft', '—')
                        rent = plan.get('rent', '—').replace('$', '').replace(',', '')
                        availability = plan.get('availability', 'Contact')
                        if 'contact' in availability.lower():
                            availability = 'Contact'
                        elif availability.lower().startswith('availability'):
                            availability = availability.replace('Availability', '').strip()
                        
                        row = [name, sqft, f"${rent}", availability]
                        rows.append(row)
                        
                        for i, cell in enumerate(row):
                            col_widths[i] = max(col_widths[i], len(str(cell)))
                table_text = "```\n"
                
                # construct table
                header_row = ""
                for i, header in enumerate(headers):
                    header_row += f"{header:<{col_widths[i]}} "
                table_text += header_row.rstrip() + "\n"
                
                sep_row = ""
                for width in col_widths:
                    sep_row += "─" * width + " "
                table_text += sep_row.rstrip() + "\n"
                
                for row in rows:
                    data_row = ""
                    for i, cell in enumerate(row):
                        data_row += f"{str(cell):<{col_widths[i]}} "
                    table_text += data_row.rstrip() + "\n"
                
                table_text += "```"
                
                embed.add_field(
                    name="📋 Current Floor Plans",
                    value=table_text,
                    inline=False
                )

            user_pings = " ".join([f"<@{user_id}>" for user_id in PING_USERS])
            if availability_opened:
                message_content = f"🚨 **APARTMENT AVAILABLE!** {user_pings}"
            else:
                message_content = f"🏠 **Apartment Update** {user_pings}"
            
            await channel.send(content=message_content, embed=embed)
            
            print(f"Sent notification to channel {channel.name}")
            
        except Exception as e:
            print(f"Error sending Discord message: {e}")

async def send_notification(floor_plans, changes_detected, availability_opened=False, complete_table=False):
    bot = ApartmentBot()
    
    try:
        await bot.login(DISCORD_TOKEN)
        await bot.send_apartment_update(floor_plans, changes_detected, availability_opened, complete_table)
    except Exception as e:
        print(f"Discord bot error: {e}")
    finally:
        await bot.close()
