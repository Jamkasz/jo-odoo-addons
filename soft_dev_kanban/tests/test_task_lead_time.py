from openerp.tests import common
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf
from openerp.models import except_orm


class TestTaskLeadTime(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTaskLeadTime, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.stage_model = cls.env['project.task.type']
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search(
            [['name', '=', 'Tasks Lead Time']])
        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])

    def test_01_get_working_hours_raises_when_non_datetime_start(self):
        with self.assertRaises(except_orm):
            self.task.get_working_hours('date1', dt.now())

    def test_02_get_working_hours_raises_when_non_datetime_end(self):
        with self.assertRaises(except_orm):
            self.task.get_working_hours(dt.now(), 'date1')

    def test_03_get_working_hours_counts_hours_from_start_to_end(self):
        start = dt.strptime('2015-10-19 10:00:00', dtf)
        end = dt.strptime('2015-10-19 12:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 2)

    def test_04_get_working_hours_does_not_count_hours_out_of_timesheet(self):
        start = dt.strptime('2015-10-19 10:00:00', dtf)
        end = dt.strptime('2015-10-19 14:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 3)

    def test_05_get_working_hours_starts_counting_within_timesheet_time(self):
        start = dt.strptime('2015-10-19 06:00:00', dtf)
        end = dt.strptime('2015-10-19 10:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 2)

    def test_06_get_working_hours_finishes_counting_within_timesheet_time(self):
        start = dt.strptime('2015-10-19 16:00:00', dtf)
        end = dt.strptime('2015-10-19 19:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 2)

    def test_07_compute_total_time_returns_false_if_no_date_in(self):
        self.task._compute_total_time()
        self.assertFalse(self.task.total_time)

    def test_08_write_non_backlog_stage_records_date_in(self):
        self.task.stage_id = self.queue.id
        self.assertTrue(self.task.date_in)

    def test_09_write_done_stage_records_date_out(self):
        self.task.stage_id = self.done.id
        self.assertTrue(self.task.date_out)

    def test_10_compute_total_time_returns_hours_until_now_if_no_date_out(self):
        self.task.date_in = (dt.now() - td(minutes=30)).strftime(dtf)
        self.task.date_out = False
        self.task._compute_total_time()
        res = self.task.total_time
        self.assertFalse(isinstance(res, bool))
        self.assertEqual(res, 0)

    def test_11_compute_total_time_returns_working_hours_from_in_to_out(self):
        self.task.date_in = '2015-10-19 10:00:00'
        self.task.date_out = '2015-10-19 12:00:00'
        self.task._compute_total_time()
        self.assertEqual(self.task.total_time, 2)

    def test_12_update_date_in_records_earliest_non_backlog_stage_log_date(self):
        self.task2.update_date_in()
        self.assertEqual(self.task2.date_in, '2015-10-19 08:00:00')

    def test_13_update_date_out_records_earliest_done_stage_log_date(self):
        self.task2.update_date_out()
        self.assertEqual(self.task2.date_out, '2015-10-19 17:00:00')
