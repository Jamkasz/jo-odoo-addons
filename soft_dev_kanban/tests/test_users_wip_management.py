from openerp.tests import common
from datetime import date, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class TestUsersWipManagement(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestUsersWipManagement, cls).setUpClass()
        cls.user_model = cls.env['res.users']
        cls.task_model = cls.env['project.task']
        cls.stage_model = cls.env['project.task.type']

        cls.backlog = cls.stage_model.search([['name', '=', 'Backlog']])
        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.analysis = cls.stage_model.search([['name', '=', 'Analysis']])
        cls.dev = cls.stage_model.search([['name', '=', 'Development']])
        cls.review = cls.stage_model.search([['name', '=', 'Testing']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])

        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

    def test_01_add_finished_items_updates_average_throughput(self):
        self.user.add_finished_item()
        self.assertEqual(self.user.wi_finished, 1)
        self.assertEqual(self.user.date_last_wip_update,
                         date.today().strftime(DF))
        self.assertEqual(self.user.total_days, 11)
        self.assertEqual(self.user.throughput, 2.0)

    def test_02_add_finished_items_updates_items_finished(self):
        self.user.add_finished_item()
        self.assertEqual(self.user.wi_finished, 2)
        self.assertEqual(self.user.date_last_wip_update,
                         date.today().strftime(DF))
        self.assertEqual(self.user.total_days, 11)
        self.assertEqual(self.user.throughput, 2.0)

    def test_03_current_wip_items_counts_analysis_items_if_user_analyst(self):
        self.assertEqual(self.user.current_wip_items()[0], 0)
        self.task.analyst_id = self.user.id
        self.assertEqual(self.user.current_wip_items()[0], 0)
        self.task.stage_id = self.analysis.id
        self.assertEqual(self.user.current_wip_items()[0], 1)

    def test_04_current_wip_items_counts_dev_items_if_user_assigned(self):
        self.task2.user_id = self.user.id
        self.assertEqual(self.user.current_wip_items()[0], 1)
        self.task2.stage_id = self.dev.id
        self.assertEqual(self.user.current_wip_items()[0], 2)
        self.task.stage_id = self.dev.id
        self.assertEqual(self.user.current_wip_items()[0], 1)

    def test_05_current_wip_items_counts_review_items_if_user_reviewer(self):
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
