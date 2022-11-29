"""Experiment class that runs sampler on the model to generate chains."""
import jax
import jax.numpy as jnp
import tqdm
from ml_collections import config_dict
import pdb

class Experiment():
  """Experiment class that generates chains of samples."""

  def __init__(self, config):
    self.config = config

  def _initialize_model_and_sampler(self, rnd, model, sampler):
    rng_param, rng_x0, rng_sampler = jax.random.split(rnd, num=3)
    params = model.make_init_params(rng_param)
    x0 = model.get_init_samples(rng_x0, self.config.batch_size)
    state = sampler.make_init_state(rng_sampler)
    return params, x0, state

  def _split(self, arr, n_devices):
    return arr.reshape(n_devices, arr.shape[0] // n_devices, *arr.shape[1:])

  def _prepare_data_for_parallel(self, params, x, state, n_devices):
    params = jnp.stack([params] * n_devices)
    state = jnp.stack([state] * n_devices)
    x = self._split(x, n_devices)
    return params, x, state

  def _compile_sampler_step(self, sampler):
    if not self.config.run_parallel:
      compiled_step = jax.jit(sampler.step, static_argnums=0)
    else:
      compiled_step = jax.pmap(sampler.step, static_broadcasted_argnums=[0])
    return compiled_step

  def _setup_num_devices(self):
    if not self.config.run_parallel:
      n_rand_split = 2
    else:
      n_rand_split = jax.local_device_count()
    return n_rand_split

  def get_batch_of_chains(self, model, sampler):
    """Sets up the model and the samlping alg and gets the chain of samples."""
    rnd = jax.random.PRNGKey(0)
    params, x, state = self._initialize_model_and_sampler(rnd, model, sampler)
    model_params = params
    sample_shape = x.shape[1:]
    n_rand_split = self._setup_num_devices()
    if self.config.run_parallel:
      params, x, state = self._prepare_data_for_parallel(
          params, x, state, n_rand_split
      )
    compiled_step = self._compile_sampler_step(sampler)
    chain, samples, state = self._compute_chain(
        model,
        compiled_step,
        state,
        params,
        rnd,
        x,
        n_rand_split,
    )

    if self.config.run_parallel:
      chain = chain.reshape(
          (chain.shape[0], self.config.batch_size)
          + sample_shape
      )
      samples = samples.reshape(
          (samples.shape[0], self.config.batch_size) + sample_shape
      )
      state = state[0]

    return chain, samples, state[1], model_params

  def _compute_chain(
      self,
      model,
      sampler_step,
      state,
      params,
      rng_sampler_step,
      x,
      n_rand_split,
  ):
    """Generates the chain of samples."""
    chain = []
    for _ in tqdm.tqdm(range(self.config.chain_length)):
      rng_sampler_step_p = jax.random.split(rng_sampler_step, num=n_rand_split)
      x, state = sampler_step(model, rng_sampler_step_p, x, params, state)
      del rng_sampler_step_p
      rng_sampler_step, _ = jax.random.split(rng_sampler_step)
      chain.append(x)
    return (
        jnp.array(chain),
        jnp.array(chain[self.config.chain_burnin_length :]),
        jnp.array(state),
    )


def build_experiment(config: config_dict):
  return Experiment(config.experiment)