from openerp.tests import common
from openerp.models import except_orm


class TestCosParentOption(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosParentOption, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.tag_model = cls.env['project.category']
        cls.cos_model = cls.env['sdk.class_of_service']

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

        cls.cos_feature = cls.cos_model.search([['name', '=', 'Feature']])
        cls.cos_demo = cls.cos_model.search([['name', '=', 'Demo CoS']])
        cls.tag_feature = cls.tag_model.search([['name', '=', 'Feature']])
        cls.tag_demo = cls.tag_model.search([['name', '=', 'Demo Tag']])

    def test_01_check_feature_id_raises_if_not_feature(self):
        with self.assertRaises(except_orm):
            self.task.check_feature_id(self.task2.id)

    def test_02_write_feature_id_raises_if_not_feature(self):
        with self.assertRaises(except_orm):
            self.task.feature_id = self.task2.id

    def test_03_check_feature_id_raises_if_task_is_feature(self):
        self.task2.categ_ids = [self.tag_feature.id]
        with self.assertRaises(except_orm):
            self.task2.check_feature_id(self.task.id)

    def test_04_write_feature_id_raises_if_task_is_feature(self):
        with self.assertRaises(except_orm):
            self.task2.feature_id = self.task.id

    def test_05_fields_view_get_feature_id_domain_excludes_non_features(self):
        res = self.task_model.fields_view_get(view_type='form')
        self.assertTrue(res['fields'].get('feature_id'))
        self.assertListEqual(
            res['fields']['feature_id'].get('domain'),
            [['id', 'in', [self.task2.id]]])

    def test_06_fields_view_get_feature_id_invisible_if_task_feature(self):
        res = self.task_model.fields_view_get(view_type='form')
        self.assertTrue(res['fields'].get('feature_id'))
        self.assertDictEqual(
            res['fields']['feature_id'].get('attrs'),
            {'invisible': [['id', 'in', [self.task2.id]]]})
