from ml_collections import config_dict


def get_lm_default_config():
  """Get combinatorial default configs."""
  exp_config = config_dict.ConfigDict()
  exp_config.evaluator = 'lm_eval'
  exp_config.name = 'Text_Infilling_Experiment'
  exp_config.batch_size = 1
  exp_config.chain_length = 4
  exp_config.max_n = 4
  exp_config.num_same_resample = 10
  exp_config.topk_num = 5
  exp_config.select_top_k = True
  exp_config.run_parallel = False
  return exp_config
