import sys

from docs_app import dev, prod

if __name__ == "__main__":
    if len(sys.argv) == 1:
        prod.main()
    else:
        dev.main()
