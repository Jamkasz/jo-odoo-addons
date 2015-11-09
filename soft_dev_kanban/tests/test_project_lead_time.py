from openerp.tests import common


class TestProjectLeadTime(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProjectLeadTime, cls).setUpClass()
        cls.project_model = cls.env['project.project']
        cls.project = cls.project_model.search(
            [['name', '=', 'Upgrade to Odoo 9']])
        cls.project2 = cls.project_model.search(
            [['name', '=', 'Kanban Odoo Module']])

    def test_01_compute_average_time_is_0_if_project_has_no_tasks(self):
        self.project._compute_average_time()
        self.assertEqual(self.project.average_lead_time, 0)

    def test_02_update_task_dates_without_history_logs_does_not_update_dates(self):
        self.project.update_task_dates()
        for task in self.project.task_ids:
            self.assertFalse(task.date_in)
            self.assertFalse(task.date_out)

    def test_03_update_task_dates_updates_date_in_and_date_out(self):
        self.project2.update_task_dates()
        for task in self.project2.task_ids:
            if task.name == 'Tasks Lead Time':
                self.assertEqual(task.date_in, '2015-10-19 08:00:00')
                self.assertEqual(task.date_out, '2015-10-19 17:00:00')

    def test_04_compute_average_time_returns_average_working_hours(self):
        self.project2._compute_average_time()
        self.assertEqual(self.project2.average_lead_time, 8)
