from openerp.tests import common
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf
from openerp.models import except_orm


class TestTaskStageTime(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTaskStageTime, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.log_model = cls.env['project.task.history']
        cls.stage_model = cls.env['project.task.type']
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search(
            [['name', '=', 'Tasks Lead Time']])
        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.dev = cls.stage_model.search([['name', '=', 'Development']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])

    def test_01_stage_working_hours_raises_if_non_datetime_date(self):
        with self.assertRaises(except_orm):
            self.task.stage_working_hours(1, 'date')

    def test_02_stage_working_hours_is_0_if_no_stage(self):
        self.assertEqual(self.task.stage_working_hours(1, dt.now())[0], 0)

    def test_03_stage_working_hours_counts_history_log_hours_for_stage(self):
        self.assertEqual(self.task2.stage_working_hours(
            self.dev.id, dt.now())[0], 6)

    def test_04_stage_working_hours_adds_working_hours_if_current_stage(self):
        logs = self.log_model.search([
            ['task_id', '=', self.task2.id],
            ['type_id', '=', self.done.id]], order='date desc')
        logs[0].date = (dt.now() - td(days=3)).strftime(dtf)
        self.assertGreaterEqual(self.task2.stage_working_hours(
            self.done.id, dt.now())[0], 1)

    def test_05_compute_stage_time_uses_now_if_no_date_out(self):
        self.task2._compute_stage_time()
        self.assertGreaterEqual(self.task2.stage_time, 1)

    def test_06_compute_stage_time_counts_working_hours_until_date_out(self):
        self.task2.date_out = (dt.now() - td(days=3)).strftime(dtf)
        self.task2._compute_stage_time()
        self.assertEqual(self.task2.stage_time, 0)
