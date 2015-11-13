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

    # def test_01_write_wip_limit_raises_if_backlog(self):
