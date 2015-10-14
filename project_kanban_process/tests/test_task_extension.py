from openerp.tests import common
from mock import patch, MagicMock
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class TestTaskExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTaskExtension, cls).setUpClass()
        # cls.task_model = cls.env['project.task']
        #
        # cls.task = cls.task_model.create({'name': 'TEST TASK'})

    def test_01_total_time_elapsed(self):
        task = MagicMock()
        task.create_date = (dt.now() - td(hours=10)).strftime(dtf)
        task.date_end = False

        def compute_total_time(self):
            if not self.date_end:
                date_end = dt.now()
            else:
                date_end = dt.strptime(self.date_end, dtf)
            elapsed_time = (date_end - dt.strptime(self.create_date, dtf)).total_seconds()
            return int(elapsed_time/3600)

        task.total_time = compute_total_time(task)
        self.assertEqual(task.total_time, 10)
        task.date_end = (dt.now() - td(hours=5)).strftime(dtf)
        task.total_time = compute_total_time(task)
        self.assertEqual(task.total_time, 5)

    def test_02_stage_time_elapsed(self):
        task = MagicMock()
        task.create_date = (dt.now() - td(hours=10)).strftime(dtf)
        task.date_end = False
        task.date_last_stage_update = (dt.now() - td(hours=2)).strftime(dtf)

        def compute_stage_time(self):
            if not self.date_end:
                date_end = dt.now()
            else:
                date_end = dt.strptime(self.date_end, dtf)
            elapsed_time = (date_end - dt.strptime(self.date_last_stage_update, dtf)).total_seconds()
            return int(elapsed_time/3600)

        task.stage_time = compute_stage_time(task)
        self.assertEqual(task.stage_time, 2)
