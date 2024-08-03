import threading


class ActionServerFileWatcher(threading.Thread):
    """
    Thread which starts watching files and calls the 'do_reload' method
    when a change is detected in a .py or .yaml file.
    """

    def __init__(self, dirs, do_reload):
        threading.Thread.__init__(self, name="ActionServerFileWatcher")
        self.daemon = True
        self._dirs = dirs
        self._do_reload = do_reload
        self._stop_event = threading.Event()

    def run(self):
        import os

        from watchfiles.filters import PythonFilter

        watch_dirs = [
            os.path.abspath(action_package_dir) for action_package_dir in self._dirs
        ]

        import watchfiles

        for _changes in watchfiles.watch(
            *watch_dirs,
            watch_filter=PythonFilter(extra_extensions=(".yaml",)),
            stop_event=self._stop_event,
            ignore_permission_denied=True,
        ):
            self._do_reload()

    def stop(self):
        self._stop_event.set()
