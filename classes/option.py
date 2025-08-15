import math
from pydantic import BaseModel, Field, computed_field
from typing import Literal
from scipy.stats import norm
from math import log, exp, sqrt

try:
    from numba import njit

    @njit(cache=True, fastmath=True)
    def _phi(x):
        # CDF standardního normálu přes erf
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

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

    NUMBA_OK = True
except Exception:
    def _phi(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

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

    NUMBA_OK = False


class Option(BaseModel):
    S: float = Field(..., gt=0, description="Current price of the underlying asset (must be > 0)")
    K: float = Field(..., gt=0, description="Strike price of the option (must be > 0)")
    T_days: float = Field(..., gt=0, description="Time to expiration in days (must be > 0)")
    r: float = Field(..., ge=0, description="Risk-free interest rate in % (e.g., 5 for 5%)")
    sigma: float = Field(..., gt=0, description="Volatility in % (e.g., 20 for 20%)")
    dividend: float = Field(0.0, ge=0, description="Continuous dividend yield (annual, default is 0, must be >= 0)")
    option_type: Literal['call', 'put'] = Field(..., description="Type of option: 'call' or 'put'")

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
    }

    @computed_field
    @property
    def T(self) -> float:
        return self.T_days / 365.0

    @property
    def _r(self) -> float:
        return self.r / 100.0

    @property
    def _sigma(self) -> float:
        return self.sigma / 100.0

    @property
    def _dividend(self) -> float:
        return self.dividend / 100.0
    
    """
    def __d1(self) -> float:
        return (
            math.log(self.S / self.K)
            + (self._r - self._dividend + 0.5 * self._sigma**2) * self.T
        ) / (self._sigma * math.sqrt(self.T))

    def __d2(self) -> float:
        return self.__d1() - self._sigma * math.sqrt(self.T)

    @property
    def price(self) -> float:
        d1 = self.__d1()
        d2 = self.__d2()

        if self.option_type == 'call':
            return round(
                self.S * math.exp(-self._dividend * self.T) * norm.cdf(d1)
                - self.K * math.exp(-self._r * self.T) * norm.cdf(d2),
                2
            )
        else:  # put
            return round(
                self.K * math.exp(-self._r * self.T) * norm.cdf(-d2)
                - self.S * math.exp(-self._dividend * self.T) * norm.cdf(-d1),
                2
            )
    """
    def price(self) -> float:
        # voláme Numba-jitovanou scalar funkci
        p = bs_price_scalar(
            self.S, self.K, self.T, self._r, self._dividend, self._sigma,
            self.option_type == 'call'
        )
        return round(p, 2)