import warnings
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from modes import Mode
import time

from events import (
    UserModeToggleEvent,
    UserSnoozeEvent,
    UserSettingsChangedEvent,
    UserSettingsType,
)
from users import User
from logging_config import logger
import humanize
import datetime

# Suppress InsecureRequestWarning for self-signed certificates
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class FoxRoseHandler:
    def __init__(self, state_manager, router, bot_token, config):
        self.system = state_manager
        self.router = router
        self.config = config

        self.application = Application.builder().token(bot_token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("state", self.state))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_keyboard_clicks)
        )
        self.application.add_error_handler(error_handler)

    def run(self):
        self.application.run_polling(drop_pending_updates=True)

    def build_persistent_keyboard(self, user: User) -> ReplyKeyboardMarkup:
        keyboard = []

        # 1. Row for Modes
        keyboard.append([mode.label for mode in Mode])

        # 2. Rows for Detection Notifications (Dynamic Toggles)
        notification_row = []
        for cam in self.system._cameras:
            status_emoji = "🔔" if user.has_camera_interest(cam) else "🔕"
            cam_label = cam.title()
            notification_row.append(f"{status_emoji} Notif: {cam_label}")
        keyboard.append(notification_row)

        # 3. Row for Snapshots
        keyboard.append(["📸 All Snapshots", "📷 Select Camera"])

        # 4. Row for Snooze
        snooze_label = "⏰ Unsnooze" if user.is_snoozing else "💤 Snooze All"
        keyboard.append([snooze_label, "🎯 Snooze Specific"])

        # Return ReplyKeyboardMarkup instead of Inline
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,  # Makes buttons fit neatly on screen
            one_time_keyboard=False,  # Keeps the keyboard persistent
            input_field_placeholder="Select an option below...",  # Tells them not to type
        )

    def build_snooze_duration_keyboard(self) -> ReplyKeyboardMarkup:
        keyboard = [
            ["⏳ 15 Mins", "⏳ 1 Hour"],
            ["⏳ 3 Hours", "⏳ 8 Hours"],
            ["❌ Cancel"],
        ]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,  # Automatically hides after they click one
        )

    def build_snooze_specific_keyboard(self, user: User) -> ReplyKeyboardMarkup:
        """Build a keyboard with specific event type snooze toggles."""
        keyboard = []
        # Indoor presence toggle
        indoor_status = "🔕" if user.is_event_type_snoozed("indoor_presence") else "🔔"
        keyboard.append([f"{indoor_status} Indoor Presence"])
        # Outdoor presence toggle
        outdoor_status = (
            "🔕" if user.is_event_type_snoozed("outdoor_presence") else "🔔"
        )
        keyboard.append([f"{outdoor_status} Outdoor Presence"])
        # Camera detection toggle
        camera_status = "🔕" if user.is_event_type_snoozed("camera") else "🔔"
        keyboard.append([f"{camera_status} Camera Detection"])
        # Add a back button
        keyboard.append(["🔙 Back"])
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    def build_snapshot_camera_keyboard(self) -> ReplyKeyboardMarkup:
        """Build a keyboard with camera buttons for snapshot selection."""
        keyboard = []
        # Add each camera as a button
        for cam in self.system._cameras:
            keyboard.append([f"📸 Snap: {cam.title()}"])
        # Add a back button
        keyboard.append(["🔙 Back"])
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    async def _send_snapshot_for_camera(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, camera_name: str
    ):
        """Fetch and send a snapshot for a specific camera."""
        await update.message.reply_text(f"⏳ Fetching snapshot for {camera_name}...")
        try:
            frigate_server = self.config.servers.frigate_server
            url = f"https://{frigate_server}:8971/api/{camera_name.lower()}/latest.jpg"
            response = requests.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=response.content,
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to fetch snapshot. Status: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Error fetching snapshot for {camera_name}: {e}")
            await update.message.reply_text(f"❌ Error fetching snapshot: {e}")

    async def _send_all_snapshots(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Fetch and send snapshots for all cameras."""
        for cam in self.system._cameras:
            await self._send_snapshot_for_camera(update, context, cam.title())

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(
            f"Start command received from effective user {update.effective_user.id}"
        )
        user = self.system.user_from_telegram_id(update.effective_user.id)
        logger.info(f"Start command received: {user!s} ({update.effective_user.id})")

        if not self.system.user_is_allowed(user):
            await update.message.reply_text("❌ Unauthorized access.")
            return

        await update.message.reply_text(
            "👋 Manage your Frigate notification settings:",
            reply_markup=self.build_persistent_keyboard(user),
        )

    async def state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(
            f"State command received from effective user {update.effective_user.id}"
        )
        user = self.system.user_from_telegram_id(update.effective_user.id)
        logger.info(f"State command received: {user!s} ({update.effective_user.id})")

        if not self.system.user_is_allowed(user):
            await update.message.reply_text("❌ Unauthorized access.")
            return

        camera_text = "\n".join(
            [f"- {key}: {value}" for key, value in user._camera_preferences.items()]
        )
        x = [
            f"{device} - {reading.as_emoji()}{temp} - ({round(temp - avg, 2) if avg else '--'})"
            for device, (
                _,
                temp,
            ), reading, avg in self.system._temperatures.get_latest_readings()
        ]
        temp_text = "\n".join(x)
        y = [
            f"{device_id} {humanize.naturaltime(datetime.timedelta(seconds=time.time() - timestamp))}"
            for device_id, timestamp in self.system._sensors.last_updates.items()
        ]
        temp_text1 = "\n".join(y)

        text = (
            f"🤖 *System Status for `{user!s}`*\n"
            f"🏡 Mode: `{user.mode}`\n\n"
            f"📸 *Camera Preferences:*\n"
            f"`{camera_text}\n\n`"
            f"🌡️ *Temperatures:*\n"
            f"`{temp_text}`\n\n"
            f"🌡️ *Presence:*\n"
            f"`{temp_text1}`"
        )
        # logger.info(text)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

    async def handle_keyboard_clicks(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user = self.system.user_from_telegram_id(update.effective_user.id)
        text = update.message.text

        if not self.system.user_is_allowed(user):
            await update.message.reply_text("❌ Unauthorized access.")
            return

        # --- HANDLE MODES ---
        if text in (mode.label for mode in Mode):
            mode = Mode.from_label(text)
            logger.info(f"User {user!s} set mode to {mode.display_name}")
            self.router.route_event(UserModeToggleEvent(user=user, value=mode))
            await update.message.reply_text(f"✅ Mode changed to: {mode.display_name}")
            return

        # --- HANDLE NOTIFICATION TOGGLES ---
        elif "Notif:" in text:
            # Extract camera name from string (e.g., "🔔 Notif: Achterdeur" -> "achterdeur")
            cam_title = text.split("Notif: ")[1]
            camera_to_toggle = cam_title.lower()

            # Pull preferences and invert the boolean
            new_state = not user.has_camera_interest(camera_to_toggle)
            logger.info(user.has_camera_interest(camera_to_toggle))
            self.router.route_event(
                UserSettingsChangedEvent(
                    user=user,
                    settings_type=UserSettingsType.CAMERA_PREFERENCE,
                    settings_value=camera_to_toggle,
                    value=new_state,
                )
            )

            # Update the user interface keyboard immediately with the new emoji
            await update.message.reply_text(
                f"Updated notification settings for {cam_title} to {new_state}.",
                reply_markup=self.build_persistent_keyboard(user),
            )
            return

        # --- HANDLE SNAPSHOTS ---
        elif text == "📸 All Snapshots":
            await self._send_all_snapshots(update, context)
            return

        elif text == "📷 Select Camera":
            await update.message.reply_text(
                "Select a camera to get a snapshot from:",
                reply_markup=self.build_snapshot_camera_keyboard(),
            )
            return

        elif "Snap:" in text:
            cam_title = text.split("Snap: ")[1]
            await self._send_snapshot_for_camera(update, context, cam_title)
            return

        elif text == "🔙 Back":
            await update.message.reply_text(
                "Back to main menu.",
                reply_markup=self.build_persistent_keyboard(user),
            )
            return

        elif text == "💤 Snooze All":
            await update.message.reply_text(
                "How long would you like to snooze all notifications for?",
                reply_markup=self.build_snooze_duration_keyboard(),
            )
            return

        elif text == "🎯 Snooze Specific":
            await update.message.reply_text(
                "Select which notification type to snooze:",
                reply_markup=self.build_snooze_specific_keyboard(user),
            )
            return

        # --- HANDLE SPECIFIC SNOOZE TOGGLES ---
        elif (
            "Indoor Presence" in text
            or "Outdoor Presence" in text
            or "Camera Detection" in text
        ):
            # Extract event type from button text
            if "Indoor Presence" in text:
                event_type = "indoor_presence"
            elif "Outdoor Presence" in text:
                event_type = "outdoor_presence"
            else:
                event_type = "camera"

            # Toggle the snooze state
            new_state = not user.is_event_type_snoozed(event_type)
            self.router.route_event(
                UserSettingsChangedEvent(
                    user=user,
                    settings_type=UserSettingsType.SNOOZE_SPECIFIC,
                    settings_value=event_type,
                    value=new_state,
                )
            )

            # Update the keyboard
            await update.message.reply_text(
                f"Toggled {event_type} snooze to {new_state}.",
                reply_markup=self.build_snooze_specific_keyboard(user),
            )
            return

        # User picked a duration
        elif text.startswith("⏳"):
            # Extract duration (e.g., "15 Mins" or "1 Hour")
            duration_text = text.replace("⏳ ", "")
            self.router.route_event(UserSnoozeEvent(user=user, value=duration_text))

            await update.message.reply_text(
                f"Notifications snoozed for {duration_text}.",
                reply_markup=self.build_persistent_keyboard(
                    user
                ),  # Bring back main menu
            )
            return

        # User wants to Unsnooze or Cancel
        elif text in ["⏰ Unsnooze", "❌ Cancel"]:
            self.router.route_event(UserSnoozeEvent(user=user, value=None))
            await update.message.reply_text(
                "Back to normal mode.",
                reply_markup=self.build_persistent_keyboard(user),
            )
            return


async def global_debug_inspector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts absolutely any incoming message text for verification"""
    logger.info("========================================")
    logger.info("🚨 RAW UPDATE RECEIVED!")
    logger.info(f"User Text: {update.message.text if update.message else 'No Text'}")
    logger.info(f"User Object: {update.effective_user}")
    logger.info("========================================")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs exceptions thrown inside the async worker context to trace failures"""
    logger.error(
        f"⚠️ Exception occurred inside Telegram framework core: {context.error}",
        exc_info=context.error,
    )
