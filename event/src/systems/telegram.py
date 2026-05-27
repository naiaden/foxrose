from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import logging
import requests
from modes import Mode

from events import UserModeToggleEvent

import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

BOT_TOKEN = os.environ['BOT_TOKEN']

logger = logging.getLogger(__name__)

def send_to_telegram(chat_id, image_bytes, camera_name):
    logger.info(f"{chat_id=}, {camera_name=}")

    url =  f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"


    files = {'photo': ('snapshot.jpg', io.BytesIO(image_bytes), 'image/jpeg')}
    data = {'chat_id': chat_id, 'caption': f"Person detected on {camera_name}"}
    
    try:
        response = requests.post(url, files=files, data=data)
        logging.info(f"Sent snapshot from {camera_name}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending to Telegram: {e}")

class FoxRoseHandler:
    def __init__(self, system):
        self.system = system

        self.application = Application.builder().token(BOT_TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_keyboard_clicks))
        self.application.add_error_handler(error_handler)

    def run(self):
        self.application.run_polling(drop_pending_updates=True)

    def build_persistent_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        keyboard = []

        # 1. Row for Modes
        keyboard.append([mode.label for mode in Mode])

        # 2. Rows for Detection Notifications (Dynamic Toggles)
        notification_row = []
        for cam in self.system.camera_system.captured_cameras:
            status_emoji = "🔔" if self.system.notification_system.get_user_preference(user_id, cam) else "🔕"
            cam_label = cam.title()
            notification_row.append(f"{status_emoji} Notif: {cam_label}")
        keyboard.append(notification_row)

        # 3. Rows for Snapshots
        snapshot_row = [f"📸 Snap: {cam.title()}" for cam in self.system.camera_system.captured_cameras]
        keyboard.append(snapshot_row)

        # 4. Row for Snooze
        is_snoozed = self.system.notification_system.is_user_snoozed(user_id)
        snooze_label = "⏰ Unsnooze" if is_snoozed else "💤 Snooze Notifications"
        keyboard.append([snooze_label])


        # Return ReplyKeyboardMarkup instead of Inline
        return ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True,          # Makes buttons fit neatly on screen
            one_time_keyboard=False,       # Keeps the keyboard persistent
            input_field_placeholder="Select an option below..." # Tells them not to type
        )
 

    def build_snooze_duration_keyboard(self) -> ReplyKeyboardMarkup:
        keyboard = [
            ["⏳ 15 Mins", "⏳ 1 Hour"],
            ["⏳ 3 Hours", "⏳ 8 Hours"],
            ["❌ Cancel"]
        ]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True # Automatically hides after they click one
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(f"Start command received: {update.effective_user.username} ({update.effective_user.id})")
        user_id = update.effective_user.id

        if user_id not in self.system.allowed_users:
            await update.message.reply_text("❌ Unauthorized access.")
            return

        await update.message.reply_text(
            "👋 Manage your Frigate notification settings:",
            reply_markup=self.build_persistent_keyboard(user_id)
        )

    async def handle_keyboard_clicks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text

        if user_id not in self.system.allowed_users:
            await update.message.reply_text("❌ Unauthorized access.")
            return

        # --- HANDLE MODES ---
        if text in (mode.label for mode in Mode):
            mode = Mode.from_label(text)
            logger.info(f"User {user_id} set mode to {mode.display_name}")
            UserModeToggleEvent(user_id, mode).handle(self.system)
            await update.message.reply_text(f"✅ Mode changed to: {mode.display_name}")
            return

        # --- HANDLE NOTIFICATION TOGGLES ---
        elif "Notif:" in text:
            # Extract camera name from string (e.g., "🔔 Notif: Achterdeur" -> "achterdeur")
            cam_title = text.split("Notif: ")[1]
            camera_to_toggle = cam_title.lower()
            
            # Pull preferences and invert the boolean
            new_state = not self.system.notification_system.get_user_preference(user_id, camera_to_toggle)
            UserSettingsChangedEvent(user_id, UserSettingsType.CAMERA_PREFERENCE, camera_to_toggle, new_state).handle(self.system)

            # Update the user interface keyboard immediately with the new emoji
            await update.message.reply_text(
                f"Updated notification settings for {cam_title}.",
                reply_markup=self.build_persistent_keyboard(user_id)
            )
            return

        # --- HANDLE SNAPSHOTS ---
        elif "Snap:" in text:
            cam_title = text.split("Snap: ")[1]
            camera_target = cam_title.lower()
            
            await update.message.reply_text(f"⏳ Fetching snapshot for {cam_title}...")
            # TODO: Grab your image from Frigate API and send it:
            # await context.bot.send_photo(chat_id=user_id, photo=open('snap.jpg', 'rb'))
            return
        
        elif text == "💤 Snooze Notifications":
            await update.message.reply_text(
                "How long would you like to snooze notifications for?",
                reply_markup=self.build_snooze_duration_keyboard()
            )
            return
        
        # User picked a duration
        elif text.startswith("⏳"):
            # Extract duration (e.g., "15 Mins" or "1 Hour")
            duration_text = text.replace("⏳ ", "")
            UserSnoozeEvent(user_id, duration_text).handle(self.system)

            await update.message.reply_text(
                f"Notifications snoozed for {duration_text}.",
                reply_markup=self.build_persistent_keyboard(user_id) # Bring back main menu
            )
            return
        
        # User wants to Unsnooze or Cancel
        elif text in ["⏰ Unsnooze", "❌ Cancel"]:
            UserSnoozeEvent(user_id, None).handle(self.system)
            await update.message.reply_text(
                "Back to normal mode.",
                reply_markup=self.build_persistent_keyboard(user_id)
            )
            return

    

from telegram.ext import MessageHandler, filters

async def global_debug_inspector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts absolutely any incoming message text for verification"""
    logger.info("========================================")
    logger.info(f"🚨 RAW UPDATE RECEIVED!")
    logger.info(f"User Text: {update.message.text if update.message else 'No Text'}")
    logger.info(f"User Object: {update.effective_user}")
    logger.info("========================================")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs exceptions thrown inside the async worker context to trace failures"""
    logger.error(f"⚠️ Exception occurred inside Telegram framework core: {context.error}", exc_info=context.error)
