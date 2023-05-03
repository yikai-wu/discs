"""Discrete Langevin Monte Carlo."""

import pdb
from discs.common import math_util as math
from discs.samplers import locallybalanced
import jax
import jax.numpy as jnp
from jax.scipy import special
import ml_collections


class DMALASampler(locallybalanced.LocallyBalancedSampler):
  """DMALA sampler."""

  def update_sampler_state(self, state, acc, local_stats):
    cur_step = state['steps']
    state['num_ll_calls'] += 4
    if not self.adaptive:
      return
    log_z = jnp.where(
        cur_step % self.reset_z_est == 0, local_stats['log_z'], state['log_z']
    )
    log_z = jnp.where(
        cur_step < self.schedule_step, local_stats['log_z'], state['log_z']
    )
    # updating tau
    n = jnp.exp(state['log_tau'] + log_z)
    n = n + 3 * (acc - self.target_acceptance_rate)
    state['log_tau'] = jnp.clip(jnp.log(n) - log_z, a_min=-log_z)
    state['log_z'] = log_z

  def select_sample(
      self, rng, local_stats, log_acc, current_sample, new_sample, sampler_state
  ):
    y, new_state = super().select_sample(
        rng, log_acc, current_sample, new_sample, sampler_state
    )
    acc = jnp.mean(jnp.exp(jnp.clip(log_acc, a_max=0.0)))
    self.update_sampler_state(new_state, acc, local_stats)
    return y, new_state

  def set_z(self, log_rates):
    if self.num_categories > 2:
      log_z = jnp.mean(jnp.sum(jnp.exp(log_rates), axis=[-2, -1]))
    else:
      log_z = jnp.mean(jnp.sum(jnp.exp(log_rates), axis=[-1]))
    return log_z

  def reset_stats(self, log_rates):
    log_z = jnp.log(self.set_z(log_rates))
    log_tau = math.log(3.0) - log_z
    return {'log_tau': log_tau, 'log_z': log_z}

  def get_value_and_rates(self, model, model_param, x):
    ll_x, grad_x = model.get_value_and_grad(model_param, x)
    if self.num_categories == 2:
      ll_delta = (1 - 2 * x) * grad_x
    else:
      ll_delta = grad_x - jnp.sum(grad_x * x, axis=-1, keepdims=True)
    log_weight_x = self.apply_weight_function_logscale(ll_delta)
    return ll_x, {'weights': log_weight_x, 'delta': ll_delta}

  def __init__(self, config: ml_collections.ConfigDict):
    super().__init__(config)
    self.adaptive = config.sampler.adaptive
    if self.adaptive:
      self.target_acceptance_rate = config.sampler.target_acceptance_rate
      self.schedule_step = config.sampler.get('schedule_step', 100)
    self.reset_z_est = config.sampler.get('reset_z_est', 20)

  def make_init_state(self, rng):
    state = super().make_init_state(rng)
    state['log_tau'] = jnp.zeros(shape=(), dtype=jnp.int32)
    state['log_z'] = jnp.zeros(shape=(), dtype=jnp.int32)
    return state

  def step(self, model, rng, x, model_param, state, x_mask=None):
    _ = x_mask
    if self.num_categories != 2:
      x = jax.nn.one_hot(x, self.num_categories, dtype=jnp.float32)
    rng_new_sample, rng_acceptance = jax.random.split(rng)

    ll_x, log_rate_x = self.get_value_and_rates(model, model_param, x)
    local_stats = self.reset_stats(log_rate_x['weights'])
    log_tau = jnp.where(
        state['steps'] == 0, local_stats['log_tau'], state['log_tau']
    )

    dist_x = self.get_dist_at(x, log_tau, log_rate_x)
    y, aux = self.sample_from_proposal(rng_new_sample, x, dist_x)
    ll_x2y = self.get_ll_onestep(dist_x, aux=aux)

    ll_y, log_rate_y = self.get_value_and_rates(model, model_param, y)
    dist_y = self.get_dist_at(y, log_tau, log_rate_y)
    aux = jnp.where(self.num_categories > 2, x, aux)
    ll_y2x = self.get_ll_onestep(dist_y, aux=aux)
    log_acc = ll_y + ll_y2x - ll_x - ll_x2y
    new_x, new_state = self.select_sample(
        rng_acceptance, local_stats, log_acc, x, y, state
    )
    acc = jnp.mean(jnp.clip(jnp.exp(log_acc), a_max=1))
    return new_x, new_state, acc


class BinaryDMALA(DMALASampler):
  """DMALA sampler in biary case."""

  def get_dist_at(self, x, log_tau, log_rate_x):
    _ = x
    log_weight_x = log_rate_x['weights']
    threshold_x = log_tau + log_weight_x
    threshold_x -= jnp.logaddexp(threshold_x, jnp.zeros_like(threshold_x))
    return jnp.exp(
        jnp.clip(threshold_x, a_max=0.0)
    )  # Kati check the values of this

  def sample_from_proposal(self, rng, x, dist_x):
    flip = jax.random.bernoulli(rng, p=dist_x)
    y = x * (1 - flip) + flip * (1 - x)
    return y, flip

  def get_ll_onestep(self, dist, aux):
    return jnp.sum(
        jnp.log(dist + 1e-32) * aux + jnp.log(1 - dist + 1e-32) * (1 - aux),
        axis=range(1, dist.ndim),
    )


class CategoricalDMALA(DMALASampler):
  """DMALA sampler in categorical case."""

  def get_dist_at(self, x, log_tau, log_rate_x):
    log_weight_x = log_rate_x['weights']
    log_posterior_x = log_tau + log_weight_x
    log_posterior_x = log_posterior_x * (1 - x)
    log_posterior_x -= jnp.log(
        jnp.sum(jnp.exp(log_posterior_x), axis=-1, keepdims=True)
    )
    return log_posterior_x

  def sample_from_proposal(self, rng, x, dist_x):
    y = jax.random.categorical(rng, logits=dist_x)
    y = jax.nn.one_hot(y, self.num_categories, dtype=jnp.float32)
    return y, y

  def get_ll_onestep(self, dist, aux):
    dist_ll = jax.nn.log_softmax(dist)
    ll_aux = jnp.sum(dist_ll * aux, axis=range(1, dist.ndim))
    return ll_aux


def build_sampler(config):
  if config.model.num_categories == 2:
    return BinaryDMALA(config)
  else:
    return CategoricalDMALA(config)