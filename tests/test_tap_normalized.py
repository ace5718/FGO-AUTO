from fgo_auto.host.tap import normalized_to_pixels


def test_normalized_to_pixels_center() -> None:
    assert normalized_to_pixels(0.5, 0.5, 800, 600) == (400, 300)


def test_normalized_clamps() -> None:
    assert normalized_to_pixels(-0.1, 1.5, 100, 100) == (0, 100)
