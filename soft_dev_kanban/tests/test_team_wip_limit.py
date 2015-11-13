from openerp.tests import common


class TestTeamWipLimit(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTeamWipLimit, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.team_model = cls.env['sdk.user.team']
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
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.team = cls.team_model.search([['name', '=', 'SDK Demo Team']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

    def test_01_current_wip_items_count_developer_items_on_dev_stage(self):
        self.task.stage_id = self.dev.id
        self.task2.stage_id = self.dev.id
        self.assertEqual(self.team.current_wip_items()[0], 0)
        self.task.user_id = self.user.id
        self.assertEqual(self.team.current_wip_items()[0], 1)
        self.task2.user_id = self.user2.id
        self.assertEqual(self.team.current_wip_items()[0], 2)

    def test_02_current_wip_items_count_developer_items_on_dev_queue(self):
        self.task.stage_id = self.queue.id
        self.task2.stage_id = self.queue.id
        self.assertEqual(self.team.current_wip_items()[0], 2)

    def test_03_current_wip_items_count_reviewer_items_on_review_stage(self):
        self.task.stage_id = self.review.id
        self.task2.stage_id = self.review.id
        self.assertEqual(self.team.current_wip_items()[0], 0)
        self.task.reviewer_id = self.user.id
        self.assertEqual(self.team.current_wip_items()[0], 1)
        self.task2.reviewer_id = self.user2.id
        self.assertEqual(self.team.current_wip_items()[0], 2)

    def test_04_current_wip_items_count_reviewer_items_on_review_queue(self):
        self.task.stage_id = self.testready.id
        self.task2.stage_id = self.testready.id
        self.assertEqual(self.team.current_wip_items()[0], 2)

    def test_05_current_wip_items_count_analyst_items_on_analysis_stage(self):
        self.task.stage_id = self.analysis.id
        self.task2.stage_id = self.analysis.id
        self.assertEqual(self.team.current_wip_items()[0], 0)
        self.task.analyst_id = self.user.id
        self.assertEqual(self.team.current_wip_items()[0], 1)
        self.task2.analyst_id = self.user2.id
        self.assertEqual(self.team.current_wip_items()[0], 2)

    def test_06_current_wip_items_count_analyst_items_on_analysis_queue(self):
        self.task.stage_id = self.input.id
        self.task2.stage_id = self.input.id
        self.assertEqual(self.team.current_wip_items()[0], 2)
