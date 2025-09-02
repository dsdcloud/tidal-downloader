import os
import subprocess
import logging
import json
import asyncio
from pyrogram import Client, filters, types

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
TIDAL_USERNAME = os.environ.get('TIDAL_USERNAME')
TIDAL_PASSWORD = os.environ.get('TIDAL_PASSWORD')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

app = Client("my_bot", bot_token=BOT_TOKEN)

async def run_command(command):
    """A helper function to run shell commands."""
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Exception(f"Command failed with exit code {proc.returncode}\n{stderr.decode()}")
    return stdout.decode()

@app.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start_command(_, message):
    await message.reply_text('Hello! I can help you download music from Tidal and upload to OneDrive. Use /download <Tidal URL> to begin.')

@app.on_message(filters.command("download") & filters.user(ADMIN_ID))
async def download_command(_, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide a Tidal URL after the command, e.g. /download <URL>')
        return

    url = message.command[1]
    
    # Ask for the Rclone destination
    await message.reply_text("Please reply with the Rclone destination (e.g., `onedrive:/Music`).")
    
    # Wait for the user's next message
    try:
        response = await app.listen(message.chat.id, timeout=60)
        rclone_destination = response.text.strip()
    except asyncio.TimeoutError:
        await message.reply_text("Timeout. Please start again with /download.")
        return

    await message.reply_text(f'Starting download for {url} and uploading to `{rclone_destination}`...')
    
    try:
        # Generate settings.json with credentials and max quality
        config_path = "settings.json"
        config_data = {
            "global": {
                "general": {
                    "download_path": "./downloads/",
                    "download_quality": "max"
                },
                "formatting": {
                    "track_filename_format": "{track_number}. {name}",
                    "album_format": "{name}{explicit}"
                },
                "covers": {
                    "embed_cover": True,
                    "save_external": False
                }
            },
            "modules": {
                "tidal": {
                    "username": TIDAL_USERNAME,
                    "password": TIDAL_PASSWORD
                }
            }
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        # Run OrpheusDL command
        download_command = ["orpheusdl", "-c", config_path, url]
        await message.reply_text(f"Running command: `{' '.join(download_command)}`")
        await run_command(download_command)

        await message.reply_text("Download completed. Starting Rclone upload...")
        
        # Determine the downloaded directory name based on the URL (this is a simple example)
        # For more complex URLs, you might need a more robust method
        download_dir_name = os.path.basename(url.strip('/'))
        local_path = os.path.join("downloads", download_dir_name)

        # Run Rclone command to sync the directory
        rclone_command = ["rclone", "sync", local_path, rclone_destination, "--verbose"]
        await message.reply_text(f"Running command: `{' '.join(rclone_command)}`")
        await run_command(rclone_command)

        await message.reply_text('Upload to OneDrive completed successfully!')

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await message.reply_text(f"An error occurred: {e}")

if __name__ == "__main__":
    if not all([BOT_TOKEN, TIDAL_USERNAME, TIDAL_PASSWORD, ADMIN_ID]):
        logger.error("Environment variables are not set. Please check your docker-compose.yml file.")
    else:
        app.run()
