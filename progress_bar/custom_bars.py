from progress.bar import IncrementalBar


class ProgressBar(IncrementalBar):
    """
    My custom progress bar that:
       - Show files, uploaded to disk
    """

    suffix = '%(index)d/%(max)d --- %(file_name)s is uploaded to disk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        file_names = kwargs.get('file_names', '')
        self.file_names_iter = iter(file_names)
        self.fn = None

    @property
    def file_name(self):
        return self.fn

    def next(self, n=1):
        self.fn = next(self.file_names_iter)
        super().next(n)
