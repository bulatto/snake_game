class GameOverException(Exception):
    """Исключение об окончании игры."""
    def __init__(self, *args, **kwargs):
        if not args:
            args = ['Game over']
        super().__init__(*args)
