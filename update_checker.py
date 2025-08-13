# update_checker.py

import os
import sys
import json
import tempfile
import zipfile
import logging

from PyQt5.QtCore    import QObject, pyqtSignal, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtGui     import QDesktopServices
from constants       import __version__ as CURRENT_VERSION, SERVER_UPDATE_URL
from logging_config  import log_exceptions

logger = logging.getLogger(__name__)

class UpdateChecker(QObject):
    """
    Проверяет сначала ZIP-архив на вашем сервере,
    при неудаче — GitHub Releases.
    """
    update_downloaded = pyqtSignal(str)      # путь к папке приложения после установки
    update_available  = pyqtSignal(str, str) # (tag, html_url) для GitHub
    update_failed     = pyqtSignal(str)      # 'server' или 'github'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mgr   = QNetworkAccessManager(self)
        self._mgr.finished.connect(self._on_reply)
        self._stage = None

    @log_exceptions
    def check_for_update(self):
        """Запустить проверку: сначала сервер, потом GitHub."""
        self._stage = "server"
        req = QNetworkRequest(QUrl(SERVER_UPDATE_URL))
        self._mgr.get(req)

    @log_exceptions
    def _on_reply(self, reply):
        # === 1) Серверный ZIP ===
        if self._stage == "server":
            if reply.error():
                logger.warning("Server update unavailable, falling back to GitHub")
                self._stage = "github"
                return self._check_github()

            data = bytes(reply.readAll())
            try:
                tmpdir   = tempfile.mkdtemp(prefix="xtimer_upd_")
                url_path = reply.request().url().path()
                filename = os.path.basename(url_path) or "update.zip"
                arc_path = os.path.join(tmpdir, filename)
                with open(arc_path, "wb") as f:
                    f.write(data)

                app_dir = os.path.dirname(__file__)
                # Распаковываем только ZIP
                with zipfile.ZipFile(arc_path, "r") as z:
                    z.extractall(app_dir)

                logger.info("Server ZIP update installed into %s", app_dir)
                self.update_downloaded.emit(app_dir)

            except Exception:
                logger.exception("Failed to install update from server")
                self.update_failed.emit("server")

            return

        # === 2) GitHub Releases ===
        if self._stage == "github":
            if reply.error():
                logger.error("GitHub update check failed: %s", reply.errorString())
                self.update_failed.emit("github")
                return

            try:
                info = json.loads(bytes(reply.readAll()).decode())
                tag  = info.get("tag_name", "")
                url  = info.get("html_url", "")
                if tag and self._is_newer(tag, CURRENT_VERSION):
                    self.update_available.emit(tag, url)
                else:
                    logger.info("No newer GitHub release found (current=%s)", CURRENT_VERSION)
            except Exception:
                logger.exception("Failed to parse GitHub release info")
            return

    @log_exceptions
    def _check_github(self):
        gh_url = "https://api.github.com/repos/End1essspace/XTimer/releases/latest"
        req    = QNetworkRequest(QUrl(gh_url))
        req.setRawHeader(b"Accept", b"application/vnd.github.v3+json")
        self._mgr.get(req)

    def _is_newer(self, new: str, curr: str) -> bool:
        def parts(v):
            return [int(x) for x in v.strip("v").split(".") if x.isdigit()]
        return parts(new) > parts(curr)
