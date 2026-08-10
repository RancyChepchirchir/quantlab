from dataclasses import dataclass

import torch
from torch import nn


class MLP(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        hidden_layers: int = 3,
    ):
        super().__init__()

        layers = [
            nn.Linear(
                input_dim,
                hidden_dim,
            ),
            nn.Tanh(),
        ]

        for _ in range(
            hidden_layers - 1
        ):
            layers.extend(
                [
                    nn.Linear(
                        hidden_dim,
                        hidden_dim,
                    ),
                    nn.Tanh(),
                ]
            )

        layers.append(
            nn.Linear(
                hidden_dim,
                output_dim,
            )
        )

        self.net = nn.Sequential(
            *layers
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        return self.net(x)


class DeepONet(nn.Module):
    def __init__(
        self,
        branch_dim: int = 5,
        trunk_dim: int = 2,
        latent_dim: int = 64,
        hidden_dim: int = 64,
    ):
        super().__init__()

        self.branch = MLP(
            branch_dim,
            hidden_dim,
            latent_dim,
        )

        self.trunk = MLP(
            trunk_dim,
            hidden_dim,
            latent_dim,
        )

        self.bias = nn.Parameter(
            torch.zeros(1)
        )

    def forward(
        self,
        branch_input:
            torch.Tensor,
        trunk_input:
            torch.Tensor,
    ) -> torch.Tensor:

        branch_features = (
            self.branch(
                branch_input
            )
        )

        trunk_features = (
            self.trunk(
                trunk_input
            )
        )

        output = torch.sum(
            branch_features
            * trunk_features,
            dim=1,
            keepdim=True,
        )

        return (
            output
            + self.bias
        )


@dataclass
class DeepONetTrainingResult:
    model: DeepONet
    losses: list
    final_loss: float
    

def train_deeponet(
    branch_inputs,
    trunk_inputs,
    targets,
    epochs: int = 2000,
    batch_size: int = 1024,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> DeepONetTrainingResult:

    torch.manual_seed(seed)

    branch_tensor = torch.tensor(
        branch_inputs,
        dtype=torch.float32,
    )

    trunk_tensor = torch.tensor(
        trunk_inputs,
        dtype=torch.float32,
    )

    target_tensor = torch.tensor(
        targets,
        dtype=torch.float32,
    )

    model = DeepONet()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    n_samples = (
        branch_tensor.shape[0]
    )

    losses = []

    for epoch in range(epochs):

        permutation = torch.randperm(
            n_samples
        )

        epoch_loss = 0.0

        for start in range(
            0,
            n_samples,
            batch_size,
        ):

            indices = permutation[
                start:
                start + batch_size
            ]

            branch_batch = (
                branch_tensor[
                    indices
                ]
            )

            trunk_batch = (
                trunk_tensor[
                    indices
                ]
            )

            target_batch = (
                target_tensor[
                    indices
                ]
            )

            prediction = model(
                branch_batch,
                trunk_batch,
            )

            loss = torch.mean(
                (
                    prediction
                    - target_batch
                )
                ** 2
            )

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()

            epoch_loss += float(
                loss.detach()
            ) * len(indices)

        epoch_loss /= n_samples

        losses.append(
            epoch_loss
        )

        if (
            epoch % 200 == 0
            or epoch
            == epochs - 1
        ):
            print(
                f"Epoch "
                f"{epoch:5d} | "
                f"Loss "
                f"{epoch_loss:.6e}"
            )

    return DeepONetTrainingResult(
        model=model,
        losses=losses,
        final_loss=losses[-1],
    )