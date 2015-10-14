"""
`task_extension.py` extends the `project.task` Odoo model adding
extra functionality to provide a better kanban process experience.
"""
from openerp import models, fields, api, _
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class ProjectTaskExtension(models.Model):
    """
    Extends `project.task` Odoo model
    """
    _name = 'project.task'
    _inherit = 'project.task'

    total_time = fields.Integer(string='Total Elapsed Time', compute='_compute_total_time', store=False, readonly=True)
    stage_time = fields.Integer(string='Stage Elapsed Time', compute='_compute_stage_time', store=False, readonly=True)

    def _compute_total_time(self):
        """
        Computes the total time elapsed between the creation date of the
        task until either the end date if exists or now, if it doesn't.

        :returns: time in hours
        :rtype: int
        """
        if not self.date_end:
            date_end = dt.now()
        else:
            date_end = dt.strptime(self.date_end, dtf)
        elapsed_time = (date_end - dt.strptime(self.create_date, dtf)).total_seconds()
        return int(elapsed_time/3600)

    def _compute_stage_time(self):
        """
        Computes the total time elapsed from the first time the task
        reached its current stage until the end date if exists or now,
        if it doesn't.

        :returns: time in hours
        :rtype: int
        """
        if not self.date_end:
            date_end = dt.now()
        else:
            date_end = dt.strptime(self.date_end, dtf)
        elapsed_time = (date_end - dt.strptime(self.date_last_stage_update, dtf)).total_seconds()
        task_history_records = self.env('project.task.history').search([['task_id', '=', self.id]], order='id asc')
        add_time = False
        date_start = False
        for th in task_history_records:
            if add_time and isinstance(date_start, dt):
                elapsed_time += (dt.strptime(th.create_date, dtf) - date_start).total_seconds()
            if self.stage_id != th.stage_id:
                add_time = False
                continue
            add_time = True
            date_start = dt.strptime(th.create_date, dtf)
        return int(elapsed_time/3600)
