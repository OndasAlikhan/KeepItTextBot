import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, ChatMemberHandler
from dotenv import load_dotenv
from transformers import pipeline
import ffmpeg

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SERVICE_URL = os.getenv('SERVICE_URL')

pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-small",
    device=-1,
    return_timestamps=True,
)


async def transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages and transcribe them."""
    status_msg = None
    voice_path = ""
    try:
        # Get the voice message
        logger.info(update.message)
        voice = update.message.voice

        # Send a "processing" message
        status_msg = await update.message.reply_text("Transcribing voice message...")

        # Download the voice message
        voice_file = await context.bot.get_file(voice.file_id)
        voice_path = f"voice_{voice.file_id}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Transcribe using OpenAI Whisper
        result = pipe(voice_path)
        transcription_text = result["text"]

        # Delete the temporary file
        os.remove(voice_path)

        # Format the response
        user = update.message.from_user
        username = user.username if user.username else user.first_name

        response = f"@{username} said:\n\n{transcription_text}"

        # Edit the status message with the transcription
        await status_msg.edit_text(response, parse_mode='Markdown')

        logger.info(f"Successfully transcribed voice message from {username}")

    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}")
        if status_msg is not None:
            await status_msg.edit_text("Sorry, error :(", parse_mode='Markdown')
        # Clean up file if it exists
        if voice_path and os.path.exists(voice_path):
            os.remove(voice_path)


async def transcribe_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video notes (round video messages) and transcribe their audio."""
    status_msg = None
    video_path = ""
    wav_path = ""
    try:
        # Get the video note
        video_note = update.message.video_note

        # Send a "processing" message
        status_msg = await update.message.reply_text("Transcribing video...")

        # Download the video note
        video_file = await context.bot.get_file(video_note.file_id)
        video_path = f"video_note_{video_note.file_id}.mp4"
        await video_file.download_to_drive(video_path)

        # Extract audio from video and convert to WAV
        wav_path = f"video_note_{video_note.file_id}.wav"
        ffmpeg.input(video_path).output(
            wav_path,
            acodec='pcm_s16le',
            ar='16000'
        ).overwrite_output().run(quiet=True)

        # Transcribe using OpenAI Whisper
        result = pipe(wav_path)
        transcription_text = result["text"]

        # Delete the temporary file
        os.remove(video_path)
        os.remove(wav_path)

        # Format the response
        user = update.message.from_user
        username = user.username if user.username else user.first_name

        response = f"@{username} said:\n\n{transcription_text}"

        # Edit the status message with the transcription
        await status_msg.edit_text(response, parse_mode='Markdown')

        logger.info(f"Successfully transcribed video note from {username}")

    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}")
        if status_msg is not None:
            await status_msg.edit_text("Sorry, error :(", parse_mode='Markdown')
        # Clean up file if it exists
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)



# async def text_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text("test")

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers for voice messages and video notes
    # application.add_handler(MessageHandler(filters.TEXT, text_response))
    application.add_handler(MessageHandler(filters.VOICE, transcribe_voice))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, transcribe_video_note))

    # Start the bot
    logger.info("Bot started. Listening for voice messages...")
    application.run_webhook(port=8080, allowed_updates=Update.ALL_TYPES, webhook_url=SERVICE_URL)

if __name__ == '__main__':
    main()
