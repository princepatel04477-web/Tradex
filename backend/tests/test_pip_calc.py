import pytest
from app.services.trading_service import trading_service

def test_pip_calc_standard_pair():
    # EUR/USD (4-decimal pair): 1 pip = 0.0001
    # 0.1 Lot = 10,000 units -> 10,000 * 0.0001 = $1.00 per pip
    pip_val = trading_service.calculate_pip_value("EUR_USD", lot_size=0.1, current_price=1.0850)
    assert pip_val == 1.0

    # 1.0 Lot = 100,000 units -> $10.00 per pip
    pip_val_std = trading_service.calculate_pip_value("EUR_USD", lot_size=1.0, current_price=1.0850)
    assert pip_val_std == 10.0

def test_pip_calc_jpy_pair():
    # TC-1: USD/JPY (2-decimal pair): 1 pip = 0.01
    # 0.1 Lot = 10,000 units -> (10,000 * 0.01) / 154.50 = approx $0.6472 per pip
    pip_val_jpy = trading_service.calculate_pip_value("USD_JPY", lot_size=0.1, current_price=154.50)
    expected = round((10000.0 * 0.01) / 154.50, 4)
    assert pip_val_jpy == expected
    assert pip_val_jpy != 1.0  # Must NOT be equal to standard 4-decimal pip value
