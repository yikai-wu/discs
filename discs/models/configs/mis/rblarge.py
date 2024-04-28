from ml_collections import config_dict


def get_model_config(cfg_str):
  """Get config for RB graphs."""
  _ = cfg_str
  num_nodes = 0
  num_edges = 0
  num_instances = 500

  model_config = dict(
      num_models=512,
      max_num_nodes=num_nodes,
      max_num_edges=num_edges,
      num_instances=num_instances,
      num_categories=2,
      shape=(0,),
      rand_type='',
      penalty=1.0001
  )

  return config_dict.ConfigDict(model_config)

def get_config():
  model_config = config_dict.ConfigDict(
      dict(
          name='mis',
          graph_type='rblarge',
          cfg_str='',
          data_root='./sco/',
          save_dir_name="mis_rblarge_1.0001"
      )
  )
  return model_config