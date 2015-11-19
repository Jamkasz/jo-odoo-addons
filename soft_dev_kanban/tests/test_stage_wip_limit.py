from openerp.tests import common
from openerp.models import except_orm


class TestStageWipLimit(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStageWipLimit, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.stage_model = cls.env['project.task.type']

        cls.backlog = cls.stage_model.search([['name', '=', 'Backlog']])
        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.input = cls.stage_model.search(
            [['name', '=', 'Input Queue']])
        cls.testready = cls.stage_model.search(
            [['name', '=', 'Test Ready']])
        cls.rel_ready = cls.stage_model.search(
            [['name', '=', 'Release Ready']])
        cls.analysis = cls.stage_model.search([['name', '=', 'Analysis']])
        cls.dev = cls.stage_model.search([['name', '=', 'Development']])
        cls.review = cls.stage_model.search([['name', '=', 'Testing']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])
        cls.other = cls.stage_model.search([['name', '=', 'Release']])

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

    def test_01_write_wip_limit_raises_if_backlog(self):
        with self.assertRaises(except_orm):
            self.backlog.wip_limit = 10

    def test_02_write_wip_limit_raises_if_queue(self):
        with self.assertRaises(except_orm):
            self.queue.wip_limit = 10

    def test_03_write_wip_limit_raises_if_done(self):
        with self.assertRaises(except_orm):
            self.done.wip_limit = 10

    def test_04_write_type_to_backlog_removes_wip_limit(self):
        self.analysis.wip_limit = 10
        self.analysis.stage_type = 'backlog'
        self.assertFalse(self.analysis.wip_limit)
        self.analysis.stage_type = 'analysis'

    def test_05_write_type_to_queue_removes_wip_limit(self):
        self.analysis.wip_limit = 10
        self.analysis.stage_type = 'queue'
        self.assertFalse(self.analysis.wip_limit)
        self.analysis.stage_type = 'analysis'

    def test_06_write_type_to_done_removes_wip_limit(self):
        self.analysis.wip_limit = 10
        self.analysis.stage_type = 'done'
        self.assertFalse(self.analysis.wip_limit)
        self.analysis.stage_type = 'analysis'

    def test_07_current_wip_items_count_tasks_related_to_stage(self):
        self.assertEqual(self.other.current_wip_items()[0], 0)
        self.task.stage_id = self.other.id
        self.assertEqual(self.other.current_wip_items()[0], 1)

    def test_08_current_wip_items_count_tasks_related_to_stage_queues(self):
        self.task.stage_id = self.backlog.id
        self.assertEqual(self.other.current_wip_items()[0], 0)
        self.task.stage_id = self.rel_ready.id
        self.assertEqual(self.rel_ready.current_wip_items()[0], 1)
        self.assertEqual(self.other.current_wip_items()[0], 1)

    def test_09_check_wip_limit_return_warning_if_overloaded(self):
        self.other.wip_limit = 1
        self.task.stage_id = self.other.id
        self.task2.stage_id = self.other.id
        self.assertEqual(self.other.check_wip_limit()[0],
                         'Release stage is overloaded')
        self.assertEqual(self.task.check_stage_limit(self.other.id)[0],
                         'Release stage is overloaded')

    def test_10_check_wip_limit_no_warning_if_limit_is_0(self):
        self.other.wip_limit = 0
        self.assertFalse(self.other.check_wip_limit()[0])
        self.assertFalse(self.task_model.check_stage_limit(self.other.id))

    def test_11_check_wip_limit_return_warning_if_overloaded_using_queue(self):
        self.other.wip_limit = 1
        self.task.stage_id = self.rel_ready.id
        self.assertEqual(self.other.check_wip_limit()[0],
                         'Release stage is overloaded')
        self.assertEqual(self.task2.check_stage_limit(self.other.id)[0],
                         'Release stage is overloaded')
        self.assertEqual(self.rel_ready.check_wip_limit()[0],
                         'Release stage is overloaded')
        self.assertEqual(self.task.check_stage_limit(self.rel_ready.id)[0],
                         'Release stage is overloaded')
