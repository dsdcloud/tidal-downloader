import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
TIDAL_USERNAME = os.environ.get('TIDAL_USERNAME')
TIDAL_PASSWORD = os.environ.get('TIDAL_PASSWORD')
RCLONE_DESTINATION = os.environ.get('RCLONE_DESTINATION')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am a bot that downloads music from Tidal and uploads it to OneDrive.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Use /download <URL> to download a Tidal track/album.')

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text('Please provide a Tidal URL after the command, e.g. /download <URL>')
        return

    url = context.args[0]
    await update.message.reply_text(f'Starting download for {url}...')

    try:
        # Create a settings.json file from environment variables
        settings_content = f'''
{{
    "global": {{
        "general": {{
            "download_path": "./downloads/",
            "download_quality": "hifi"
        }}
    }},
    "modules": {{
        "tidal": {{
            "username": "{TIDAL_USERNAME}",
            "password": "{TIDAL_PASSWORD}"
        }}
    }}
}}
'''
        with open('settings.json', 'w') as f:
            f.write(settings_content)

        # Run the OrpheusDL command
        download_command = ['orpheusdl', url]
        subprocess.run(download_command, check=True)

        await update.message.reply_text('Download completed. Starting Rclone upload...')

        # Find the downloaded directory (OrpheusDL creates a directory with the album name)
        download_dir = os.path.join("downloads", "*")
        
        # Run the Rclone command to sync the downloaded directory to OneDrive
        rclone_command = ['rclone', 'sync', download_dir, RCLONE_DESTINATION, '--verbose']
        subprocess.run(rclone_command, check=True)

        await update.message.reply_text('Upload to OneDrive completed!')

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        await update.message.reply_text(f'An error occurred: {e}')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

def main() -> None:
    """Start the bot."""
    if not all([BOT_TOKEN, TIDAL_USERNAME, TIDAL_PASSWORD, RCLONE_DESTINATION]):
        logger.error("Environment variables are not set. Please check your docker-compose.yml file.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))

    application.run_polling()

if __name__ == "__main__":
    main()
