from module import normalize_tag


def main() -> None:
    assert normalize_tag("  Urgent  ") == "urgent"


if __name__ == "__main__":
    main()
