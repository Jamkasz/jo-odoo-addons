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
