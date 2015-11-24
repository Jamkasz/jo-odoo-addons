from openerp.tests import common
from openerp.models import except_orm
from datetime import datetime as dt, timedelta as td
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
        cls.cos_demo.dynamic_priority = 'deadline'
        cls.cos_demo.deadline_normal = 3
        cls.cos_demo.deadline_high = 1.5
        cls.cos_demo.time_normal = 3
        cls.cos_demo.time_high = 7
        cls.cos_urgent.limit = 0
        cls.cos_urgent.deadline = 'noreq'
        cls.task.categ_ids = [cls.tag_urgent.id]

    def test_01_get_dynamic_priority_ret_minus_1_if_not_dynamic(self):
        self.assertEqual(self.task.get_dynamic_priority()[0], False)

    def test_02_get_dynamic_priority_ret_minus_1_if_no_deadline(self):
        self.task.priority = '0'
        self.assertEqual(self.task.get_dynamic_priority()[0], False)

    def test_03_get_dynamic_priority_ret_minus_1_if_no_leadtime(self):
        self.task.date_deadline = dt.now() + td(days=1)
        self.assertEqual(self.task.get_dynamic_priority()[0], False)

    def test_04_get_dynamic_priority_ret_0_if_more_than_leadtime_n(self):
        self.task.categ_ids = [[6, 0, [self.tag_demo.id]]]
        self.task.date_deadline = dt.now() + td(days=30)
        self.task2.date_in = '2015-10-05 00:00:00'
        self.task2.date_out = '2015-10-10 00:00:00'
        self.task2.project_id._compute_average_time()
        self.assertEqual(self.task.get_dynamic_priority()[0], '0')

    def test_05_get_dynamic_priority_ret_1_if_between_leadtime_n_and_h(self):
        self.task.date_deadline = dt.now() + td(days=14)
        self.assertEqual(self.task.get_dynamic_priority()[0], '1')

    def test_06_get_dynamic_priority_ret_2_if_less_than_leadtime_h(self):
        self.task.date_deadline = dt.now() + td(days=5)
        self.assertEqual(self.task.get_dynamic_priority()[0], '2')

    def test_07_get_dynamic_priority_ret_0_if_less_than_stage_time_n(self):
        self.cos_demo.dynamic_priority = 'blocked'
        self.task.write({'date_last_stage_update': dt.now()})
        self.assertEqual(self.task.get_dynamic_priority()[0], '0')

    def test_08_get_dynamic_priority_ret_1_if_between_stage_time_n_and_h(self):
        self.task.write({'date_last_stage_update': dt.now()-td(days=4)})
        self.assertEqual(self.task.get_dynamic_priority()[0], '1')

    def test_09_get_dynamic_priority_ret_2_if_more_than_stage_time_h(self):
        self.task.write({'date_last_stage_update': dt.now()-td(days=8)})
        self.assertEqual(self.task.get_dynamic_priority()[0], '2')

    def test_10_task_changes_to_low_priority_no_leadtime_reached(self):
        self.cos_demo.dynamic_priority = 'deadline'
        self.task.date_deadline = dt.now() + td(days=30)
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '0')

    def test_11_task_changes_to_normal_priority_1st_leadtime_reached(self):
        self.task.date_deadline = dt.now() + td(days=14)
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '1')

    def test_12_task_changes_to_high_priority_if_2nd_leadtime_reached(self):
        self.task.date_deadline = dt.now() + td(days=5)
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '2')

    def test_13_task_changes_to_low_priority_no_stage_time_reached(self):
        self.cos_demo.dynamic_priority = 'blocked'
        self.task.write({'date_last_stage_update': dt.now()})
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '0')

    def test_14_task_changes_to_normal_priority_1st_stage_time_reached(self):
        self.task.write({'date_last_stage_update': dt.now()-td(days=4)})
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '1')

    def test_15_task_changes_to_high_priority_if_2nd_stage_time_reached(self):
        self.task.write({'date_last_stage_update': dt.now()-td(days=8)})
        self.task._compute_priority()
        self.assertEqual(self.task.dynamic_priority, '2')
