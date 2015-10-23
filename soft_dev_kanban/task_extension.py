"""
`task_extension.py` extends the `project.task` Odoo model adding
extra functionality to provide a better kanban process experience.
"""
from openerp import models, fields, api
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class ProjectTaskHistoryExtension(models.Model):
    """
    Extends `project.task.history` Odoo model to change the ``date``
    field to `datetime` type.
    """
    _name = 'project.task.history'
    _inherit = 'project.task.history'

    date = fields.Datetime('Date', select=True)


class ProjectTaskExtension(models.Model):
    """
    Extends `project.task` Odoo model
    """
    _name = 'project.task'
    _inherit = 'project.task'

    total_time = fields.Integer(
        string='Lead Time', compute='_compute_total_time',
        store=False, readonly=True)
    # TODO internal_time = fields.Integer(string='Internal Lead Time', compute='_compute_internal_time', store=False, readonly=True)
    stage_time = fields.Integer(
        string='Stage Working Hours', compute='_compute_stage_time',
        store=False, readonly=True)

    @api.one
    def _store_history(self):
        """
        Overwrites Odoo `_store_history` so it stores a `datetime` on
        the ``date`` field instead of a `date`

        :returns: ``True``
        :rtype: bool
        """
        self.env['project.task.history'].create({
            'task_id': self.id,
            'remaining_hours': self.remaining_hours,
            'planned_hours': self.planned_hours,
            'kanban_state': self.kanban_state,
            'type_id': self.stage_id.id,
            'user_id': self.user_id.id,
            'date': dt.now()
        })
        return True

    @api.one
    def _compute_total_time(self):
        """
        Computes the total time elapsed between the creation date of the
        task until either the end date if exists or now, if it doesn't.

        If the task is related to a project with a working hours
        calendar, it returns only the working hours.

        :returns: time in hours
        :rtype: int
        """
        if self.date_end:
            date_end = dt.strptime(self.date_end, dtf)
        else:
            date_end = dt.now()
        self.total_time = self.get_working_hours(
            dt.strptime(self.date_start, dtf), date_end)[0]

    @api.one
    def _compute_stage_time(self):
        """
        Computes the total time elapsed from the first time the task
        reached its current stage until the end date if exists or now,
        if it doesn't.

        If the task is related to a project with a working hours
        calendar, it returns only the working hours.

        :returns: time in hours
        :rtype: int
        """
        if self.date_end:
            date_end = dt.strptime(self.date_end, dtf)
        else:
            date_end = dt.now()
        stage_id = self.stage_id.id
        self.stage_time = self.stage_working_hours(stage_id, date_end)[0]

    @api.one
    def get_working_hours(self, date_start, date_end):
        """
        Computes the working hours between two given dates using the
        calendar information from the related project.

        Does not check if the dates are consistent with the task start
        and end dates.

        :param date_start: Start time
        :type date_start: datetime
        :param date_end: End time
        :type date_end: datetime
        :raises: `models.except_orm`
        :returns: working hours
        :rtype: int
        """
        if not isinstance(date_start, dt):
            raise models.except_orm(
                'Attribute Error',
                'expected datetime, received %s' % type(date_start))
        if not isinstance(date_end, dt):
            raise models.except_orm(
                'Attribute Error',
                'expected datetime, received %s' % type(date_end))
        if self.project_id and self.project_id.resource_calendar_id:
            return int(self.project_id.resource_calendar_id.get_working_hours(
                date_start, date_end)[0])
        else:
            return int((date_end - date_start).total_seconds()/3600)

    @api.one
    def stage_working_hours(self, stage_id, date):
        """
        Computes the working hours spent in a given stage until a given
        date.

        :param stage_id: `project.task.type` id
        :type stage_id: int
        :param date: end date
        :type date: datetime
        :raises: `models.except_orm`
        :returns: working hours
        :rtype: int
        """
        if not isinstance(date, dt):
            raise models.except_orm(
                'Attribute Error',
                'expected datetime, received %s' % type(date))
        task_history_records = self.env['project.task.history'].search([
            ['task_id', '=', self.id], ['date', '<=', date.strftime(dtf)]],
            order='date asc')
        result = 0
        if task_history_records:
            add_time = False
            date_start = False
            for th in task_history_records:
                if add_time and isinstance(date_start, dt):
                    date_end = dt.strptime(th.date, dtf)
                    result += self.get_working_hours(date_start, date_end)[0]
                if stage_id == th.type_id.id:
                    add_time = True
                    date_start = dt.strptime(th.date, dtf)
                else:
                    add_time = False
            if add_time:
                result += self.get_working_hours(date_start, date)[0]
        elif self.stage_id.id == stage_id:
            date_start = dt.strptime(self.date_last_stage_update, dtf)
            result += self.get_working_hours(date_start, date)[0]
        return result
