import logging
import logging.handlers
import os
import sys
import time
import traceback
from decimal import Decimal
from pprint import pprint
from queue import Queue
from typing import Optional, Union

import requests
from pythonjsonlogger import jsonlogger


_log_setup_done = False
sys_cmd = " ".join(sys.argv)
app_identifier = ""
is_production = os.environ.get("ENVIRONMENT", "production") == "production"
is_development = os.environ.get("ENVIRONMENT", "production") == "development"
IGNORE_ENVIRONMENT = True
LOG: Optional[logging.Logger] = None
APP_PATH = ""


def ignore_environment(yes=True):  # Yes is True because of BC
    global IGNORE_ENVIRONMENT
    IGNORE_ENVIRONMENT = yes


class BeatsFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        kwargs["json_ensure_ascii"] = False

        super().__init__(*args, **kwargs)

    def jsonify_log_record(self, log_record: dict):
        if log_record.get("_for_notification_only_", False) is True:
            return ""

        if "tg_parse_mode" in log_record or "tg_additional_params" in log_record:
            return ""

        if log_record.get("raw_notify", False) is True:
            return ""  # This clearly meant to be a notification

        try:
            del log_record["custom_chat_id"]
        except KeyError:
            pass

        try:
            del log_record["no_tg"]
        except KeyError:
            pass

        try:
            del log_record["_for_notification_only_"]
        except KeyError:
            pass

        for k in log_record.copy().keys():
            if isinstance(log_record[k], Decimal):
                log_record[k] = str(log_record[k])

        return super().jsonify_log_record(log_record)

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["app_id"] = app_identifier
        log_record["sys_cmd"] = sys_cmd.removeprefix("-m").strip()


class TelegramFormatter(BeatsFormatter):
    def jsonify_log_record(self, log_record):
        if log_record.get("no_tg", False) is True:
            return ""

        for k in log_record.copy().keys():
            if isinstance(log_record[k], Decimal):
                log_record[k] = str(log_record[k])

        try:
            del log_record["no_tg"]
        except KeyError:
            pass

        try:
            del log_record["_for_notification_only_"]
        except KeyError:
            pass

        output = []
        for k, v in log_record.items():
            output.append(f"{k}: {v}\n")

        return "\n".join(output)


class HttpHandler(logging.Handler):
    session = None

    def __init__(self, url, max_retry=None, delay=None, level=logging.NOTSET):
        self.url = url
        if max_retry is None or max_retry < 1:
            max_retry = 1

        if delay is None or delay < 0.2:
            delay = 0.2

        self.max_retry = max_retry
        self.delay = delay

        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        if self.formatter is None:
            return

        log_data = self.formatter.format(record)
        if not log_data:
            return

        self._send_request(record, dict(log=log_data))

    def _send_request(self, record, data) -> bool:
        if not data:
            return True

        if self.session is None:
            self.session = requests.Session()

        tried = 0
        while tried < self.max_retry:
            try:
                self.session.post(self.url, json=data, verify=False)
            except requests.RequestException:
                self.handleError(record)
                try:
                    self.session.close()
                except BaseException:
                    pass
                finally:
                    time.sleep(self.delay)
            else:
                return True

            finally:
                tried += 1

        return False


class TelegramHandler(HttpHandler):
    def __init__(
        self, chat_id, token, max_retry=None, delay=None, level=logging.NOTSET
    ):
        self.chat_id = chat_id

        super().__init__(
            f"https://api.telegram.org/bot{token}/sendMessage", max_retry, delay, level
        )

    def emit(self, record: logging.LogRecord) -> None:
        if self.formatter is None:
            return

        try:
            chat_id = record.__dict__["custom_chat_id"]
            if not chat_id:
                raise KeyError

        except KeyError:
            chat_id = self.chat_id

        else:
            del record.__dict__["custom_chat_id"]

        try:
            raw_notify = record.__dict__["raw_notify"]
        except KeyError:
            raw_notify = False

        else:
            del record.__dict__["raw_notify"]

        try:
            tg_parse_mode = record.__dict__["tg_parse_mode"]
        except KeyError:
            tg_parse_mode = None

        else:
            del record.__dict__["tg_parse_mode"]

        try:
            tg_additional_params = record.__dict__["tg_additional_params"]
            if not isinstance(tg_additional_params, dict):
                del record.__dict__["tg_additional_params"]
                raise KeyError

        except KeyError:
            tg_additional_params = dict()

        else:
            del record.__dict__["tg_additional_params"]

        if raw_notify:
            txt = record.msg
        else:
            txt = self.formatter.format(record)

        if txt == "":  # This means we need to ignore it
            return

        i = 0
        limit = 4096
        while True:
            i += 1
            if i > 1:
                time.sleep(0.1)

            end = i * limit
            start = end - limit
            partial = txt[start:end]
            if not partial:
                break

            params = {
                "chat_id": chat_id,
                "text": partial,
                "disable_web_page_preview": True,
                **tg_additional_params,
            }

            if tg_parse_mode:
                params["parse_mode"] = tg_parse_mode

            r = self._send_request(record, params)

            if not r:
                break


class CustomStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        if self.formatter is None:
            return

        try:
            msg = self.format(record)
            if msg == "":
                return
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)


def setup(
    identifier,
    log_level,
    on_exit_handler,
    app_path,
    tg_token=None,
    chat_id=None,
    beats_url=None,
    reload=False,
    additional_loggers: Optional[Union[list, tuple]] = None,
    tg_log_lvl_on_development=None,
):
    """
    Setup an elk compatible logging system
    and also

    :return:
    """
    global _log_setup_done
    global LOG
    global APP_PATH
    global app_identifier

    if _log_setup_done and reload is False:
        return LOG

    app_identifier = identifier

    if not tg_log_lvl_on_development:
        tg_log_lvl_on_development = logging.ERROR

    APP_PATH = app_path
    is_ok_for_current_env = is_production or IGNORE_ENVIRONMENT

    logger = logging.getLogger(identifier)
    logger.setLevel(log_level)

    for h in logger.handlers:
        try:
            h.close()
            logger.removeHandler(h)
        except BaseException:
            pass

    handlers = []

    if tg_token and chat_id and is_ok_for_current_env:
        tg = TelegramHandler(chat_id, tg_token)
        tg.setFormatter(TelegramFormatter())
        tg.setLevel(
            logging.CRITICAL if not is_development else tg_log_lvl_on_development
        )
        handlers.append(tg)

    if beats_url is not None and is_ok_for_current_env and beats_url:
        http = HttpHandler(beats_url)
        http.setFormatter(BeatsFormatter())
        http.setLevel(log_level)
        handlers.append(http)

    out = CustomStreamHandler()
    out.setFormatter(TelegramFormatter())
    out.setLevel(logging.WARNING if is_ok_for_current_env else logging.DEBUG)
    logger.addHandler(out)

    queue = Queue()

    ql = logging.handlers.QueueListener(queue, *handlers, respect_handler_level=True)
    ql.start()

    qh = logging.handlers.QueueHandler(queue)
    logger.addHandler(qh)

    if additional_loggers:
        for al in additional_loggers:
            _al = logging.getLogger(al)
            _al.setLevel(log_level)
            _al.addHandler(qh)

    on_exit_handler.append(ql.stop)
    on_exit_handler.append(qh.close)

    _log_setup_done = True
    LOG = logger
    return LOG


def setup_base(log_level):
    """
    Change base logging config level
    :return:
    """
    logging.basicConfig(level=log_level)


def _do_log(lvl, kind, msg, *args, stacklevel=1, **kwargs):
    """
    Actual logging func.

    if kwargs contain a key named "exc_info", then we remove it, but do include
    traceback information in log too.

    if kwargs contains key "extra", then we pass it to logging as is.
    if kwargs does not contain key "extra", we do kwargs=dict(extra=kwargs)


    :param lvl: according to logging module
    :param kind: an identity to make it easier to search logging
    :param msg: a human readable text
    :param args:
    :param stacklevel:
    :param kwargs:
    :return:
    """

    wants_exc = False
    if "exc_info" in kwargs:
        wants_exc = True
        del kwargs["exc_info"]

    if "extra" not in kwargs:
        kwargs = dict(extra=kwargs)

    kwargs["extra"]["log_kind"] = kind

    if wants_exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack = LOG.findCaller(True, stacklevel)
        if exc_type is exc_value is exc_traceback is None:
            kwargs["extra"]["exc"] = dict(
                tb=traceback.format_exc(),
                stack=stack[-1],
                name="",
                msg="",
                line=stack[1],
                fp=stack[0],
            )
        else:
            fp = exc_traceback.tb_frame.f_code.co_filename.removeprefix(str(APP_PATH))
            kwargs["extra"]["exc"] = dict(
                name=exc_type.__name__,
                msg=str(exc_value),
                line=exc_traceback.tb_lineno,
                fp=fp,
                tb=traceback.format_exc(),
                stack=stack[-1],
            )

    if not _log_setup_done:
        print("**Fallback Logging to print**")
        print("Level:", lvl)
        print("msg:", msg)
        if args:
            print("args:", end=" ", flush=True)
            pprint(args)

        if kwargs:
            print("kwargs:", end=" ", flush=True)
            pprint(kwargs)

        return

    getattr(LOG, lvl)(msg, *args, **kwargs)


def debug(kind, msg, *args, **kwargs):
    """
    Log debug messages

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    _do_log("debug", kind, msg, *args, **kwargs)


def info(kind, msg, *args, **kwargs):
    """
    Log info messages

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    _do_log("info", kind, msg, *args, **kwargs)


def warning(kind, msg, *args, **kwargs):
    """
    Log warning messages

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    _do_log("warning", kind, msg, *args, **kwargs)


def error(kind, msg, *args, **kwargs):
    """
    Log error messages

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    _do_log("error", kind, msg, *args, **kwargs)


def critical(kind, msg, *args, **kwargs):
    """
    Log critical messages

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    _do_log("critical", kind, msg, *args, **kwargs)


def exception(kind, msg, *args, **kwargs):
    """
    Log as error but include traceback information too.
    This is the same behaviour as logging module

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """
    kwargs["exc_info"] = True
    _do_log("error", kind, msg, *args, **kwargs)


def notification(kind, msg, *args, **kwargs):
    """
    Log notification.
    this means send message in telegram only

    :param kind:
    :param msg:
    :param args:
    :param kwargs:
    :return:
    """

    kwargs["_for_notification_only_"] = True
    _do_log("critical", kind, msg, *args, **kwargs)


def raw_notification(msg, chat_id=None, parse_mode=None, **tg_additional_params):
    notification(
        "",
        msg,
        custom_chat_id=chat_id,
        raw_notify=True,
        tg_parse_mode=parse_mode,
        tg_additional_params=tg_additional_params,
    )
