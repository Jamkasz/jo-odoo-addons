from openerp.tests import common


class TestLogMessageWizard(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestLogMessageWizard, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.message_model = cls.env['mail.message']
        cls.user_model = cls.env['res.users']
        cls.team_model = cls.env['sdk.user.team']
        cls.stage_model = cls.env['project.task.type']
        cls.log_model = cls.env['log.message.wizard']

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
        cls.team2 = cls.team_model.search([['name', '=', 'SDK Demo Team 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])

    def test_01_write_log_message_logs_message_on_task(self):
        wizard = self.log_model.create({'res_model': 'project.task',
                                        'res_id': self.task.id,
                                        'subject': 'Test'})
        wizard.message = 'test message'
        messages = self.message_model.search([
            ['type', '=', 'comment'], ['model', '=', 'project.task'],
            ['res_id', '=', self.task.id], ['subject', '=', 'Test'],
            ['message', '=', 'test message']])
        self.assertTrue(messages)

    def test_02_write_log_not_message_field_does_not_log_message_on_task(self):
        wizard = self.log_model.create({'res_model': 'project.task',
                                        'res_id': self.task.id,
                                        'subject': 'Test'})
        wizard.subject = 'Test 2'
        messages = self.message_model.search([
            ['type', '=', 'comment'], ['model', '=', 'project.task'],
            ['res_id', '=', self.task.id], ['subject', '=', 'Test 2']])
        self.assertFalse(messages)
