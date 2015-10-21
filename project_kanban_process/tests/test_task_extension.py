from openerp.tests import common
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf
from openerp.models import except_orm


class TestTaskExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTaskExtension, cls).setUpClass()
        cls.task_model = cls.env['project.task']
        cls.stage_model = cls.env['project.task.type']
        cls.project_model = cls.env['project.project']
        cls.log_model = cls.env['project.task.history']
        cls.calendar_model = cls.env['resource.calendar']
        cls.attendance_model = cls.env['resource.calendar.attendance']

        cls.stage = cls.stage_model.create({'name': 'TEST STAGE'})
        cls.stage2 = cls.stage_model.create({'name': 'TEST STAGE 2'})
        cls.cal = cls.calendar_model.create({'name': 'TEST CALENDAR'})
        for i in range(4):
            cls.attendance_model.create({
                'name': 'AT0' + str(i), 'dayofweek': str(i), 'hour_from': 10.0,
                'hour_to': 18.0, 'calendar_id': cls.cal.id
            })
        cls.project = cls.project_model.create({'name': 'TEST PROJECT', 'type_ids': [cls.stage.id, cls.stage2.id],
                                                'resource_calendar_id': cls.cal.id})
        cls.task = cls.task_model.create({
            'name': 'TEST TASK', 'project_id': cls.project.id, 'date_start': '1988-10-24 11:20:00',
            'date_end': '1988-10-24 12:30:00'})
        cls.task2 = cls.task_model.create({
            'name': 'TEST TASK2', 'project_id': cls.project.id, 'date_start': '1988-10-24 09:00:00',
            'date_end': '1988-10-25 19:00:00'})

    def test_01_get_working_hours_raises_exception_with_non_datetime_start_date(self):
        with self.assertRaises(except_orm):
            self.task.get_working_hours('date1', dt.now())

    def test_02_get_working_hours_raises_exception_with_non_datetime_end_date(self):
        with self.assertRaises(except_orm):
            self.task.get_working_hours(dt.now(), 'date2')

    def test_03_get_working_hours_same_day_within_calendar_times(self):
        start = dt.strptime('2015-10-19 10:00:00', dtf)
        end = dt.strptime('2015-10-19 15:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 5)

    def test_04_get_working_hours_same_day_outside_calendar_times(self):
        start = dt.strptime('2015-10-19 08:00:00', dtf)
        end = dt.strptime('2015-10-19 15:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 5)

    def test_05_get_working_hours_different_day(self):
        start = dt.strptime('2015-10-19 08:00:00', dtf)
        end = dt.strptime('2015-10-20 12:00:00', dtf)
        self.assertEqual(self.task.get_working_hours(start, end)[0], 10)

    def test_06_stage_working_hours_raises_exception_with_non_datetime_date(self):
        with self.assertRaises(except_orm):
            self.task.stage_working_hours(1, 'date')

    def test_07_stage_working_hours_no_stage(self):
        self.assertEqual(self.task.stage_working_hours(1, dt.now())[0], 0)

    def test_08_stage_working_hours(self):
        self.task2.stage_id = self.stage.id
        self.log_model.create({
            'task_id': self.task2.id,
            'type_id': self.stage.id,
            'date': '1988-10-24 09:00:00'
        })
        self.log_model.create({
            'task_id': self.task2.id,
            'type_id': self.stage2.id,
            'date': '1988-10-24 17:00:00'
        })
        self.log_model.create({
            'task_id': self.task2.id,
            'type_id': self.stage.id,
            'date': '1988-10-25 10:00:00'
        })
        self.assertEqual(self.task2.stage_working_hours(self.stage.id, dt.strptime('1988-10-25 19:00:00', dtf))[0], 15)
