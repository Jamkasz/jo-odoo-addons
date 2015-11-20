from openerp.tests import common


class TestCosTasksKanbanColour(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCosTasksKanbanColour, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.user_model = cls.env['res.users']
        cls.stage_model = cls.env['project.task.type']
        cls.cos_model = cls.env['sdk.class_of_service']
        cls.tag_model = cls.env['project.category']

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
        cls.cos_urgent.deadline = 'noreq'

    def test_01_tag_get_cos_color_returns_highest_priority_color(self):
        self.assertFalse(self.tag_demo.get_cos_colour())
        self.assertEqual(self.tag_urgent.get_cos_colour(), 9)
        tags = self.tag_model.browse([self.tag_demo.id, self.tag_urgent.id])
        self.assertEqual(tags.get_cos_colour(), 9)

    def test_02_task_create_assigns_cos_color(self):
        task = self.task_model.create({
            'name': 'Test Task',
            'categ_ids': [[6, 0, [self.tag_urgent.id]]]})
        self.assertEqual(task.color, 9)

    def test_03_task_write_assigns_cos_color(self):
        self.task.color = 0
        self.task.write({'categ_ids': [[6, 0, [self.tag_urgent.id]]]})
        self.assertEqual(self.task.color, 9)

    def test_04_tag_write_assigns_cos_color_to_tasks(self):
        self.task.color = 0
        self.task.write({'categ_ids': [[6, 0, [self.tag_demo.id]]]})
        self.tag_demo.cos_id = self.cos_urgent.id
        self.assertEqual(self.task.color, 9)

    def test_05_cos_write_color_assigns_new_color_to_tasks(self):
        self.task.color = 0
        self.cos_urgent.colour = 8
        self.assertEqual(self.task.color, 8)

    def test_06_cos_write_color_priority_reassigns_cos_color_to_tasks(self):
        self.task2.categ_ids = [self.tag_urgent.id, self.tag_demo.id]
        self.tag_demo.cos_id = self.cos_demo.id
        self.cos_urgent.colour = 9
        self.cos_demo.colour = 1
        self.cos_urgent.priority = 10
        self.cos_demo.priority = 1
        self.assertEqual(self.task2.color, 1)
