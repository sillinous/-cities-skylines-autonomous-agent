from cities_agent.bundle_compiler import bundle_from_compiled
from cities_agent.calibration import Calibration
from cities_agent.compiler import IntentCompiler
from cities_agent.intent import Intent, IntentKind


def test_compiled_zone_becomes_transactional_bundle():
    calibration = Calibration(1920, 1080, {"zone:residential": (0.1, 0.1)})
    compiled = IntentCompiler(calibration).compile(
        Intent(IntentKind.ZONE, target="residential", point=(100, 100), confidence=0.95)
    )
    bundle = bundle_from_compiled(compiled)
    assert bundle is not None
    assert bundle.effect.meta("phase") == "effect"
    assert bundle.preparation
