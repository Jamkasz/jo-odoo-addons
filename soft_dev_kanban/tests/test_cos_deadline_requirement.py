from openerp.tests import common
from openerp.models import except_orm
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class TestCosDeadlineRequirement(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosDeadlineRequirement, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.tag_model = cls.env['project.category']
        cls.cos_model = cls.env['sdk.class_of_service']

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

        cls.cos_urgent = cls.cos_model.search([['name', '=', 'Urgent']])
        cls.cos_demo = cls.cos_model.search([['name', '=', 'Demo CoS']])
        cls.tag_urgent = cls.tag_model.search([['name', '=', 'Urgent']])
        cls.tag_demo = cls.tag_model.search([['name', '=', 'Demo Tag']])
        cls.cos_urgent.limit = 0

    def test_01_tag_check_deadline_required_raises_if_no_deadline(self):
        with self.assertRaises(except_orm):
            self.tag_urgent.check_deadline_required(False)

    def test_02_tag_check_deadline_required_raises_if_deadline(self):
        self.cos_demo.deadline = 'nodate'
        with self.assertRaises(except_orm):
            self.tag_demo.check_deadline_required(True)

    def test_03_tag_check_deadline_required_not_raises_if_not_required(self):
        self.cos_demo.deadline = 'noreq'
        self.assertTrue(self.tag_demo.check_deadline_required(True))

    def test_04_task_create_raises_if_cos_req_deadline_and_no_deadline(self):
        with self.assertRaises(except_orm):
            self.task_model.create({
                'name': 'Test Task',
                'categ_ids': [[6, 0, [self.tag_urgent.id]]]})

    def test_05_task_write_raises_if_cos_req_deadline_and_no_deadline(self):
        with self.assertRaises(except_orm):
            self.task.categ_ids = [self.tag_urgent.id]

    def test_06_task_create_raises_if_cos_req_no_deadline_and_deadline(self):
        self.cos_demo.deadline = 'nodate'
        with self.assertRaises(except_orm):
            self.task_model.create({
                'name': 'Test Task',
                'date_deadline': dt.today().strftime(DF),
                'categ_ids': [[6, 0, [self.tag_demo.id]]]})

    def test_07_task_write_raises_if_cos_req_no_deadline_and_deadline(self):
        self.task.date_deadline = dt.today().strftime(DF)
        with self.assertRaises(except_orm):
            self.task.categ_ids = [self.tag_demo.id]
