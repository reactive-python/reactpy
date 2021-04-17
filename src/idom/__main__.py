import warnings

from .cli import main


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter(DeprecationWarning)
        main()
