class Logger:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled

    def info(self, message):
        print(f"[INFO] {message}")

    def debug(self, message):
        if self.debug_enabled:
            print(f"[DEBUG] {message}")

    def error(self, message):
        print(f"[ERROR] {message}")

    def enable_debug(self):
        self.debug_enabled = True

    def disable_debug(self):
        self.debug_enabled = False