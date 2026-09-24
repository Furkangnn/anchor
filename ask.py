import sys

from anchor.chain import build_chain


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "When is a missed pickup refunded?"
    print(build_chain().invoke(question))


if __name__ == "__main__":
    main()
