import sys
import logging
from logging.handlers import RotatingFileHandler
from sync_clip.utils.util_path import get_log_path


def set_scripts_logging(_file_, logger=None, level=logging.DEBUG,
                        console_log=True, file_log=True, file_mode="w"):
    """
        为了是脚本log安装正确，请把此函数的调用放在脚本的最上面， 例：
            from commons import set_scripts_logging
            set_scripts_logging(__file__)

            import logging
            import ..others..

    @_file_:
    @level:
    @return:
    """
    log_filename = get_log_path(_file_)
    if logger is None:
        logger = logging.getLogger()
    # 解除第三方 logger 广播日志
    for log_name, _log in logger.manager.loggerDict.items():
        if (isinstance(_log, logging.Logger)
                and log_name != logger.name
                and _log.parent.name == logger.name):
            _log.propagate = False
    if logger.handlers:  # 防止有多个 handler
        logger.handlers.clear()
    if console_log:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s "
                              "%(message)s"))
        logger.addHandler(console_handler)

    if file_log:
        file_handler = logging.FileHandler(filename=log_filename,
                                           mode=file_mode)
        file_handler.setFormatter(logging.Formatter(
            ("%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s")
        ))

        logger.addHandler(file_handler)

    logger.setLevel(level=level)
    logger.info("Log_filename: {}".format(log_filename))
    return log_filename


if __name__ == "__main__":
    test_logger = logging.getLogger("test")
    set_scripts_logging(__file__, logger=test_logger)
