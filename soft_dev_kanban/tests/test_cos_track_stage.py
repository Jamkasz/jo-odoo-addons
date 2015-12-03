from openerp.tests import common
from openerp.models import except_orm


class TestCosParentOption(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosParentOption, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.stage_model = cls.env['project.task.type']
        cls.tag_model = cls.env['project.category']
        cls.cos_model = cls.env['sdk.class_of_service']

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])
        cls.task3 = cls.task_model.search([['name', '=', 'Tasks Lead Time']])

        cls.queue = cls.stage_model.search(
            [['name', '=', 'Development Ready']])
        cls.dev = cls.stage_model.search(
            [['name', '=', 'Development']])
        cls.done = cls.stage_model.search([['name', '=', 'Done']])

        cls.cos_feature = cls.cos_model.search([['name', '=', 'Feature']])
        cls.cos_demo = cls.cos_model.search([['name', '=', 'Demo CoS']])
        cls.tag_feature = cls.tag_model.search([['name', '=', 'Feature']])
        cls.tag_demo = cls.tag_model.search([['name', '=', 'Demo Tag']])

    def test_01_get_tracked_stage_id_returns_false_if_not_feature(self):
        self.assertFalse(self.task.get_tracked_stage_id()[0])

    def test_02_get_tracked_stage_id_returns_false_if_no_childs(self):
        self.task.categ_ids = [self.tag_feature.id]
        self.assertFalse(self.task.get_tracked_stage_id()[0])

    def test_03_get_tracked_stage_id_returns_child_stage(self):
        self.task2.write({'feature_id': self.task.id,
                          'stage_id': self.queue.id})
        self.assertEqual(self.task.get_tracked_stage_id()[0], self.queue.id)

    def test_04_update_feature_stage_tracking_updates_stage(self):
        self.task2.update_feature_stage_tracking()
        self.assertEqual(self.task.stage_id.id, self.queue.id)

    def test_05_get_tracked_stage_id_rets_earliest_child_task_stage(self):
        self.task3.write({'feature_id': self.task.id,
                          'stage_id': self.dev.id})
        self.task2.stage_id = self.done.id
        self.assertEqual(self.task.get_tracked_stage_id()[0], self.dev.id)

    def test_06_update_feature_stage_tracking_rets_if_no_feature(self):
        self.assertTrue(self.task.update_feature_stage_tracking()[0])

    def test_07_write_task_stage_updates_feature_tracking_stage(self):
        self.task3.stage_id = self.done.id
        self.assertEqual(self.task.stage_id.id, self.done.id)

    def test_08_create_cos_track_stage_without_can_be_parent_raises(self):
        with self.assertRaises(except_orm):
            self.cos_model.create({'name': 'Test CoS', 'track_stage': True})

    def test_09_write_cos_track_stage_without_can_be_parent_raises(self):
        with self.assertRaises(except_orm):
            self.cos_demo.track_stage = True

    def test_10_remove_can_be_parent_removes_track_stage_too(self):
        self.cos_feature.can_be_parent = False
        self.assertFalse(self.cos_feature.track_stage)

    def test_11_update_feature_stage_tracking_rets_if_no_tracker(self):
        tasks = self.task_model.browse([self.task.id, self.task2.id,
                                        self.task3.id])
        tasks.write({'feature_id': False, 'categ_ids': False})
        self.cos_demo.can_be_parent = True
        self.task2.write({'categ_ids': [[6, 0, [self.tag_demo.id]]],
                          'stage_id': self.queue.id})
        self.task.feature_id = self.task2.id
        self.assertTrue(self.task.update_feature_stage_tracking()[0])
        self.assertEqual(self.task2.stage_id.id, self.queue.id)
