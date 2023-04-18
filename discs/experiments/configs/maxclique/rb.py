"""Config for maxcut ba dataset."""

from ml_collections import config_dict


def get_config():
  """Get config."""
  exp_config = dict(
      experiment=dict(
          num_models=512,
          batch_size=16,
          t_schedule='exp_decay',
          chain_length=1001,
          log_every_steps=100,
          init_temperature=1.0,
          decay_rate=0.1,
          final_temperature=0.001,
          save_root='',
      )
  )
  return config_dict.ConfigDict(exp_config)
