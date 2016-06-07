# analyze androcov result
# giving the instrumentation.json generated by androcov and the logcat generated at runtime
__author__ = 'yuanchun'
import os
import re
import json
from datetime import datetime
# logcat regex, which will match the log message generated by `adb logcat -v threadtime`
LOGCAT_THREADTIME_RE = re.compile('^(?P<date>\S+)\s+(?P<time>\S+)\s+(?P<pid>[0-9]+)\s+(?P<tid>[0-9]+)\s+'
                                  '(?P<level>[VDIWEFS])\s+(?P<tag>[^:]*):\s+(?P<content>.*)$')


class Androcov(object):
    def __init__(self, androcov_dir):
        self.androcov_dir = androcov_dir
        self.all_methods = self._parse_all_methods()

    def _parse_all_methods(self):
        instrumentation_file_path = os.path.join(self.androcov_dir, "instrumentation.json")
        instrumentation_detail = json.load(open(instrumentation_file_path))
        return set(instrumentation_detail['allMethods'])

    def gen_androcov_report(self, logcat_path):
        """
        generate a coverage report
        :param logcat_path:
        :return:
        """
        reached_methods, reached_timestamps = Androcov._parse_reached_methods(logcat_path)
        unreached_methods = self.all_methods - reached_methods
        report = {}
        report['reached_methods_count'] = len(reached_methods)
        report['unreached_methods_count'] = len(unreached_methods)
        report['all_methods_count'] = len(self.all_methods)
        report['coverage'] = "%.0f%%" % (100.0 * len(reached_methods) / len(self.all_methods))
        report['uncoverage'] = "%.0f%%" % (100.0 * len(unreached_methods) / len(self.all_methods))
        time_scale = reached_timestamps[-1] - reached_timestamps[0]
        timestamp_count = {}
        for timestamp in range(0, time_scale.total_seconds()+1):
            timestamp_count[timestamp] = 0
        for timestamp in reached_timestamps:
            timestamp_count[int(timestamp)] += 1
        for timestamp in range(1, time_scale.total_seconds()+1):
            timestamp_count[timestamp] += timestamp_count[timestamp-1]
        report['timestamp_count'] = timestamp_count
        return report

    @staticmethod
    def _parse_reached_methods(logcat_path):
        reached_methods = set()
        reached_timestamps = []
        log_msgs = open(logcat_path).readlines()
        androcov_log_re = re.compile('^\[androcov\] reach \d+: (<.+>)$')
        for log_msg in log_msgs:
            log_data = Androcov.parse_log(log_msg)
            log_content = log_data['content']
            m = re.match(androcov_log_re, log_content)
            if not m:
                continue
            reached_method = m.group(1)
            if reached_method in reached_methods:
                continue
            reached_methods.add(reached_method)
            reached_timestamps.append(log_data['datetime'])
        return reached_methods, reached_timestamps

    @staticmethod
    def parse_log(log_msg):
        """
        parse a logcat message
        the log should be in threadtime format
        @param log_msg:
        @return:
        """
        m = LOGCAT_THREADTIME_RE.match(log_msg)
        if not m:
            return None
        log_dict = {}
        date = m.group('date')
        time = m.group('time')
        log_dict['pid'] = m.group('pid')
        log_dict['tid'] = m.group('tid')
        log_dict['level'] = m.group('level')
        log_dict['tag'] = m.group('tag')
        log_dict['content'] = m.group('content')
        datetime_str = "%s-%s %s" % (datetime.today().year, date, time)
        log_dict['datetime'] = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        return log_dict
