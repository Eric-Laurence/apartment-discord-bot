import asyncio
import sys
import argparse
from crawl import crawl_apartments
from discord_bot import send_notification

def main():
    parser = argparse.ArgumentParser(description='Monitor apartment floor plans')
    parser.add_argument('--complete', action='store_true', 
                       help='Show complete table with all columns (Type and Bath)')
    args = parser.parse_args()
    
    try:
        floor_plans, has_changes, availability_opened = crawl_apartments()
        
        if floor_plans:
            print(f"Found {len(floor_plans)} floor plans")
            if availability_opened:
                print("APARTMENT AVAILABLE - sending urgent notification")
            elif has_changes:
                print("Changes detected - sending Discord notification")
            else:
                print("No changes detected")
                
            asyncio.run(send_notification(floor_plans, has_changes, availability_opened, args.complete))
        else:
            print("Error: No floor plans found")
            sys.exit(1)
            
    except Exception as e:
        print(f"Monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
