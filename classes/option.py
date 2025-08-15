import math
from pydantic import BaseModel, Field, computed_field
from typing import Literal
from scipy.stats import norm

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