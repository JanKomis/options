import pytest
from classes.option import Option


def test_option_price():
    option = Option(
        S=142.27,
        K=142,
        T_days=25,
        r=0.0175,
        sigma=0.2269,
        dividend=0.016,
        option_type='call'
    )

    expected_price = 3.51
    calculated_price = option.price

    assert pytest.approx(calculated_price, rel=1e-2) == expected_price