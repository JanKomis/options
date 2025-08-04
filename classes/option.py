import math
from pydantic import BaseModel, Field, computed_field
from typing import Literal
from scipy.stats import norm

class Option(BaseModel):
    S: float = Field(..., description="Current price of the underlying asset")
    K: float = Field(..., description="Strike price of the option")
    T_days: float = Field(..., description="Time to expiration (in days)")
    r: float = Field(..., description="Risk-free interest rate (annual)")
    sigma: float = Field(..., description="Volatility of the underlying asset (annual)")
    dividend: float = Field(0.0, description="Continuous dividend yield (annual, default is 0)")
    option_type: Literal['call', 'put'] = Field(..., description="Type of option: 'call' or 'put'")

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
    }

    @computed_field
    @property
    def T(self) -> float:
        return self.T_days / 365.0

    def __d1(self) -> float:
        return (
            math.log(self.S / self.K)
            + (self.r - self.dividend + 0.5 * self.sigma**2) * self.T
        ) / (self.sigma * math.sqrt(self.T))

    def __d2(self) -> float:
        return self.__d1() - self.sigma * math.sqrt(self.T)

    @property
    def price(self) -> float:
        d1 = self.__d1()
        d2 = self.__d2()

        if self.option_type == 'call':
            return (self.S * math.exp(-self.dividend * self.T)
            * norm.cdf(d1) - self.K * math.exp(-self.r * self.T) * norm.cdf(d2))
        else:  # put
            return (self.K * math.exp(-self.r * self.T) * norm.cdf(-d2)
                     - self.S * math.exp(-self.dividend * self.T) * norm.cdf(-d1))