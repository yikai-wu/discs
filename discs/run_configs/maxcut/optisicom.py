from ml_collections import config_dict


def get_config():
  """Get config."""

  config = config_dict.ConfigDict(
      dict(
          model='maxcut',
          sampler='path_auxiliary',
          graph_type='optsicom',
          sweep=[
              {
                  'model_config.cfg_str': [
                      'r-b',
                  ],
                  'config.experiment.log_every_steps': [100],
                  'config.experiment.num_models': [10],
                  'config.experiment.batch_size': [16],
              },
          ],
      )
  )
  return config
