from openerp.tests import common


class TestCosIgnoresWipLimit(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosIgnoresWipLimit, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.stage_model = cls.env['project.task.type']
        cls.tag_model = cls.env['project.category']
        cls.team_model = cls.env['sdk.user.team']

        cls.analysis = cls.stage_model.search([['name', '=', 'Analysis']])
        cls.dev = cls.stage_model.search([['name', '=', 'Development']])
        cls.review = cls.stage_model.search([['name', '=', 'Testing']])

        cls.user = cls.user_model.search([['name', '=', 'SDK Demo User']])
        cls.user2 = cls.user_model.search([['name', '=', 'SDK Demo User 2']])
        cls.task = cls.task_model.search(
            [['name', '=', 'Refactor Tests Code']])
        cls.task2 = cls.task_model.search([['name', '=', 'WIP Management']])
        cls.team = cls.team_model.search([['name', '=', 'SDK Demo Team']])

        cls.tag_urgent = cls.tag_model.search([['name', '=', 'Urgent']])
        cls.task.categ_ids = [cls.tag_urgent.id]

    def test_01_ignore_wip_limit_is_true_linked_with_ignore_limit_cos(self):
        self.assertTrue(self.task.ignore_wip_limit()[0])

    def test_02_ignore_wip_limit_false_not_linked_with_ignore_limit_cos(self):
        self.assertFalse(self.task2.ignore_wip_limit()[0])

    def test_03_task_check_wip_limit_does_not_warn_with_ignore_limit_cos(self):
        self.user.wip_limit = 1
        self.task.write({'user_id': self.user.id, 'stage_id': self.dev.id})
        self.task2.write({'user_id': self.user.id, 'stage_id': self.dev.id})
        self.assertFalse(self.task.check_wip_limit(self.dev.id)[0])

    def test_04_onchange_user_id_does_not_warn_with_ignore_limit_cos(self):
        self.assertFalse(self.task.onchange_user_id())

    def test_05_onchange_analyst_id_does_not_warn_with_ignore_limit_cos(self):
        self.task.write({'analyst_id': self.user.id,
                         'stage_id': self.analysis.id})
        self.task2.write({'analyst_id': self.user.id,
                          'stage_id': self.analysis.id})
        self.assertFalse(self.task.onchange_analyst_id())

    def test_06_onchange_reviewer_id_does_not_warn_with_ignore_limit_cos(self):
        self.task.write({'reviewer_id': self.user.id,
                         'stage_id': self.review.id})
        self.task2.write({'reviewer_id': self.user.id,
                          'stage_id': self.review.id})
        self.assertFalse(self.task.onchange_reviewer_id())

    def test_07_team_check_wip_limit_does_not_warn_with_ignore_limit_cos(self):
        self.user.wip_limit = 0
        self.team.wip_limit = 1
        self.task.write({'user_id': self.user.id, 'stage_id': self.dev.id})
        self.task2.write({'user_id': self.user2.id, 'stage_id': self.dev.id})
        self.assertFalse(self.task.check_team_limit(self.dev.id)[0])

    def test_08_onchange_user_id_does_not_warn_team_overload(self):
        self.assertFalse(self.task.onchange_user_id())

    def test_09_onchange_analyst_id_does_not_warn_team_overload(self):
        self.task.write({'analyst_id': self.user.id,
                         'stage_id': self.analysis.id})
        self.task2.write({'analyst_id': self.user.id,
                          'stage_id': self.analysis.id})
        self.assertFalse(self.task.onchange_analyst_id())

    def test_10_onchange_reviewer_id_does_not_warn_team_overload(self):
        self.task.write({'reviewer_id': self.user.id,
                         'stage_id': self.review.id})
        self.task2.write({'reviewer_id': self.user.id,
                          'stage_id': self.review.id})
        self.assertFalse(self.task.onchange_reviewer_id())

    def test_11_stage_check_wip_limit_does_not_warn_with_ignore_limit(self):
        self.dev.wip_limit = 1
        self.task.write({'user_id': self.user.id, 'stage_id': self.dev.id})
        self.task2.write({'user_id': self.user2.id, 'stage_id': self.dev.id})
        self.assertFalse(self.task.check_stage_limit(self.dev.id)[0])
