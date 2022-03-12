from pathlib import Path
from typing import Dict
import re
import time
import os
import pickle

import click
import tensorboardX as tb

from . import marian_nmt, training
from .utils.fs import DirectoryTree


train_log_line_regexp = re.compile(
    training.TIMESTAMP_PATTERN +
    '(?P<_epoch>Ep.)\s+(?P<epoch>\d+)\s+:\s+'
    '(?P<_up>Up.)\s+(?P<up>\d+)\s+:\s+'
    '(?P<_sent>Sen.)\s+(?P<sent>\d+[,]?(?:\d+))\s+:\s+'
    '(?P<_cost>Cost)\s+(?P<cost>[\d.]+)\s+:\s+'
    '(?P<_time>Time)\s+(?P<time>[\d.]+s)\s+:\s+'
    '(?P<wps>\d+.\d+)\s+(?P<_wps>words/s)\s+:\s+'
    '(?P<_lr>L.r.)\s+(?P<lr>\d.[\d-]+)')

valid_log_line_regexp = re.compile(
    training.TIMESTAMP_PATTERN +
    '\\[valid\\]\s+' +
    '(?P<_epoch>Ep.)\s+(?P<epoch>\d+)\s+:\s+'
    '(?P<_up>Up.)\s+(?P<up>\d+)\s+:\s+'
    '(?P<_metric>[\w-]+)\s+:\s+'
    '(?P<metric>[\d.]+)\s+:\s+'
    '(new best|(?P<_stalled>[\w]+)\s+(?P<stalled>\d+))')


class JobMonitor:

    def __init__(self,
                 marian_conf_defaults: Dict,
                 job_path: Path,
                 log_filename: str):
        self.marian_conf_defaults = marian_conf_defaults
        self.log_filename = log_filename
        self.job_path = job_path
        self.tb_logdir = Path(job_path, 'tb')
        self.train_log = Path(job_path, self.log_filename)
        self.last_update_time = 0
        self.last_update_line = -1
        self.gpus = 0
        self.sen_last = 0
        self.last_wall_time = None
        self.gaps = 0
        self.avg_gaps = 0
        self.gaps_num = 0
        self.avg_status = {}
        self.pickle_file = Path(self.tb_logdir, 'monitor-status.pickle')
        if os.path.exists(self.pickle_file):
            with open(self.pickle_file, 'rb') as f:
                (self.last_update_time,
                 self.last_update_line,
                 self.gpus,
                 self.sen_last,
                 self.avg_status,
                 self.last_wall_time,
                 self.gaps,
                 self.avg_gaps,
                 self.gaps_num) = pickle.load(f)
        self.writer = tb.SummaryWriter(self.tb_logdir)
        Path(self.tb_logdir).mkdir(exist_ok=True)

    def wall_time_minus_gaps(self, wall_time):
        if self.last_wall_time is None:
            self.last_wall_time = wall_time
            return wall_time
        gap = wall_time - self.last_wall_time
        if gap > 1200:  # 20 minutes
            self.gaps += gap - self.avg_gaps
        else:
            self.gaps_num += 1
            self.avg_gaps *= self.gaps_num - 1
            self.avg_gaps += gap / self.gaps_num
        self.last_wall_time = wall_time
        return wall_time - self.gaps

    def parse_train(self, line):
        log = train_log_line_regexp.search(line).groupdict()
        wall_time = training.wall_time_from_log(log)
        real_wall_time = wall_time
        wall_time = self.wall_time_minus_gaps(wall_time)

        ep = int(log['epoch'])
        up = int(log['up'])
        self.writer.add_scalar('train/epoch', ep, up, wall_time)
        self.writer.add_scalar('train/wall-clock',
                               real_wall_time,
                               up,
                               real_wall_time)

        sen = int(log['sent'].replace(',', ''))
        cost = float(log['cost'])
        self.writer.add_scalar('train/sentences', sen, up, wall_time)
        self.writer.add_scalar('train/sentences-diff',
                               sen - self.sen_last,
                               up,
                               wall_time)
        self.sen_last = sen

        self.writer.add_scalar('train/cost', cost, up, wall_time)
        t = float(log['time'].rstrip('s'))
        self.writer.add_scalar('train/time[sec]', t, up, wall_time)

        speed = float(log['wps'])
        self.writer.add_scalar('train/speed[words per sec]',
                               speed,
                               up,
                               wall_time)

        if 'lr-report' in self.marian_conf_defaults:
            lr = float(log['lr'])
            self.writer.add_scalar('train/learning_rate', lr, up, wall_time)
            self.writer.add_scalar('train/gpus', self.gpus, up, wall_time)

        return up

    def parse_valid(self, line):
        try:
            log = valid_log_line_regexp.search(line).groupdict()
        except AttributeError:
            print('Ignoring line:', line)
            return None
        if any(v is None for v in log.values()):
            print('Got dodgy log for line:', line)
            print('LOG:', log)
            return None
        try:
            wall_time = training.get_wall_time(log['log_date'],
                                               log['log_time'])
        except TypeError:
            print('LOG:', log)
            raise
        wall_time = self.wall_time_minus_gaps(wall_time)
        up = int(log['up'])
        metric_name = log['_metric']
        metric_value = float(log['metric'])
        self.writer.add_scalar(f'valid/{metric_name}',
                               metric_value,
                               up,
                               wall_time)
        stalled = int(log.get('stalled', 0))
        self.writer.add_scalar(f'valid/{metric_name}_stalled',
                               stalled,
                               up,
                               wall_time)

    def save_last_update(self):
        t = os.path.getmtime(self.train_log)
        self.last_update_time = t
        with open(self.pickle_file, 'wb') as fp:
            pickle.dump((self.last_update_time,
                         self.last_update_line,
                         self.gpus,
                         self.sen_last,
                         self.avg_status,
                         self.last_wall_time,
                         self.gaps,
                         self.avg_gaps,
                         self.gaps_num),
                        fp)

    def update_needed(self):
        t = os.path.getmtime(self.train_log)
        if t > self.last_update_time:
            print('current modification time:',
                  t,
                  'last:',
                  self.last_update_time)
            return True
        return False

    def update_loop(self):
        self.update_all_avg()
        if not self.update_needed():
            return
        with open(self.train_log, 'r') as f:
            for (i, line) in enumerate(f):
                if i <= self.last_update_line:
                    continue
                if '--devices' in line:
                    self.gpus = 0
                    words = line.split()
                    for w in words[words.index('--devices') + 1:]:
                        try:
                            int(w)
                        except Exception:
                            break
                        self.gpus += 1
                elif '] Ep. ' in line and '[valid]' not in line:
                    self.parse_train(line)
                elif '[valid]' in line:
                    self.parse_valid(line)
        self.last_update_line = i
        print('last line id:', self.last_update_line)
        self.save_last_update()

    # This assumes some files like 'avg-8.log' exist in model
    # directory. If not, this does nothing.
    def update_all_avg(self):
        for fn in os.listdir(self.job_path):
            if not fn.startswith('avg-'):
                continue
            if not fn.endswith('.log'):
                continue
            name = fn.replace('.log', '')
            with open(self.job_path + fn) as f:
                if name not in self.avg_status:
                    self.avg_status[name] = -1
                for line in f:
                    label, *score = line.split()
                    try:
                        step = int(label.split('-')[2])
                    except Exception:
                        continue
                    if step <= self.avg_status[name]:
                        continue
                    if not score:
                        continue
                    score = float(score[0])
                    self.writer.add_scalar('valid-avg/' + name + '_bleu',
                                           score,
                                           step)
                    self.avg_status[name] = step


def find_all_log_files(root_dir, filename):
    sessions = training.Session._load()
    for session in sessions.values():
        logs_dir = session.folders.get('logs_dir')
        if logs_dir is None:
            continue
        for path in DirectoryTree(root_dir):
            if filename == path.name:
                yield path


@click.command()
@click.option('--experiments-dir',
              type=click.Path(),
              default='/experiments')
@click.option('--log-filename',
              type=click.Path(),
              default='marian.log')
def monitor_logs(experiments_dir, log_filename):
    marian_conf = marian_nmt.read_config_template()
    monitors = {}
    while True:
        monitored = set()
        # create new monitors
        for log_path in find_all_log_files(experiments_dir, log_filename):
            dirname = log_path.parent
            if dirname not in monitors:
                m = JobMonitor(marian_conf, dirname, log_path.name)
                monitors[dirname] = m
                monitored.add(dirname)
        # delete unregistered monitors
        for dirname in list(monitors.keys()):
            if dirname not in monitored:
                monitors.pop(dirname, None)

        # update all monitors
        for (j, m) in monitors.items():
            print('update loop', j)
            m.update_loop()

        #    break
        time.sleep(5)


if __name__ == '__main__':
    monitor_logs()
