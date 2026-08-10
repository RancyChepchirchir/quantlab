from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn

from app.models.black_scholes import (
    OptionInputs,
)


class BlackScholesPINN(nn.Module):
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

        spot_normalized = (
            2.0
            * spot
            / self.s_max
            - 1.0
        )

        time_normalized = (
            2.0
            * time
            / self.maturity
            - 1.0
        )

        x = torch.cat(
            [
                spot_normalized,
                time_normalized,
            ],
            dim=1,
        )

        return self.network(x)


@dataclass
class PINNTrainingResult:
    model: BlackScholesPINN
    losses: list
    final_loss: float


def pde_residual(
    model: BlackScholesPINN,
    spot: torch.Tensor,
    time: torch.Tensor,
    rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
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

    residual = (
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

    return residual

def train_european_pinn(
    inputs: OptionInputs,
    option_type: str = "call",
    epochs: int = 2000,
    n_interior: int = 2000,
    n_terminal: int = 500,
    n_boundary: int = 500,
    learning_rate: float = 1e-3,
    s_max: Optional[float] = None,
    seed: int = 42,
) -> PINNTrainingResult:

    if option_type not in {
        "call",
        "put",
    }:
        raise ValueError(
            "option_type must be "
            "'call' or 'put'"
        )

    torch.manual_seed(seed)

    if s_max is None:
        s_max = max(
            4.0 * inputs.spot,
            4.0 * inputs.strike,
        )

    model = BlackScholesPINN(
        s_max=s_max,
        maturity=inputs.maturity,
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    losses = []

    for epoch in range(epochs):

        # -----------------------
        # Interior collocation
        # -----------------------

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

        residual = pde_residual(
            model,
            spot,
            time,
            inputs.rate,
            inputs.volatility,
            inputs.dividend_yield,
        )

        pde_loss = torch.mean(
            residual**2
        )

        # -----------------------
        # Terminal condition
        # -----------------------

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

        if option_type == "call":
            terminal_target = torch.relu(
                terminal_spot
                - inputs.strike
            )
        else:
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

        # -----------------------
        # Boundary conditions
        # -----------------------

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

        tau = (
            inputs.maturity
            - boundary_time
        )

        if option_type == "call":

            lower_target = (
                torch.zeros_like(
                    boundary_time
                )
            )

            upper_target = (
                s_max
                * torch.exp(
                    -inputs.dividend_yield
                    * tau
                )
                - inputs.strike
                * torch.exp(
                    -inputs.rate
                    * tau
                )
            )

        else:

            lower_target = (
                inputs.strike
                * torch.exp(
                    -inputs.rate
                    * tau
                )
            )

            upper_target = (
                torch.zeros_like(
                    boundary_time
                )
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

        # -----------------------
        # Combined PINN loss
        # -----------------------

        loss = (
            pde_loss
            + terminal_loss
            + boundary_loss
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
                f"Terminal {float(terminal_loss.detach()):.6e} | "
                f"Boundary {float(boundary_loss.detach()):.6e}"
            )

    return PINNTrainingResult(
        model=model,
        losses=losses,
        final_loss=losses[-1],
    )


def pinn_price(
    model: BlackScholesPINN,
    spot: float,
    time: float = 0.0,
) -> float:

    model.eval()

    with torch.no_grad():

        spot_tensor = torch.tensor(
            [[spot]],
            dtype=torch.float32,
        )

        time_tensor = torch.tensor(
            [[time]],
            dtype=torch.float32,
        )

        prediction = model(
            spot_tensor,
            time_tensor,
        )

    return float(
        prediction.item()
    )