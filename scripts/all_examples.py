import sys
from pathlib import Path
from traceback import print_exc

import idom
from idom.server.sanic import PerClientStateServer


here = Path(__file__).parent
examples_dir = here.parent / "docs" / "source" / "examples"
sys.path.insert(0, str(examples_dir))

for file in examples_dir.iterdir():
    if not file.is_file() or not file.suffix == ".py" or file.stem.startswith("_"):
        continue


def main():
    views = []

    for example_file in examples_dir.glob("*.py"):
        if not example_file.stem.startswith("_"):
            with example_file.open() as f_obj:
                try:
                    idom.run = lambda func: views.append((example_file.stem, func))
                    exec(
                        f_obj.read(),
                        {
                            "__file__": str(file),
                            "__name__": f"__main__.examples.{file.stem}",
                        },
                    )
                except Exception:
                    print(f"Failed to load {example_file}")
                    print_exc()
                    print()

    @idom.component
    def AllExamples():
        examples = []
        for title, func in views:
            examples.append(idom.html.h1(title))
            examples.append(func())
            examples.append(idom.html.hr({"style": {"margin-top": "20px"}}))
        return idom.html.div({"style": {"margin": "20px"}}, examples)

    PerClientStateServer(AllExamples).run("127.0.0.1", 5000)


if __name__ == "__main__":
    main()
