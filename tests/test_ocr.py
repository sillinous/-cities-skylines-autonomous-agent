from cities_agent.ocr import OcrEngine

def test_integer_parser():
    assert OcrEngine().integer("$12,345") == 12345

def test_percent_parser():
    assert OcrEngine().percent("Traffic 82.5%") == 82.5
