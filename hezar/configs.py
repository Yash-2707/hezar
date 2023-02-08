import logging
import os
from dataclasses import dataclass, field
from typing import *

import torch
from omegaconf import DictConfig, OmegaConf
from huggingface_hub import hf_hub_download

from hezar.utils.logging import get_logger
from .hub import HEZAR_TMP_DIR

logger = get_logger(__name__)

CONFIG_TYPE = Literal['base', 'model', 'dataset', 'train', 'criterion', 'optimizer']


@dataclass
class Config:
    config_type: CONFIG_TYPE = field(
        default='base',
        metadata={
            'help': "The category this config is responsible for"
        }
    )

    def dict(self):
        return self.__dict__

    def get(self, key, default):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default

    @classmethod
    def load(cls, hub_or_local_path: Union[str, os.PathLike], filename='config.yaml', **kwargs):
        """
        Load config from Hub or locally if it already exists_on_hub (handled by HfApi)
        """
        config_path = os.path.join(hub_or_local_path, filename)
        is_local = os.path.isfile(config_path)

        # if the file or repo_id does not exist locally, load from the Hub
        if not is_local:
            config_path = hf_hub_download(hub_or_local_path, filename=filename, cache_dir=HEZAR_TMP_DIR)

        dict_config = OmegaConf.load(config_path)
        config = OmegaConf.to_container(dict_config)
        config = cls.from_dict(config, strict=False, **kwargs)
        return config

    @classmethod
    def from_dict(cls, dict_config: Union[Dict, DictConfig], **kwargs):
        """
        Load config from a dict-like object
        """
        strict = kwargs.pop('strict', True)  # Whether ignore redundant parameters in kwargs or force-assign

        # Update config parameters with kwargs
        dict_config.update(**kwargs)

        config = cls(**{
            k: v for k, v in dict_config.items()
            if k in cls.__annotations__.keys()
        })

        for k, v in dict_config.items():
            if not hasattr(cls, k):
                if strict:
                    logger.warning(f'`{cls.__name__}` does not take `{k}` in attributes!\n Hint: add this attribute '
                                   f'to `{cls.__name__}` as:\n `{k}: {v.__class__.__name__} = field(default=None)` '
                                   f'or set `strict=False` when using `load()`')
                else:
                    setattr(config, k, v)

        return config

    def save(self, save_dir, filename='config.yaml'):
        """
        Save the *config.yaml file to a local path

        Args:
             save_dir: save directory path
             filename: config file name
        """
        config = self.dict()
        config.pop('config_type', None)
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
    weight: Optional[torch.Tensor] = None
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
