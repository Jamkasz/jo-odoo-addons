from openerp.tests import common
from openerp.models import except_orm


class TestCosLimitTaskAmount(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosLimitTaskAmount, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.stage_model = cls.env['project.task.type']
        cls.cos_model = cls.env['sdk.class_of_service']
        cls.tag_model = cls.env['project.category']

        cls.done = cls.stage_model.search([['name', '=', 'Done']])

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

        cls.cos_urgent = cls.cos_model.search([['name', '=', 'Urgent']])
        cls.cos_demo = cls.cos_model.search([['name', '=', 'Demo CoS']])
        cls.tag_urgent = cls.tag_model.search([['name', '=', 'Urgent']])
        cls.tag_demo = cls.tag_model.search([['name', '=', 'Demo Tag']])

    def test_01_finished_task_does_not_count_towards_cos_limit_amount(self):
        task = self.task_model.create({
            'name': 'Test Task',
            'categ_ids': [[6, 0, [self.tag_urgent.id]]]})
        task.stage_id = self.done.id
        self.assertTrue(self.task.write({
            'categ_ids': [[6, 0, [self.tag_urgent.id]]]}))

    def test_02_task_create_raises_if_cos_limit_overflow(self):
        self.task.categ_ids = [self.tag_urgent.id]
        with self.assertRaises(except_orm):
            self.task_model.create({
                'name': 'Test Task',
                'categ_ids': [[6, 0, [self.tag_urgent.id]]]})

    def test_03_task_create_does_not_raise_if_cos_limit_0(self):
        self.assertTrue(self.task_model.create({
            'name': 'Test Task',
            'categ_ids': [[6, 0, [self.tag_demo.id]]]}))

    def test_04_task_write_raises_if_cos_limit_overflow(self):
        with self.assertRaises(except_orm):
            self.task2.categ_ids = [self.tag_urgent.id]

    def test_05_task_write_does_not_raise_if_cos_limit_0(self):
        self.assertTrue(self.task2.write({
            'categ_ids': [[6, 0, [self.tag_demo.id]]]}))

    def test_06_tag_write_raises_if_cos_limit_overflow(self):
        with self.assertRaises(except_orm):
            self.tag_demo.cos_id = self.cos_urgent.id

    def test_07_tag_write_does_not_raise_if_cos_limit_0(self):
        self.assertTrue(self.tag_urgent.write({'cos_id': self.cos_demo.id}))
