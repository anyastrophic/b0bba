import logging
import discord
import threading
import requests


class _ColourFormatter(
    logging.Formatter
):  # thanks to https://github.com/Rapptz/discord.py/blob/master/discord/utils.py
    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[37;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f"{colour}%(levelname)-8s\x1b[32;1m%(asctime)s\x1b\x1b[0m \x1b[36m%(name)s\x1b[{colour}: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


class _DiscordColorFormatter(
    logging.Formatter
):  # thanks to https://github.com/Rapptz/discord.py/blob/master/discord/utils.py
    LEVELS = [
        (logging.DEBUG, "```bash\n", '"```', lambda text: f'"{text}"'),
        (logging.INFO, "```ini\n", "```", lambda text: f"[{text}]"),
        (logging.WARNING, "```fix\n", "```", lambda text: text),
        (logging.ERROR, "```diff\n ", "```", lambda text: f"- {text}"),
        (logging.CRITICAL, "```diff\n ", "```", lambda text: f"- {text}"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'{start_format}{formatter("%(levelname)s")}    %(asctime)s %(name)s: {formatter("%(message)s")}{end_format}',
            "%Y-%m-%d %H:%M:%S",
        )
        for level, start_format, end_format, formatter in LEVELS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = text

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


class DiscordWebhookHandler(logging.StreamHandler):
    """
    A handler class that uses a discord webhook specified in the constructor
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

        return super().__init__()

    def _send_webhook(self, message: str):
        requests.post(
            url=self.webhook_url, json={
                "content": message, "username": "B0BBA logging"}
        )

    def emit(self, record):
        try:
            t = threading.Thread(target=self._send_webhook,
                                 args=[self.format(record)])
            t.start()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class Logger:
    class Main:
        logger = logging.getLogger("b0bba.main")

        @classmethod
        def AppCommandsSynced(self):
            self.logger.info("App commands synced!")

    class Music:
        logger = logging.getLogger("b0bba.music")

        @classmethod
        def FetchingMetadataFailed(self):
            self.logger.warning("Fetching metadata failed!")

    class Payout:
        logger = logging.getLogger("b0bba.payouts")

        @classmethod
        def Success(self, manager: discord.User, target: discord.User):
            self.logger.info(
                f"Manager {manager} ({manager.id}) paid out {target} ({target.id})"
            )

        @classmethod
        def Failure(self, manager: discord.User, target: discord.User, message: str):
            self.logger.error(
                f"Manager {manager} ({manager.id}) tried to pay out {target} ({target.id}) but something went wrong. Message: {message}"
            )

    class Linking:
        logger = logging.getLogger("b0bba.linking")

        @classmethod
        def Success(self, user: discord.User, roblox_username: str, roblox_id: int):
            self.logger.info(
                f"User {user} ({user.id}) linked their ROBLOX account ({roblox_username}, {roblox_id})"
            )

        @classmethod
        def Failure(
            self, user: discord.User, roblox_username: str, roblox_id: int, message: str
        ):
            self.logger.error(
                f"User {user} ({user.id}) tried linking their ROBLOX account ({roblox_username}, {roblox_id}) but something went wrong. Message: {message}"
            )

    class RobloxMod:
        prefix = ""

        class GlobalMessage:
            logger = logging.getLogger("b0bba.robloxmod.globalmessage")

            @classmethod
            def Success(self, admin: discord.User, message: str):
                self.logger.info(
                    f"Admin {admin} ({admin.id}) posted a global message: {message}"
                )

            @classmethod
            def Failure(self, admin: discord.User, message: str, _message: str):
                self.logger.error(
                    f"Admin {admin} ({admin.id}) tried posting a global message: {message} but something went wrong. Message: {_message}"
                )

        class GameBan:
            logger = logging.getLogger("b0bba.robloxmod.globalmessage")

            @classmethod
            def Success(
                self, admin: discord.User, roblox_username: str, roblox_id: int
            ):
                self.logger.info(
                    f"Admin {admin} ({admin.id}) gamebanned a player ({roblox_username}, {roblox_id})"
                )

            @classmethod
            def Failure(
                self,
                admin: discord.User,
                roblox_username: str,
                roblox_id: int,
                message: str,
            ):
                self.logger.error(
                    f"Admin {admin} ({admin.id}) tried gamebanning a player ({roblox_username}, {roblox_id}) but something went wrong. Message: {message}"
                )

    class Reports:
        logger = logging.getLogger("b0bba.reports")

        @classmethod
        def ReportClosed(self, report_id: int, admin: discord.User) -> None:
            self.logger.info(
                f"{admin} ({admin.id}) just closed a report! Report ID: {report_id}"
            )

    class Economy:
        class Misc:
            logger = logging.getLogger("b0bba.economy.misc")

            @classmethod
            def ExchangeRatesUpdated(self, copies: int, deletes: int) -> None:
                self.logger.info(
                    f"Exchange rates updated. Copies: {copies}, Deletes: {deletes}"
                )

    class Fun:
        class Impersonate:
            logger = logging.getLogger("b0bba.fun.impersonate")

            @classmethod
            def UserImpersonated(
                self,
                user: discord.User,
                impersonated_user: discord.Member,
                message: discord.WebhookMessage,
            ):
                self.logger.info(
                    f"{user} ({user.id}) impersonated {impersonated_user.name} ({impersonated_user.id}) (under disp. name: {impersonated_user.display_name}). Message content: {message.system_content}. Message link: {message.jump_url}"
                )
