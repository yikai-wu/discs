"""Saver Class."""

from discs.samplers.locallybalanced import LBWeightFn
import ml_collections
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import os
import csv


class Saver:
  """Class used to plot and save the results of the experiments."""

  def __init__(self, save_dir, config: ml_collections.ConfigDict):
    self.config = config
    self.save_dir = save_dir
    if not os.path.isdir(self.save_dir):
      os.makedirs(self.save_dir)

  def _plot_acc_ratio(self, acc_ratio):
    plt.plot(jnp.arange(1, 1 + len(acc_ratio)), acc_ratio, '--b')
    plt.xlabel('Steps')
    plt.ylabel('Acc Ratio')
    plt.ylim((-0.1, 1.1))
    plt.title(
        'Acc Ratio for sampler {} on model {}!'.format(
            self.config.sampler.name, self.config.model.name
        )
    )
    path = f'{self.save_dir}/AccRatio_{self.config.sampler.name}_{self.config.model.name}'
    plt.savefig(path)
    plt.close()

  def _plot_hops(self, hops):
    plt.plot(jnp.arange(1, 1 + len(hops)), hops, '--b')
    plt.xlabel('Steps')
    plt.ylabel('Hops')
    plt.title(
        'Hops for sampler {} on model {}!'.format(
            self.config.sampler.name, self.config.model.name
        )
    )
    path = f'{self.save_dir}/Hops_{self.config.sampler.name}_{self.config.model.name}'
    plt.savefig(path)
    plt.close()

  def _save_results(self, metrcis, running_time):
    """Saving the Evaluation Results in txt and CSV file."""

    results = {}
    results['sampler'] = self.config.sampler.name
    if 'adaptive' in self.config.sampler.keys():
      results['sampler'] = f'a_{self.config.sampler.name}'

    if 'balancing_fn_type' in self.config.sampler.keys():
      if self.config.sampler.balancing_fn_type == LBWeightFn.RATIO:
        results['sampler'] = results['sampler'] + '(ratio)'
      elif self.config.sampler.balancing_fn_type == LBWeightFn.MAX:
        results['sampler'] = results['sampler'] + '(max)'
      elif self.config.sampler.balancing_fn_type == LBWeightFn.MIN:
        results['sampler'] = results['sampler'] + '(min)'
      else:
        results['sampler'] = results['sampler'] + '(sqrt)'

    metrcis = jnp.array(metrcis)
    results['model'] = self.config.model.name
    results['num_categories'] = self.config.model.num_categories
    results['shape'] = self.config.model.shape
    results['ESS'] = metrcis[0]
    results['ESS_M-H'] = metrcis[1]
    results['ESS_T'] = metrcis[2]
    results['ESS_EE'] = metrcis[3]
    results['Time'] = running_time
    results['batch_size'] = self.config.experiment.batch_size
    results['chain_length'] = self.config.experiment.chain_length
    results['ess_ratio'] = self.config.experiment.ess_ratio

    csv_path = f'{self.save_dir}/results.csv'
    if not os.path.exists(csv_path):
      with open(f'{self.save_dir}/results.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(results.keys()))
        writer.writeheader()
        writer.writerow(results)
        csvfile.close()
    else:
      with open(f'{self.save_dir}/results.csv', 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(results.keys()))
        writer.writerow(results)
        csvfile.close()

    with open(
        f'{self.save_dir}/{self.config.model.name}_{self.config.sampler.name}_{running_time}.txt',
        'w',
    ) as f:
      f.write('Mean ESS: {} \n'.format(metrcis[0]))
      f.write('ESS M-H Steps: {} \n'.format(metrcis[1]))
      f.write('ESS over time: {} \n'.format(metrcis[2]))
      f.write('ESS over loglike calls: {} \n'.format(metrcis[3]))
      f.write('Running time: {} s \n'.format(running_time))
      f.write(str(self.config))

  def save_results(self, acc_ratio, hops, metrcis, running_time):
    self._plot_acc_ratio(acc_ratio)
    self._plot_hops(hops)
    self._save_results(metrcis, running_time)


def build_saver(save_dir, config):
  return Saver(save_dir, config)