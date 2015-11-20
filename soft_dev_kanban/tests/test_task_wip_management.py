from openerp.tests import common


class TestTaskWipManagement(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTaskWipManagement, cls).setUpClass()
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

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

    def test_01_write_stage_from_analysis_adds_analyst_wi_finished(self):
        self.task.analyst_id = self.user.id
        self.task.stage_id = self.analysis.id
        self.task.stage_id = self.dev.id
        self.assertEqual(self.user.wi_finished, 1)

    def test_02_write_stage_from_dev_adds_dev_wi_finished(self):
        self.task.user_id = self.user.id
        self.task.stage_id = self.review.id
        self.assertEqual(self.user.wi_finished, 2)

    def test_03_write_stage_from_review_adds_reviewer_wi_finished(self):
        self.task.reviewer_id = self.user.id
        self.task.stage_id = self.queue.id
        self.assertEqual(self.user.wi_finished, 3)

    def test_04_check_wip_limit_dev_stage_return_warning_if_overloaded(self):
        self.user.wip_limit = 1
        self.task2.user_id = self.user.id
        self.task.stage_id = self.dev.id
        self.task2.stage_id = self.dev.id
        self.assertEqual(self.task.check_wip_limit(self.dev.id)[0],
                         'SDK Demo User is overloaded')

    def test_05_onchange_user_id_returns_warning(self):
        self.assertDictEqual(
            self.task.onchange_user_id(),
            {
                'warning':
                    {'message': 'SDK Demo User is overloaded',
                     'title': 'Warning'}
            })

    def test_06_check_wip_limit_dev_queue_return_warning_if_overloaded(self):
        self.task.stage_id = self.queue.id
        self.assertEqual(self.task.check_wip_limit(self.queue.id)[0],
                         'SDK Demo User is overloaded')

    def test_07_check_wip_limit_analysis_return_warning_if_overloaded(self):
        self.task.stage_id = self.analysis.id
        self.assertEqual(self.task.check_wip_limit(self.analysis.id)[0],
                         'SDK Demo User is overloaded')

    def test_08_onchange_analyst_id_returns_warning(self):
        self.assertDictEqual(
            self.task.onchange_analyst_id(),
            {
                'warning':
                    {'message': 'SDK Demo User is overloaded',
                     'title': 'Warning'}
            })

    def test_09_check_wip_limit_analysis_queue_warns_if_overloaded(self):
        self.task.stage_id = self.input.id
        self.assertEqual(self.task.check_wip_limit(self.input.id)[0],
                         'SDK Demo User is overloaded')

    def test_10_check_wip_limit_review_return_warning_if_overloaded(self):
        self.task.stage_id = self.review.id
        self.assertEqual(self.task.check_wip_limit(self.review.id)[0],
                         'SDK Demo User is overloaded')

    def test_11_onchange_reviewer_id_returns_warning(self):
        self.assertDictEqual(
            self.task.onchange_reviewer_id(),
            {
                'warning':
                    {'message': 'SDK Demo User is overloaded',
                     'title': 'Warning'}
            })

    def test_12_check_wip_limit_review_queue_warns_if_overloaded(self):
        self.task.stage_id = self.testready.id
        self.assertEqual(self.task.check_wip_limit(self.testready.id)[0],
                         'SDK Demo User is overloaded')

    def test_13_check_wip_limit_other_stage_does_not_return_warning(self):
        self.task.stage_id = self.backlog.id
        self.assertFalse(self.task.check_wip_limit(self.backlog.id)[0])

    def test_14_check_wip_limit_no_warning_if_limit_is_0(self):
        self.user.wip_limit = 0
        self.assertFalse(self.task2.check_wip_limit(self.dev.id)[0])

    def test_15_onchange_user_id_no_warning_if_limit_is_0(self):
        self.assertFalse(self.task2.onchange_user_id())

    def test_16_onchange_analyst_id_no_warning_if_limit_is_0(self):
        self.task2.analyst_id = self.user.id
        self.task2.stage_id = self.analysis.id
        self.assertFalse(self.task2.onchange_analyst_id())

    def test_17_onchange_reviewer_id_no_warning_if_limit_is_0(self):
        self.task2.reviewer_id = self.user.id
        self.task2.stage_id = self.review.id
        self.assertFalse(self.task2.onchange_reviewer_id())
