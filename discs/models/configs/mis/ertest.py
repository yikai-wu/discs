"""Config for er-test dataset."""

from discs.common import configs
from ml_collections import config_dict
from sco.experiments import default_configs


def get_config(cfg_str):
  """Get config for er benchmark graphs."""
  extra_cfg = default_configs.parse_cfg_str(cfg_str)
  rand_type = extra_cfg['r']
  num_nodes = num_edges = num_instances = 0
  if rand_type == '800':
    num_nodes = 800
    num_edges = 47885
    num_instances = 128
  elif rand_type == '10k':
    num_nodes = 10915
    num_edges = 1190799
    num_instances = 16

  model_config = dict(
      name='mis',
      max_num_nodes=num_nodes,
      max_num_edges=num_edges,
      num_instances=num_instances,
      num_categories=2,
      shape=(0,),
      rand_type=rand_type,
      penalty=1.001,
      data_root='',
      graph_type='ertest',
  )
  return config_dict.ConfigDict(model_config)
