import pytest
from classes.option import Option


def test_option_price():
    option = Option(
        S=142.27,
        K=142,
        T_days=25,
        r=1.75,
        sigma=22.69,
        dividend=1.6,
        option_type='call'
    )

    expected_price = 3.51
    calculated_price = option.price

    assert pytest.approx(calculated_price, rel=1e-2) == expected_price