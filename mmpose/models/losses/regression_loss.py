import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..registry import LOSSES


@LOSSES.register_module()
class SmoothL1Loss(nn.Module):
    """SmoothL1Loss loss ."""

    def __init__(self, use_target_weight=False, loss_weight=1.):
        super().__init__()
        self.criterion = F.smooth_l1_loss
        self.use_target_weight = use_target_weight
        self.loss_weight = loss_weight

    def forward(self, output, target, target_weight):
        """Forward function.

        Note:
            batch_size: N
            num_keypoints: K

        Args:
            output (torch.Tensor[N, K, 2]): Output regression.
            target (torch.Tensor[N, K, 2]): Target regression.
            target_weight (torch.Tensor[N, K, 2]):
                Weights across different joint types.
        """
        num_joints = output.size(1)
        if self.use_target_weight:
            loss = self.criterion(
                output.mul(target_weight), target.mul(target_weight))
        else:
            loss = self.criterion(output, target)

        return loss / num_joints * self.loss_weight


@LOSSES.register_module()
class WingLoss(nn.Module):
    """Wing Loss 'Wing Loss for Robust Facial Landmark Localisation with
    Convolutional Neural Networks' Feng et al.

    CVPR'2018
    """

    def __init__(self,
                 omega=10,
                 epsilon=2,
                 use_target_weight=False,
                 loss_weight=1.):
        super().__init__()
        self.omega = omega
        self.epsilon = epsilon
        self.use_target_weight = use_target_weight
        self.loss_weight = loss_weight

    def criterion(self, pred, target):
        delta = (target - pred).abs()
        c = self.omega * (1.0 - math.log(1.0 + self.omega / self.epsilon))
        losses = torch.where(
            torch.lt(delta, self.omega),
            self.omega * torch.log(1.0 + delta / self.epsilon), delta - c)
        return torch.mean(torch.sum(losses, dim=[1, 2]), dim=0)

    def forward(self, output, target, target_weight):
        """Forward function.

        Note:
            batch_size: N
            num_keypoints: K

        Args:
            output (torch.Tensor[N, K, 2]): Output regression.
            target (torch.Tensor[N, K, 2]): Target regression.
            target_weight (torch.Tensor[N, K, 2]):
                Weights across different joint types.
        """
        num_joints = output.size(1)
        if self.use_target_weight:
            loss = self.criterion(
                output.mul(target_weight), target.mul(target_weight))
        else:
            loss = self.criterion(output, target)

        return loss / num_joints * self.loss_weight
