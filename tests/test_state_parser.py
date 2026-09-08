from cities_agent.state_parser import StateParser


class FakeOcr:
    def text(self, image):
        return ""


def test_parse_text_extracts_normalized_state_and_confidence():
    parser = StateParser(FakeOcr())
    state = parser.parse_text(
        "Money: $12,345\nPopulation 4,321\nTraffic 87.5%\n"
        "Residential Demand 62%\nCommercial Demand 31%\nIndustrial Demand 44%\n"
        "Weekly Income: $900\nWeekly Expenses: $500\nPaused\nPower OK"
    )
    assert state.money == 12345
    assert state.population == 4321
    assert state.traffic_percent == 87.5
    assert state.residential_demand == 62
    assert state.commercial_demand == 31
    assert state.industrial_demand == 44
    assert state.weekly_income == 900
    assert state.weekly_expenses == 500
    assert state.simulation_paused is True
    assert state.power_ok is True
    assert state.water_ok is None
    assert state.confidence_for("money") >= 0.70


def test_parse_text_does_not_guess_missing_values():
    state = StateParser(FakeOcr()).parse_text("Population: 100")
    assert state.population == 100
    assert state.money is None
    assert state.traffic_percent is None
    assert state.water_ok is None
    assert state.warnings == ()
