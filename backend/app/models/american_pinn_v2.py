from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn

from app.models.black_scholes import OptionInputs


class AmericanPutPINNV2(nn.Module):
    def __init__(
        self,
        s_max: float,
        maturity: float,
        hidden_width: int = 64,
        hidden_layers: int = 4,
    ):
        super().__init__()

        self.s_max = s_max
        self.maturity = maturity

        layers = [
            nn.Linear(2, hidden_width),
            nn.Tanh(),
        ]

        for _ in range(hidden_layers - 1):
            layers.extend(
                [
                    nn.Linear(
                        hidden_width,
                        hidden_width,
                    ),
                    nn.Tanh(),
                ]
            )

        layers.append(
            nn.Linear(
                hidden_width,
                1,
            )
        )

        self.network = nn.Sequential(
            *layers
        )

    def forward(
        self,
        spot: torch.Tensor,
        time: torch.Tensor,
    ) -> torch.Tensor:
        s_norm = (
            2.0 * spot / self.s_max
            - 1.0
        )

        t_norm = (
            2.0 * time
            / self.maturity
            - 1.0
        )

        return self.network(
            torch.cat(
                [s_norm, t_norm],
                dim=1,
            )
        )


@dataclass
class AmericanPINNV2Result:
    model: AmericanPutPINNV2
    losses: list
    final_loss: float

def value_and_operator(
    model: AmericanPutPINNV2,
    spot: torch.Tensor,
    time: torch.Tensor,
    inputs: OptionInputs,
):
    spot.requires_grad_(True)
    time.requires_grad_(True)

    value = model(
        spot,
        time,
    )

    value_t = torch.autograd.grad(
        value,
        time,
        grad_outputs=torch.ones_like(
            value
        ),
        create_graph=True,
    )[0]

    value_s = torch.autograd.grad(
        value,
        spot,
        grad_outputs=torch.ones_like(
            value
        ),
        create_graph=True,
    )[0]

    value_ss = torch.autograd.grad(
        value_s,
        spot,
        grad_outputs=torch.ones_like(
            value_s
        ),
        create_graph=True,
    )[0]

    operator = (
        value_t
        + 0.5
        * inputs.volatility**2
        * spot**2
        * value_ss
        + (
            inputs.rate
            - inputs.dividend_yield
        )
        * spot
        * value_s
        - inputs.rate
        * value
    )

    return value, operator

def fischer_burmeister(
    a: torch.Tensor,
    b: torch.Tensor,
    epsilon: float = 1e-4,
) -> torch.Tensor:
    return (
        torch.sqrt(
            a**2
            + b**2
            + epsilon**2
        )
        - a
        - b
    )

def train_american_put_pinn_v2(
    inputs: OptionInputs,
    epochs: int = 4000,
    n_interior: int = 3000,
    n_terminal: int = 1000,
    n_boundary: int = 1000,
    learning_rate: float = 1e-3,
    s_max: Optional[float] = None,
    lambda_comp: float = 10.0,
    lambda_terminal: float = 5.0,
    lambda_boundary: float = 5.0,
    seed: int = 42,
) -> AmericanPINNV2Result:

    torch.manual_seed(seed)

    if s_max is None:
        s_max = max(
            4.0 * inputs.spot,
            4.0 * inputs.strike,
        )

    model = AmericanPutPINNV2(
        s_max=s_max,
        maturity=inputs.maturity,
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    losses = []

    for epoch in range(epochs):

        spot = (
            torch.rand(
                n_interior,
                1,
            )
            * s_max
        )

        time = (
            torch.rand(
                n_interior,
                1,
            )
            * inputs.maturity
        )

        value, operator = (
            value_and_operator(
                model,
                spot,
                time,
                inputs,
            )
        )

        payoff = torch.relu(
            inputs.strike - spot
        )

        gap = value - payoff

        continuation_residual = (
            -operator
        )

        complementarity = (
            fischer_burmeister(
                gap,
                continuation_residual,
            )
        )

        comp_loss = torch.mean(
            complementarity**2
        )

        terminal_spot = (
            torch.rand(
                n_terminal,
                1,
            )
            * s_max
        )

        terminal_time = torch.full(
            (
                n_terminal,
                1,
            ),
            inputs.maturity,
        )

        terminal_prediction = model(
            terminal_spot,
            terminal_time,
        )

        terminal_target = torch.relu(
            inputs.strike
            - terminal_spot
        )

        terminal_loss = torch.mean(
            (
                terminal_prediction
                - terminal_target
            )
            ** 2
        )

        boundary_time = (
            torch.rand(
                n_boundary,
                1,
            )
            * inputs.maturity
        )

        lower_spot = torch.zeros(
            n_boundary,
            1,
        )

        upper_spot = torch.full(
            (
                n_boundary,
                1,
            ),
            s_max,
        )

        lower_prediction = model(
            lower_spot,
            boundary_time,
        )

        upper_prediction = model(
            upper_spot,
            boundary_time,
        )

        lower_target = torch.full(
            (
                n_boundary,
                1,
            ),
            inputs.strike,
        )

        upper_target = torch.zeros(
            n_boundary,
            1,
        )

        boundary_loss = (
            torch.mean(
                (
                    lower_prediction
                    - lower_target
                )
                ** 2
            )
            + torch.mean(
                (
                    upper_prediction
                    - upper_target
                )
                ** 2
            )
        )

        loss = (
            lambda_comp
            * comp_loss
            + lambda_terminal
            * terminal_loss
            + lambda_boundary
            * boundary_loss
        )

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        loss_value = float(
            loss.detach()
        )

        losses.append(
            loss_value
        )

        if (
            epoch % 200 == 0
            or epoch == epochs - 1
        ):
            print(
                f"Epoch {epoch:5d} | "
                f"Total {loss_value:.6e} | "
                f"Comp {float(comp_loss.detach()):.6e} | "
                f"TC {float(terminal_loss.detach()):.6e} | "
                f"BC {float(boundary_loss.detach()):.6e}"
            )

    return AmericanPINNV2Result(
        model=model,
        losses=losses,
        final_loss=losses[-1],
    )

def american_pinn_v2_price(
    model: AmericanPutPINNV2,
    spot: float,
    time: float = 0.0,
) -> float:
    model.eval()

    with torch.no_grad():
        value = model(
            torch.tensor(
                [[spot]],
                dtype=torch.float32,
            ),
            torch.tensor(
                [[time]],
                dtype=torch.float32,
            ),
        )

    return float(
        value.item()
    )