"""
`task_extension.py` extends the `project.task` Odoo model adding
extra functionality to provide a better kanban process experience.
"""
from openerp.models import Environment
from openerp import models, fields, api
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class ProjectTaskHistoryExtension(models.Model):
    """
    Extends `project.task.history` Odoo model to change the ``date``
    field to `datetime` type.
    """
    _name = 'project.task.history'
    _inherit = 'project.task.history'

    date = fields.Datetime('Date', select=True)
    working_hours = fields.Integer('Working Hours')

    def _update_working_hours_on_install(self, cr, uid, ids=None, context=None):
        """
        To be called on installation of the module.

        Updates previous instances of this model and inserts the
        ``working_hours`` value.
        """
        env = Environment(cr, uid, {'uid': uid})
        task_model = env['project.task']
        history_model = env['project.task.history']
        task_records = task_model.search([], order='id asc')
        for t in task_records:
            history_records = history_model.search([['task_id', '=', t.id]],
                                                   order='id asc')
            for i in range(len(history_records)-1):
                if not history_records[i].working_hours:
                    history_records[i].write({
                        'working_hours': t.get_working_hours(
                            dt.strptime(history_records[i].date, dtf),
                            dt.strptime(history_records[i+1].date, dtf)
                        )[0]})


class ProjectTaskTypeExtension(models.Model):
    """
    Extends `project.task.type` Odoo model to add stage types that
    will allow getting better and more accurate kanban metrics like
    lead time and throughput.

    `backlog` type allows to have a buffer to store ideas to pull
    into the workflow whenever necessary.
    `input` type marks the starting point ot fhe workflow, a task
    ``date_start`` will be updated when reaching this stage.
    `queue` type is used as buffers within the workflow. Time spent
    here counts towards the lean time anyway, but it will be ignored
    when computing employee workload.
    `analysis` type marks the WIP stages for analysts.
    `dev` type marks the WIP stages for developers.
    `review` type marks the WIP stages for reviewers (i.e. testing).
    `done` type marks the finishing points of the workflow, a task
    ``date_end`` will be updated when reaching this stage.

    `internal` and `external` sources allows us to measure extra
    metrics like lead time within our organization only.
    """
    _name = 'project.task.type'
    _inherit = 'project.task.type'
    _types = [
        ['backlog', 'Backlog'],
        ['input', 'Input Queue/ToDo'],
        ['queue', 'Queue/Buffer'],
        ['analysis', 'Analysis'],
        ['dev', 'Development'],
        ['review', 'Review'],
        ['done', 'Done'],
        ['other', 'Other']
    ]

    stage_type = fields.Selection(_types, 'Type', default='other')

    def _update_stages_on_install(self, cr, uid, ids=None, context=None):
        """
        To be called on installation of the module.

        Updates the default Project stages and adds some new ones to
        have a default stage structure.
        """
        # Migrate original project stages
        env = Environment(cr, uid, {'uid': uid})
        stage_model = env['project.task.type']
        analysis = stage_model.search([['name', '=', 'Analysis']])
        spec = stage_model.search([['name', '=', 'Specification']])
        design = stage_model.search([['name', '=', 'Design']])
        dev = stage_model.search([['name', '=', 'Development']])
        test = stage_model.search([['name', '=', 'Testing']])
        merge = stage_model.search([['name', '=', 'Merge']])
        done = stage_model.search([['name', '=', 'Done']])
        cancel = stage_model.search([['name', '=', 'Cancelled']])
        if analysis:
            analysis.write({'sequence': 5, 'stage_type': 'analysis'})
        if spec:
            spec.write({'stage_type': 'analysis'})
        if design:
            design.write({'stage_type': 'analysis'})
        if dev:
            dev.write({'sequence': 13, 'stage_type': 'dev'})
        if test:
            test.write({'sequence': 15, 'stage_type': 'review'})
        if merge:
            merge.write({'sequence': 16, 'stage_type': 'queue'})
        if done:
            done.write({'stage_type': 'done'})
        if cancel:
            cancel.write({'stage_type': 'done'})
        # Add new stages
        new = stage_model.search([['name', 'in', [
            'Backlog', 'Input Queue', 'Development Ready', 'Test Ready']]])
        if not new:
            stage_model.create({'name': 'Backlog', 'sequence': 1,
                                'case_default': True, 'stage_type': 'backlog'})
            stage_model.create({'name': 'Input Queue', 'sequence': 2,
                                'case_default': True, 'stage_type': 'input'})
            stage_model.create({'name': 'Development Ready', 'sequence': 12,
                                'case_default': True, 'stage_type': 'queue'})
            stage_model.create({'name': 'Test Ready', 'sequence': 14,
                                'case_default': True, 'stage_type': 'queue'})


class ProjectTaskExtension(models.Model):
    """
    Extends `project.task` Odoo model
    """
    _name = 'project.task'
    _inherit = 'project.task'

    total_time = fields.Integer(
        string='Lead Time', compute='_compute_total_time',
        store=False, readonly=True)
    stage_time = fields.Integer(
        string='Stage Working Hours', compute='_compute_stage_time',
        store=False, readonly=True)
    analyst_id = fields.Many2one('res.users', 'Analyst', select=True,
                                 track_visibility='onchange')

    @api.one
    def _store_history(self):
        """
        Overwrites Odoo `_store_history` so it stores a `datetime` on
        the ``date`` field instead of a `date` and stores the working
        hours elapsed from the previous log.

        :returns: ``True``
        :rtype: bool
        """
        history_model = self.env['project.task.history']
        history_records = history_model.search([['task_id', '=', self.id]], order="date desc")
        if history_records:
            history_records[0].write({'working_hours': self.get_working_hours(
                dt.strptime(history_records[0].date, dtf), dt.now())[0]})
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
            ['task_id', '=', self.id], ['date', '<=', date.strftime(dtf)],
            ['type_id', '=', stage_id]],
            order='date asc')
        result = 0
        for th in task_history_records:
            result += th.working_hours if th.working_hours else 0
        if self.stage_id.id == stage_id:
            date_start = dt.strptime(
                task_history_records[len(task_history_records)-1].date, dtf) \
                if len(task_history_records) > 1 \
                else dt.strptime(self.date_last_stage_update, dtf)
            result += self.get_working_hours(date_start, date)[0]
        return result
