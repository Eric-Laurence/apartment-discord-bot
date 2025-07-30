# Apartment Monitor Bot

This bot watches apartment listings and pings you on Discord when something changes. It's currently set up for a specific site, but should be easily adaptable for other site structures.

## What it does

The bot scrapes apartment floor plan data every time you run it, then:
- Compares the new data with what it found last time
- Sends you a quick status update in one Discord channel 
- If anything changed, sends a full notification with a table to another channel and pings you
- If apartments become available (change from "Contact" to actual numbers), sends an urgent alert

You'll get pinged for two types of changes:
- Regular updates: Price changes, new floor plans, etc.
- Availability alerts: When apartments go from "Contact for details" to showing actual availability

## Setup

### Step 1: Create a Discord Bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application", give it a name
3. Go to "Bot" section, click "Add Bot"
4. Copy the bot token (you'll need this later)
5. Invite the bot to your Discord server with "Send Messages" permission

### Step 3: Create your .env file
Create a `.env` file with all your configuration:

```bash
# discord config
DISCORD_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_main_notification_channel_id
STATUS_CHANNEL_ID=your_status_channel_id
PING_USERS=123456789,987654321

# site config
TARGET_URL=https://your-apartment-site.com/floorplans
TARGET_XPATH=//*[@id='YourContainerID']
```

To get channel and user IDs: enable Developer Mode in Discord settings, then right-click any channel and "Copy Channel ID".

PING_USERS should be comma-separated user ids, no spaces

### Step 4: Install stuff
```bash
pip install -r requirements.txt
```

### Step 5: Test it
```bash
python run_monitor.py
```

If everything works, you should see it scrape the site and send a Discord message.

### Step 6: Run it automatically
Set up a cron job to run it every 10 minutes:

```bash
crontab -e
# Add this line:
*/10 * * * * cd /path/to/your/apartment-monitor && python3 run_monitor.py
```

## Command line options

```bash
python run_monitor.py
python run_monitor.py --complete
```

The complete flag outputs the full table, the default version is more mobile friendly.

## Want to monitor a different apartment site?

Just update the `TARGET_URL` and `TARGET_XPATH` values in your `.env` file. You will probably have to tweak the scraping logic in `crawl.py` if the site structure is different enough.

## Files in this project

- `run_monitor.py` - Main script
- `crawl.py` - Does the web scraping
- `discord_bot.py` - Sends discord messages
- `config.py` - All the settings and configuration
- `floor_plans.json` - Stores data to detect changes
- `floor_plans.md` - Human readable table for debugging

## Troubleshooting

**Bot can't send messages?**
- Make sure your bot token is correct in the `.env` file
- Check that the bot has permissions in your Discord server
- Verify the channel IDs are right

**Not finding any apartments?**
- The website might have changed - check if the URL still works
- You might need to update the `TARGET_XPATH` in `config.py`
- Make sure Chrome is installed (needed for the web scraping)
- Check if you're getting captcha'd

**Want to see what's happening?**
Just run `python run_monitor.py` in your terminal and it'll show you what it's doing.

## How it works under the hood

1. Uses Selenium to load the apartment website (with basic anti-bot detection measures)
2. Finds the floor plan container and extracts all the apartment data
3. Compares it with the last run's data stored in `floor_plans.json`
4. If there are changes, sends Discord notifications
5. Updates the stored data and creates a markdown table

The bot is slightly smart about detecting when apartments become available - it looks for when the availability changes from "Contact for details" to showing actual numbers. However, most websites will be somewhat different, so tweak based on the site you're scraping.
