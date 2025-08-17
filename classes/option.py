import math
import numpy as np
from pydantic import BaseModel, Field, computed_field
from typing import Literal
from numba import njit

# =========================
# Helper BS functions (Numba)
# =========================

@njit(cache=True, fastmath=True)
def _phi(x):
    # Standard normal CDF using erf (Numba-compatible)
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

@njit(cache=True, fastmath=True)
def _norm_pdf(x):
    # Standard normal PDF
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

@njit(cache=True, fastmath=True)
def bs_price_scalar(S, K, T, r, q, sig, is_call):
    sqrtT = math.sqrt(T)
    sigsqrt = sig * sqrtT
    inv_sigsqrt = 1.0 / sigsqrt

    d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) * inv_sigsqrt
    d2 = d1 - sigsqrt

    e_qT = math.exp(-q * T)
    e_rT = math.exp(-r * T)

    if is_call:
        return S * e_qT * _phi(d1) - K * e_rT * _phi(d2)
    else:
        return K * e_rT * _phi(-d2) - S * e_qT * _phi(-d1)

@njit(cache=True, fastmath=True)
def bs_price_strikes(S, T, r, q, sig, is_call, K_arr):
    """
    Black–Scholes prices for an array of strikes K_arr (numpy array).
    The returned ndarray has the same length as K_arr.
    """
    n = K_arr.size
    out = np.empty(n, dtype=np.float64)

    sqrtT = math.sqrt(T)
    sigsqrt = sig * sqrtT
    inv_sigsqrt = 1.0 / sigsqrt

    e_qT = math.exp(-q * T)
    e_rT = math.exp(-r * T)

    for i in range(n):
        K = K_arr[i]
        d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) * inv_sigsqrt
        d2 = d1 - sigsqrt
        if is_call:
            out[i] = S * e_qT * _phi(d1) - K * e_rT * _phi(d2)
        else:
            out[i] = K * e_rT * _phi(-d2) - S * e_qT * _phi(-d1)
    return out

@njit(cache=True, fastmath=True)
def bs_greeks_scalar(S, K, T, r, q, sig, is_call):
    """
    Returns (delta, gamma, theta_daily, vega_per_1pct, rho_per_1pct)

    - theta_daily: **daily** theta (annual theta / 365). Negative = time decay.
    - vega_per_1pct: price change for a 1 percentage point (1%) change in volatility.
    - rho_per_1pct: price change for a 1 percentage point (1%) change in risk-free rate.
    """
    sqrtT = math.sqrt(T)
    sigsqrt = sig * sqrtT
    inv_sigsqrt = 1.0 / sigsqrt

    d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) * inv_sigsqrt
    d2 = d1 - sigsqrt

    e_qT = math.exp(-q * T)
    e_rT = math.exp(-r * T)

    pdf_d1 = _norm_pdf(d1)

    # Delta
    if is_call:
        delta = e_qT * _phi(d1)
    else:
        delta = -e_qT * _phi(-d1)

    # Gamma (same for call and put)
    gamma = e_qT * pdf_d1 / (S * sig * sqrtT)

    # Theta (annual -> daily)
    if is_call:
        theta_annual = (-e_qT * pdf_d1 * sig / (2.0 * sqrtT)) + q * e_qT * _phi(d1) - r * e_rT * K * _phi(d2)
    else:
        theta_annual = (-e_qT * pdf_d1 * sig / (2.0 * sqrtT)) - q * e_qT * _phi(-d1) + r * e_rT * K * _phi(-d2)
    theta_daily = theta_annual / 365.0

    # Vega: per 1 percentage point
    vega_raw = S * e_qT * pdf_d1 * sqrtT   # for 1.00 (100%) change in σ
    vega_per_1pct = vega_raw / 100.0       # for 1%

    # Rho: per 1 percentage point
    if is_call:
        rho_raw = K * T * e_rT * _phi(d2)  # for 1.00 (100%) change in r
    else:
        rho_raw = -K * T * e_rT * _phi(-d2)
    rho_per_1pct = rho_raw / 100.0         # for 1%

    return delta, gamma, theta_daily, vega_per_1pct, rho_per_1pct


@njit(cache=True, fastmath=True)
def bs_greeks_strikes(S, T, r, q, sig, is_call, K_arr):
    """
    Vectorized Greeks for an array of strikes.
    Returns 5 ndarrays: (delta, gamma, theta_daily, vega_per_1pct, rho_per_1pct)
    """
    n = K_arr.size
    delta_out  = np.empty(n, dtype=np.float64)
    gamma_out  = np.empty(n, dtype=np.float64)
    theta_out  = np.empty(n, dtype=np.float64)  # daily
    vega_out   = np.empty(n, dtype=np.float64)  # per 1%
    rho_out    = np.empty(n, dtype=np.float64)  # per 1%

    sqrtT = math.sqrt(T)
    sigsqrt = sig * sqrtT
    inv_sigsqrt = 1.0 / sigsqrt

    e_qT = math.exp(-q * T)
    e_rT = math.exp(-r * T)

    for i in range(n):
        K = K_arr[i]

        d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) * inv_sigsqrt
        d2 = d1 - sigsqrt

        pdf_d1 = _norm_pdf(d1)

        # Delta
        if is_call:
            delta = e_qT * _phi(d1)
        else:
            delta = -e_qT * _phi(-d1)
        delta_out[i] = delta

        # Gamma (same for call & put)
        gamma = e_qT * pdf_d1 / (S * sig * sqrtT)
        gamma_out[i] = gamma

        # Theta (annual -> daily)
        if is_call:
            theta_annual = (-e_qT * pdf_d1 * sig / (2.0 * sqrtT)) + q * e_qT * _phi(d1) - r * e_rT * K * _phi(d2)
        else:
            theta_annual = (-e_qT * pdf_d1 * sig / (2.0 * sqrtT)) - q * e_qT * _phi(-d1) + r * e_rT * K * _phi(-d2)
        theta_out[i] = theta_annual / 365.0

        # Vega: per 1 percentage point
        vega_raw = S * e_qT * pdf_d1 * sqrtT
        vega_out[i] = vega_raw / 100.0

        # Rho: per 1 percentage point
        if is_call:
            rho_raw = K * T * e_rT * _phi(d2)
        else:
            rho_raw = -K * T * e_rT * _phi(-d2)
        rho_out[i] = rho_raw / 100.0

    return delta_out, gamma_out, theta_out, vega_out, rho_out


# =========================
# Option class (Pydantic v2)
# =========================

class Option(BaseModel):
    S: float = Field(..., gt=0, description="Current price of the underlying asset (must be > 0)")
    K: float = Field(..., gt=0, description="Strike price of the option (must be > 0)")
    T_days: float = Field(..., gt=0, description="Time to expiration in days (must be > 0)")
    r: float = Field(..., ge=0, description="Risk-free interest rate in % (e.g., 5 for 5%)")
    sigma: float = Field(..., gt=0, description="Volatility in % (e.g., 20 for 20%)")
    dividend: float = Field(0.0, ge=0, description="Continuous dividend yield in % (annual, >= 0)")
    option_type: Literal['call', 'put'] = Field(..., description="Type of option: 'call' or 'put'")

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
    }

    @computed_field
    @property
    def T(self) -> float:
        # convert days to years
        return self.T_days / 365.0

    @property
    def _r(self) -> float:
        # internal decimal format
        return self.r / 100.0

    @property
    def _sigma(self) -> float:
        return self.sigma / 100.0

    @property
    def _dividend(self) -> float:
        return self.dividend / 100.0

    # -------------
    # Option price
    # -------------
    def price(self) -> float:
        p = bs_price_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(p, 2)

    def price_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        """
        Takes a list/ndarray of strikes and returns an ndarray of prices (rounded to 2 decimals).
        """
        K_arr = np.asarray(strikes, dtype=np.float64)
        prices = bs_price_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(prices, 2)

    # -------------
    # Greeks (scalar)
    # -------------
    def delta(self) -> float:
        d, _, _, _, _ = bs_greeks_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(d, 6)

    def gamma(self) -> float:
        _, g, _, _, _ = bs_greeks_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(g, 6)

    def theta(self) -> float:
        """
        Daily Theta (directly returned from bs_greeks_scalar).
        Negative value = time decay.
        """
        _, _, th_daily, _, _ = bs_greeks_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(th_daily, 6)

    def vega(self) -> float:
        """
        Vega: price change for a 1 percentage point (1%) change in volatility.
        """
        _, _, _, v, _ = bs_greeks_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(v, 6)

    def rho(self) -> float:
        """
        Rho: price change for a 1 percentage point (1%) change in the risk-free rate r.
        """
        _, _, _, _, r_ = bs_greeks_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(r_, 6)

    # -------------
    # Greeks for arrays of strikes
    # -------------
    def delta_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        K_arr = np.asarray(strikes, dtype=np.float64)
        d, _, _, _, _ = bs_greeks_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(d, 6)

    def gamma_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        K_arr = np.asarray(strikes, dtype=np.float64)
        _, g, _, _, _ = bs_greeks_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(g, 6)

    def theta_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        """
        Daily theta for each strike (negative = time decay).
        """
        K_arr = np.asarray(strikes, dtype=np.float64)
        _, _, th, _, _ = bs_greeks_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(th, 6)

    def vega_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        """
        Vega per 1 percentage point change in volatility.
        """
        K_arr = np.asarray(strikes, dtype=np.float64)
        _, _, _, v, _ = bs_greeks_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(v, 6)

    def rho_for_strikes(self, strikes: np.ndarray) -> np.ndarray:
        """
        Rho per 1 percentage point change in the risk-free rate.
        """
        K_arr = np.asarray(strikes, dtype=np.float64)
        _, _, _, _, r_ = bs_greeks_strikes(
            self.S, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call', K_arr
        )
        return np.round(r_, 6)