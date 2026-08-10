from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn

from app.models.black_scholes import (
    OptionInputs,
)


class AmericanPutPINN(nn.Module):
    def __init__(
        self,
        s_max: float,
        maturity: float,
        hidden_width: int = 64,
        hidden_layers: int = 3,
    ):
        super().__init__()

        self.s_max = s_max
        self.maturity = maturity

        layers = [
            nn.Linear(
                2,
                hidden_width,
            ),
            nn.Tanh(),
        ]

        for _ in range(
            hidden_layers - 1
        ):
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
            2.0
            * spot
            / self.s_max
            - 1.0
        )

        t_norm = (
            2.0
            * time
            / self.maturity
            - 1.0
        )

        x = torch.cat(
            [
                s_norm,
                t_norm,
            ],
            dim=1,
        )

        return self.network(x)


@dataclass
class AmericanPINNTrainingResult:
    model: AmericanPutPINN
    losses: list
    final_loss: float


def american_pde_residual(
    model: AmericanPutPINN,
    spot: torch.Tensor,
    time: torch.Tensor,
    rate: float,
    volatility: float,
    dividend_yield: float,
) -> torch.Tensor:

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

    return (
        value_t
        + 0.5
        * volatility**2
        * spot**2
        * value_ss
        + (
            rate
            - dividend_yield
        )
        * spot
        * value_s
        - rate
        * value
    )

def train_american_put_pinn(
    inputs: OptionInputs,
    epochs: int = 3000,
    n_interior: int = 2500,
    n_terminal: int = 750,
    n_boundary: int = 750,
    learning_rate: float = 1e-3,
    s_max: Optional[float] = None,
    lambda_pde: float = 1.0,
    lambda_obstacle: float = 10.0,
    lambda_terminal: float = 5.0,
    lambda_boundary: float = 5.0,
    seed: int = 42,
) -> AmericanPINNTrainingResult:

    torch.manual_seed(seed)

    if s_max is None:
        s_max = max(
            4.0 * inputs.spot,
            4.0 * inputs.strike,
        )

    model = AmericanPutPINN(
        s_max=s_max,
        maturity=inputs.maturity,
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    losses = []

    for epoch in range(epochs):

        # --------------------
        # Interior
        # --------------------

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

        value = model(
            spot,
            time,
        )

        residual = (
            american_pde_residual(
                model,
                spot,
                time,
                inputs.rate,
                inputs.volatility,
                inputs.dividend_yield,
            )
        )

        intrinsic = torch.relu(
            inputs.strike
            - spot
        )

        obstacle_violation = (
            torch.relu(
                intrinsic
                - value
            )
        )

        pde_loss = torch.mean(
            residual**2
        )

        obstacle_loss = torch.mean(
            obstacle_violation**2
        )

        # --------------------
        # Terminal condition
        # --------------------

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

        # --------------------
        # Boundary conditions
        # --------------------

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

        # --------------------
        # Combined loss
        # --------------------

        loss = (
            lambda_pde
            * pde_loss
            + lambda_obstacle
            * obstacle_loss
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
                f"PDE {float(pde_loss.detach()):.6e} | "
                f"Obs {float(obstacle_loss.detach()):.6e} | "
                f"TC {float(terminal_loss.detach()):.6e} | "
                f"BC {float(boundary_loss.detach()):.6e}"
            )

    return AmericanPINNTrainingResult(
        model=model,
        losses=losses,
        final_loss=losses[-1],
    )

def american_pinn_price(
    model: AmericanPutPINN,
    spot: float,
    time: float = 0.0,
) -> float:

    model.eval()

    with torch.no_grad():

        s = torch.tensor(
            [[spot]],
            dtype=torch.float32,
        )

        t = torch.tensor(
            [[time]],
            dtype=torch.float32,
        )

        value = model(
            s,
            t,
        )

    return float(
        value.item()
    )