import logging
import os
import copy
from dataclasses import dataclass, field, asdict
from typing import *

import torch
from torch import Tensor
from omegaconf import DictConfig, OmegaConf

from .hub_interface import HubInterface

CONFIG_TYPE = Literal['base', 'model', 'dataset', 'task', 'criterion', 'optimizer']


@dataclass
class Config:
    config_type: CONFIG_TYPE = field(
        default='base',
        metadata={
            'help': "The category this config is responsible for"
        }
    )

    def dict(self):
        return asdict(self)

    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default

    @classmethod
    def from_pretrained(cls, pretrained_path: Union[str, os.PathLike], filename='config.yaml', **kwargs):
        """
        Load config from Hub or locally if it already exists (handled by HfApi)
        """
        repo = HubInterface(pretrained_path, repo_type='model')
        kwargs = copy.deepcopy(kwargs)
        config = repo.get_config(config_file=filename)
        if cls.config_type != 'base':
            # if config_type is not `base` create a {config_type}Config() instance e.g, ModelConfig()
            config = cls.from_dict(config, **kwargs)
        return config

    @classmethod
    def from_dict(cls, dict_config: Union[Dict, DictConfig], strict=False, **kwargs):
        """
        Load config from a dict-like object
        """
        # load config_type part of the config if config_type is given
        dict_config = dict_config[cls.config_type]
        dict_config.update(**kwargs)

        config = cls(**{
            k: v for k, v in dict_config.items()
            if k in cls.__annotations__.keys()
        })

        for k, v in dict_config.items():
            if not hasattr(cls, k):
                if strict:
                    raise ValueError(f'`{cls.__name__}` does not take `{k}` in attributes!\n Hint: add this attribute '
                                     f'to `{cls.__name__}` as:\n `{k}: {v.__class__.__name__} = field(default=None)` '
                                     f'or set `strict=False` when using `from_pretrained()`')
                else:
                    setattr(config, k, v)

        if config is None:
            raise ValueError(f'This dict config has no `{cls.config_type}` key!')
        return config

    def save_pretrained(self, save_dir, filename='config.yaml'):
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        OmegaConf.save(self.dict(), save_path)
        logging.info(f'Saved config to `{save_path}`')


@dataclass
class ModelConfig(Config):
    config_type: CONFIG_TYPE = 'model'
    name: str = field(
        default=None,
        metadata={
            'help': "Name of the model's key in the models_registry"
        })
    pretrained_path: str = field(
        default=None,
        metadata={
            'help': 'pretrained path for the model, automatically filled when loading model from Hub'
        }
    )


@dataclass
class DatasetConfig(Config):
    config_type: CONFIG_TYPE = 'dataset'
    name: str = field(
        default=None,
        metadata={
            'help': 'Name of the dataset'
        })
    task: Union[str, List[str]] = field(
        default=None,
        metadata={
            'help': 'Name of the task(s) this dataset is built for'
        }
    )


@dataclass
class CriterionConfig(Config):
    config_type: CONFIG_TYPE = 'criterion'
    name: str = None
    weight: Optional[Tensor] = None
    reduce: str = None
    ignore_index: int = -100


@dataclass
class OptimizerConfig(Config):
    config_type: CONFIG_TYPE = 'optimizer'
    name: str = None
    lr: float = None


@dataclass
class TrainConfig(Config):
    config_type: CONFIG_TYPE = 'train'
    device: str = 'cpu'
    model_name: str = field(
        default=None,
        metadata={
            'help': 'name of the model in the models_registry'
        })
    name: str = field(default=None)
    model_config: ModelConfig = field(
        default=ModelConfig(),
        metadata={
            'help': 'model config for the trainer'
        })
    dataset_config: DatasetConfig = field(
        default=DatasetConfig(),
        metadata={
            'help': 'dataset config for the trainer'
        }
    )
