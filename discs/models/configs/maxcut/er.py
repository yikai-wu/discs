from discs.common import utils
from ml_collections import config_dict


def get_model_config(cfg_str):
  """Get config."""
  extra_cfg = utils.parse_cfg_str(cfg_str)
  
  num_nodes = num_edges = 0
  rand_type = extra_cfg['r']
  if rand_type.endswith('1024-1100'):
    num_nodes = 1100
    num_edges = 91239
  elif rand_type.endswith('512-600'):
    num_nodes = 600
    num_edges = 27132
  elif rand_type.endswith('256-300'):
    num_nodes = 300
    num_edges = 6839

  model_config= dict(
      max_num_nodes=num_nodes,
      max_num_edges=num_edges,
      num_categories=2,
      shape=(0,),
      rand_type=rand_type,
  )
  
  return config_dict.ConfigDict(model_config)