from openerp.tests import common
from openerp.models import except_orm


class TestStageRelatedStage(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStageRelatedStage, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.stage_model = cls.env['project.task.type']
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search(
            [['name', '=', 'Tasks Lead Time']])
        cls.backlog = cls.stage_model.search(
            [['name', '=', 'Backlog']])
        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.dev = cls.stage_model.search(
            [['name', '=', 'Development']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])

    def test_01_write_related_stage_raises_if_target_is_queue_type(self):
        with self.assertRaises(except_orm):
            self.queue.related_stage_id = self.queue.id

    def test_02_write_related_stage_raises_if_target_is_backlog_type(self):
        with self.assertRaises(except_orm):
            self.queue.related_stage_id = self.backlog.id

    def test_03_write_related_stage_raises_if_source_is_not_queue_type(self):
        with self.assertRaises(except_orm):
            self.backlog.related_stage_id = self.dev.id

    def test_04_write_stage_type_to_non_queue_removes_related_stage(self):
        self.queue.stage_type = 'other'
        self.assertFalse(self.queue.related_stage_id)

    def test_05_onchange_related_stage_id_returns_warning(self):
        self.assertDictEqual(
            self.backlog.onchange_related_stage_id(),
            {
                'warning':
                    {'message': 'Only queue stages can have a related stage',
                     'title': 'Warning'}
            })
        self.assertFalse(self.backlog.related_stage_id)
