from openerp.tests import common
from datetime import date, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class TestBaseExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBaseExtension, cls).setUpClass()
        cls.user_model = cls.env['res.users']
        cls.task_model = cls.env['project.task']
        cls.stage_model = cls.env['project.task.type']

        cls.backlog = cls.stage_model.create({'name': 'TEST BACKLOG',
                                              'stage_type': 'backlog'})
        cls.input = cls.stage_model.create({'name': 'TEST INPUT',
                                            'stage_type': 'queue'})
        cls.queue = cls.stage_model.create({'name': 'TEST BUFFER',
                                            'stage_type': 'queue'})
        cls.analysis = cls.stage_model.create({'name': 'TEST ANALYSIS',
                                            'stage_type': 'analysis'})
        cls.dev = cls.stage_model.create({'name': 'TEST DEVELOPMENT',
                                            'stage_type': 'dev'})
        cls.review = cls.stage_model.create({'name': 'TEST REVIEW',
                                            'stage_type': 'review'})
        cls.done = cls.stage_model.create({'name': 'TEST DONE',
                                            'stage_type': 'done'})

        cls.user = cls.user_model.create({
            'name': 'TEST USER',
            'login': 'testuser',
            'wip_finished': 2,
            'total_wip_days': 10,
            'wip_average': 2.0,
            'wip_limit': 2,
            'date_last_wip_update': (date.today() - td(days=1)).strftime(DF)
        })
        cls.task = cls.task_model.create({
            'name': 'TEST TASK',
            'stage_id': cls.backlog.id})
        cls.task2 = cls.task_model.create({
            'name': 'TEST TASK2',
            'stage_id': cls.backlog.id})

    def test_01_add_wip_average_update(self):
        self.user.add_wip()
        self.assertEqual(self.user.wip_finished, 1)
        self.assertEqual(self.user.date_last_wip_update,
                         date.today().strftime(DF))
        self.assertEqual(self.user.total_wip_days, 11)
        self.assertEqual(self.user.wip_average, 2.0)

    def test_02_add_wip_current_working_day(self):
        self.user.add_wip()
        self.assertEqual(self.user.wip_finished, 2)
        self.assertEqual(self.user.date_last_wip_update,
                         date.today().strftime(DF))
        self.assertEqual(self.user.total_wip_days, 11)
        self.assertEqual(self.user.wip_average, 2.0)

    def test_03_current_wip_analysis_items(self):
        self.assertEqual(self.user.current_wip_items()[0], 0)
        self.task.analyst_id = self.user.id
        self.assertEqual(self.user.current_wip_items()[0], 0)
        self.task.stage_id = self.analysis.id
        self.assertEqual(self.user.current_wip_items()[0], 1)

    def test_04_current_wip_dev_items(self):
        self.task2.user_id = self.user.id
        self.assertEqual(self.user.current_wip_items()[0], 1)
        self.task2.stage_id = self.dev.id
        self.assertEqual(self.user.current_wip_items()[0], 2)
        self.task.stage_id = self.dev.id
        self.assertEqual(self.user.current_wip_items()[0], 1)

    def test_05_current_wip_review_items(self):
        self.task.reviewer_id = self.user.id
        self.assertEqual(self.user.current_wip_items()[0], 1)
        self.task2.stage_id = self.review.id
        self.assertEqual(self.user.current_wip_items()[0], 0)
        self.task.stage_id = self.review.id
        self.assertEqual(self.user.current_wip_items()[0], 1)

    def test_06_current_wip_items_ignores_queue_stages(self):
        self.task.stage_id = self.queue.id
        self.task2.stage_id = self.queue.id
        self.assertEqual(self.user.current_wip_items()[0], 0)
