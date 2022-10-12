"""Tests for Ising."""

from absl.testing import absltest
from absl.testing import parameterized
import dmcx.model.ising as ising_model
import jax
from ml_collections import config_dict
import numpy as np


class IsingTest(parameterized.TestCase):

  def setUp(self):
    """This method will be run before each of the test methods in the class."""
    super().setUp()
    self.config = config_dict.ConfigDict(
        initial_dictionary=dict(
            shape=7,
            init_sigma=1.0,
            lambdaa=0.4407,
            external_field_type=0))
    self.ising_model = ising_model.Ising(self.config)
    self.rng = jax.random.PRNGKey(0)
    if isinstance(self.config.shape, int):
      self.shape = (self.config.shape, self.config.shape)
    else:
      self.shape = self.config.shape

  def test_make_init_params(self):
    params = self.ising_model.make_init_params(self.rng)
    w_b = params[0]
    w_h = params[1]
    w_v = params[2]
    self.assertEqual(w_b.shape, self.shape)
    self.assertEqual(w_h.shape, self.shape)
    self.assertEqual(w_v.shape, self.shape)

  @parameterized.named_parameters(('Ising Initial Samples', 2))
  def test_get_init_samples(self, num_samples):
    x0 = self.ising_model.get_init_samples(self.rng, num_samples)
    self.assertEqual(x0.shape,
                     (num_samples,)+self.shape)

  @parameterized.named_parameters(('Ising Forward', 2))
  def test_forward(self, num_samples):
    rng_param, rng_x0 = jax.random.split(self.rng)
    params = self.ising_model.make_init_params(rng_param)
    x0 = self.ising_model.get_init_samples(rng_x0, num_samples)
    loglikelihood = self.ising_model.forward(params, x0)
    self.assertEqual(loglikelihood.shape, (num_samples,))

  @parameterized.named_parameters(('Ising Value and Grad', 10))
  def test_value_grad(self, num_samples):
    rng_param, rng_x0 = jax.random.split(self.rng)
    params = self.ising_model.make_init_params(rng_param)
    x0 = self.ising_model.get_init_samples(rng_x0, num_samples)
    loglikelihood, grad = self.ising_model.get_value_and_grad(params, x0)
    self.assertEqual(loglikelihood.shape, (num_samples,))
    self.assertEqual(grad.shape,
                     (num_samples,)+self.shape)

if __name__ == '__main__':
  absltest.main()