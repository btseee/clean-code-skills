import torch
from torch import optim
from torch.utils.data import DataLoader

from model import Net


def train(train_loader: DataLoader, val_loader: DataLoader, epochs: int = 5) -> Net:
    model = Net().cuda()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for images, labels in train_loader:
            images, labels = images.cuda(), labels.cuda()
            optimizer.zero_grad()
            loss = loss_fn(model(images), labels)
            loss.backward()
            optimizer.step()
        print(f"epoch {epoch}: train loss {loss.item():.4f}")

    return model
