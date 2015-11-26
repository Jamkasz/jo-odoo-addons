"""
`project_extension.py` extends the `project` Odoo module adding
extra functionality to provide a better kanban process experience.
"""
from openerp.models import Environment
from openerp import models, fields, api
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ProjectTaskHistoryExtension(models.Model):
    """
    Extends `project.task.history` Odoo model to change the ``date``
    field to `datetime` type.
    """
    _name = 'project.task.history'
    _inherit = 'project.task.history'

    date = fields.Datetime('Date', select=True)
    working_hours = fields.Integer('Working Hours')

    def _update_working_hours_on_install(self, cr, uid,
                                         ids=None, context=None):
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
            for i in range(len(history_records) - 1):
                if not history_records[i].working_hours:
                    history_records[i].write({
                        'working_hours': t.get_working_hours(
                            dt.strptime(history_records[i].date, dtf),
                            dt.strptime(history_records[i + 1].date, dtf)
                        )[0]})


class ProjectTaskTypeExtension(models.Model):
    """
    Extends `project.task.type` Odoo model to add stage types that
    will allow getting better and more accurate kanban metrics like
    lead time and throughput.

    `backlog` type allows to have a buffer to store ideas to pull
    into the workflow whenever necessary.
    `queue` type is used as buffers within the workflow.
    `analysis` type marks the WIP stages for analysts.
    `dev` type marks the WIP stages for developers.
    `review` type marks the WIP stages for reviewers (i.e. testing).
    `done` type marks the finishing points of the workflow, a task
    ``date_out`` will be updated when reaching this stage.
    """
    _name = 'project.task.type'
    _inherit = 'project.task.type'
    _types = [
        ['backlog', 'Backlog'],
        ['queue', 'Queue/Buffer'],
        ['analysis', 'Analysis'],
        ['dev', 'Development'],
        ['review', 'Review'],
        ['done', 'Done'],
        ['other', 'Other']
    ]

    stage_type = fields.Selection(_types, 'Type', default='other')
    related_stage_id = fields.Many2one(
        'project.task.type', string='Queue To',
        domain=[['stage_type', 'not in', ['backlog', 'queue']]])
    wip_limit = fields.Integer('WIP Limit')

    @api.multi
    def write(self, vals):
        """
        Extends Odoo `write` method to manage the ``related_stage_id``
        changes.

        Non `queue` stages are not allowed to have a related stage.
        related_stage_id cannot be of `backlog` or `queue` type.
        """
        if vals.get('related_stage_id'):
            if self.browse(vals.get('related_stage_id')).stage_type in \
                    ['backlog', 'queue']:
                raise models.except_orm(
                    'Stage Type Error',
                    'related_stage_id cannot be of backlog or queue type')
            for stage in self:
                if stage.stage_type != 'queue':
                    raise models.except_orm(
                        'Stage Type Error',
                        'Only queue stages can have related_stage_id')
        if vals.get('stage_type'):
            if vals.get('stage_type') != 'queue':
                vals['related_stage_id'] = False
            if vals.get('stage_type') in ['backlog', 'queue', 'done']:
                    vals['wip_limit'] = False
        if vals.get('wip_limit'):
            for stage in self:
                if stage.stage_type in ['backlog', 'queue', 'done']:
                    raise models.except_orm(
                        'Stage WIP Limit Error',
                        '{0} stages cannot have a WIP limit'.format(
                            stage.stage_type))
        return super(ProjectTaskTypeExtension, self).write(vals)

    @api.one
    def check_wip_limit(self):
        """
        Checks the WIP item limit for the stage and returns a warning
        message if it is overloaded.
        """
        if self.wip_limit:
            if self.current_wip_items()[0] > self.wip_limit:
                return '{0} stage is overloaded'.format(self.name)
        if self.related_stage_id:
            return self.related_stage_id.check_wip_limit()[0]
        return False

    @api.one
    def current_wip_items(self):
        """
        Computes the current number of work in progress items of the
        stage.

        :returns: number of work items
        :rtype: int
        """
        task_model = self.env['project.task']
        queues = self.search([['related_stage_id', '=', self.id]])
        work_items = task_model.search([
            '|',
            ['stage_id', '=', self.id],
            ['stage_id', 'in', [q.id for q in queues]]])
        return len(work_items)

    @api.onchange('related_stage_id')
    def onchange_related_stage_id(self):
        """
        Shows a warning message if the analyst assigned is being
        overloaded above the work in progress limit.
        """
        res = {}
        if self.stage_type != 'queue':
            res['warning'] = {
                'title': 'Warning',
                'message': 'Only queue stages can have a related stage'
            }
            self.related_stage_id = False
        return res

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


class ProjectTaskExtension(models.Model):
    """
    Extends `project.task` Odoo model
    """
    _name = 'project.task'
    _inherit = 'project.task'
    _priority_selection = [('0', 'Low'), ('1', 'Normal'), ('2', 'High')]

    total_time = fields.Integer(
        string='Lead Time', compute='_compute_total_time',
        store=False, readonly=True)
    stage_time = fields.Integer(
        string='Stage Working Hours', compute='_compute_stage_time',
        store=False, readonly=True)
    analyst_id = fields.Many2one('res.users', 'Analyst', select=True,
                                 track_visibility='onchange')
    date_in = fields.Datetime('Date In')
    date_out = fields.Datetime('Date Out')
    dynamic_priority = fields.Selection(
        _priority_selection, string='Dynamic Priority',
        compute='_compute_priority', store=False, readonly=True)

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields,
                                           auto_follow_fields=None):
        """
        Extends Odoo method to add ``analyst_id`` to the automatic follow
        users of the task.
        """
        if auto_follow_fields is None:
            auto_follow_fields = ['user_id', 'reviewer_id', 'analyst_id']
        return super(
            ProjectTaskExtension, self
        )._message_get_auto_subscribe_fields(updated_fields,
                                             auto_follow_fields)

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
        history_records = history_model.search([['task_id', '=', self.id]],
                                               order="date desc")
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
        """
        if self.date_out:
            date_end = dt.strptime(self.date_out, dtf)
        else:
            date_end = dt.now()
        if self.date_in:
            self.total_time = self.get_working_hours(
                dt.strptime(self.date_in, dtf), date_end)[0]
        else:
            self.total_time = False

    @api.one
    def _compute_stage_time(self):
        """
        Computes the total time elapsed from the first time the task
        reached its current stage until the end date if exists or now,
        if it doesn't.

        If the task is related to a project with a working hours
        calendar, it returns only the working hours.
        """
        if self.date_out:
            date_end = dt.strptime(self.date_out, dtf)
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
            return int((date_end - date_start).total_seconds() / 3600)

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
                task_history_records[len(task_history_records) - 1].date, dtf) \
                if len(task_history_records) > 1 \
                else dt.strptime(self.date_last_stage_update, dtf)
            result += self.get_working_hours(date_start, date)[0]
        return result

    @api.one
    def get_dynamic_priority(self):
        """
        Gets priority value to set to the task depending on the related
        tags.

        :returns: '0', '1' or '2'
        :rtype: str
        """
        for cat in self.categ_ids:
            if cat.cos_id:
                if cat.cos_id.dynamic_priority == 'deadline':
                    pld = self.project_id.average_lead_time
                    if pld > 0 and self.date_deadline:
                        deadline = dt.strptime(self.date_deadline, DF)
                        time = self.get_working_hours(dt.today(), deadline)
                        if cat.cos_id.deadline_high*pld >= time[0]:
                            return '2'
                        if cat.cos_id.deadline_normal*pld >= time[0]:
                            return '1'
                        return '0'
                elif cat.cos_id.dynamic_priority == 'blocked':
                    stage = dt.strptime(self.date_last_stage_update, dtf)
                    time = dt.now()-stage
                    if cat.cos_id.time_high <= time.days:
                        return '2'
                    if cat.cos_id.time_normal <= time.days:
                        return '1'
                    return '0'
        return False

    @api.one
    def _compute_priority(self):
        """
        Computes the priority of the task depending on the related
        classes of service.
        """
        self.dynamic_priority = self.get_dynamic_priority()[0]

    @api.onchange('analyst_id')
    def onchange_analyst_id(self):
        """
        Shows a warning message if the analyst assigned is being
        overloaded above the work in progress limit.
        Same if any of the user teams is overloaded.
        """
        res = {}
        if self.analyst_id:
            if self.analyst_id.wip_limit:
                message = self.check_wip_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
            if self.analyst_id.team_ids:
                message = self.check_team_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
        return res

    @api.onchange('user_id')
    def onchange_user_id(self):
        """
        Shows a warning message if the user assigned is being
        overloaded above the work in progress limit.
        Same if any of the user teams is overloaded.
        """
        res = {}
        if self.user_id:
            if self.user_id.wip_limit:
                message = self.check_wip_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
            if self.user_id.team_ids:
                message = self.check_team_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
        return res

    @api.onchange('reviewer_id')
    def onchange_reviewer_id(self):
        """
        Shows a warning message if the user assigned is being
        overloaded above the work in progress limit.
        Same if any of the user teams is overloaded.
        """
        res = {}
        if self.reviewer_id:
            if self.reviewer_id.wip_limit:
                message = self.check_wip_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
            if self.reviewer_id.team_ids:
                message = self.check_team_limit(self.stage_id.id)[0]
                if message:
                    return {'warning': {
                        'title': 'Warning',
                        'message': message
                    }}
        return res

    @api.model
    def create(self, vals):
        """
        Extends Odoo `create` method to do class of service checks.

        :param vals: values dictionary
        :type vals: dict
        :returns: ``project.task`` id
        :rtype: int
        """
        res = super(ProjectTaskExtension, self).create(vals)
        if vals.get('categ_ids'):
            tag_model = self.env['project.category']
            tags = tag_model.browse(vals.get('categ_ids')[0][2]) \
                if isinstance(vals.get('categ_ids')[0], (list, tuple)) \
                else tag_model.browse(vals.get('categ_ids'))
            if tags.cos_limit_overflow():
                raise models.except_orm(
                    'Class of Service Error!',
                    'Cannot create a new task with that class of service, the '
                    'maximum allowed amount has already been reached.')
            color = tags.get_cos_colour()
            if color:
                res.color = color
            tags.check_deadline_required(vals.get('date_deadline'))
        return res

    @api.multi
    def write(self, vals):
        """
        Extends Odoo `write` method to log the Work In Progress per user
        when a task changes stage.

        It also records automatically the ``date_out`` of a task if
        the new stage is of type `done` and the ``date_in`` if a
        task is not type ``backlog`` and it doesn't have it already.

        :param vals: values dictionary
        :type vals: dict
        :returns: True
        :rtype: bool
        """
        if vals.get('stage_id'):
            self.filtered(
                lambda t:
                t.stage_id.stage_type == 'dev' and t.user_id
            ).user_id.add_finished_item()
            self.filtered(
                lambda t:
                t.stage_id.stage_type == 'analysis' and t.analyst_id
            ).analyst_id.add_finished_item()
            self.filtered(
                lambda t:
                t.stage_id.stage_type == 'review' and t.reviewer_id
            ).reviewer_id.add_finished_item()
            stage = self.env['project.task.type'].browse(vals.get('stage_id'))
            if stage.stage_type != 'backlog' and not self.date_in:
                vals['date_in'] = dt.now().strftime(dtf)
            if stage.stage_type == 'done' and not self.date_out:
                vals['date_out'] = dt.now().strftime(dtf)
        res = super(ProjectTaskExtension, self).write(vals)
        if vals.get('categ_ids'):
            tag_model = self.env['project.category']
            tags = tag_model.browse(vals.get('categ_ids')[0][2]) \
                if isinstance(vals.get('categ_ids')[0], (list, tuple)) \
                else tag_model.browse(vals.get('categ_ids'))
            if tags.cos_limit_overflow():
                raise models.except_orm(
                    'Class of Service Error!',
                    'Cannot link another task with that class of service, the '
                    'maximum allowed amount has already been reached.')
            color = tags.get_cos_colour()
            if color:
                self.color = color
            for task in self:
                tags.check_deadline_required(task.date_deadline)
        elif 'date_deadline' in vals:
            self.categ_ids.check_deadline_required(vals.get('date_deadline'))
        return res

    @api.one
    def ignore_wip_limit(self):
        """
        Checks if the task is related to any tag linked with a class
        of service that ignores WIP limits.

        :returns: True or False
        :rtype: bool
        """
        for tag in self.categ_ids:
            if tag.cos_id and tag.cos_id.ignore_limit:
                return True
        return False

    @api.one
    def check_wip_limit(self, stage_id):
        """
        Checks the WIP item limit for the analyst, developer or reviewer
        of the task and returns a warning message if any of them
        is overloaded.

        :param stage_id: ``project.task.type`` id
        :type stage_id: int
        """
        if self.ignore_wip_limit()[0]:
            return False
        stage_model = self.env['project.task.type']
        stage = stage_model.browse(stage_id)
        if stage.stage_type == 'queue' and stage.related_stage_id:
            stage = stage.related_stage_id
        if stage.stage_type == 'dev':
            if self.user_id and self.user_id.wip_limit:
                if self.user_id.current_wip_items()[0] > \
                        self.user_id.wip_limit:
                    return self.user_id.name + ' is overloaded'
        elif stage.stage_type == 'analysis':
            if self.analyst_id and self.analyst_id.wip_limit:
                if self.analyst_id.current_wip_items()[0] > \
                        self.analyst_id.wip_limit:
                    return self.analyst_id.name + ' is overloaded'
        elif stage.stage_type == 'review':
            if self.reviewer_id and self.reviewer_id.wip_limit:
                if self.reviewer_id.current_wip_items()[0] > \
                        self.reviewer_id.wip_limit:
                    return self.reviewer_id.name + ' is overloaded'
        return False

    @api.one
    def check_stage_limit(self, stage_id):
        """
        Checks the WIP item limit for the stage and returns a
        warning message if it is overloaded.

        :param stage_id: ``project.task.type`` id
        :type stage_id: int
        """
        if self.ignore_wip_limit()[0]:
            return False
        stage_model = self.env['project.task.type']
        stage = stage_model.browse(stage_id)
        return stage.check_wip_limit()[0] if stage else False

    @api.one
    def check_team_limit(self, stage_id):
        """
        Checks the WIP item limit for the analyst, developer or reviewer
        team of the task and returns a warning message if any of them
        is overloaded.

        :param team_id: :mod:`team<team.KanbanUserTeam>` id
        :type team_id: int
        """
        if self.ignore_wip_limit()[0]:
            return False
        stage_model = self.env['project.task.type']
        stage = stage_model.browse(stage_id)
        if stage.stage_type == 'queue' and stage.related_stage_id:
            stage = stage.related_stage_id
        if stage.stage_type == 'dev':
            if self.user_id and self.user_id.team_ids:
                res = self.user_id.team_ids.check_wip_limit()
                for r in res:
                    if r:
                        return r
        elif stage.stage_type == 'analysis':
            if self.analyst_id and self.analyst_id.team_ids:
                res = self.analyst_id.team_ids.check_wip_limit()
                for r in res:
                    if r:
                        return r
        elif stage.stage_type == 'review':
            if self.reviewer_id and self.reviewer_id.team_ids:
                res = self.reviewer_id.team_ids.check_wip_limit()
                for r in res:
                    if r:
                        return r
        return False

    @api.one
    def update_date_in(self):
        """
        Updates ``date_in`` depending on the `project.task.history`
        logs recorded for the task.
        """
        history_model = self.env['project.task.history']
        history_records = history_model.search([
            ['task_id', '=', self.id],
            ['type_id.stage_type', '!=', 'backlog'],
            ['type_id.stage_type', '!=', False]], order="date asc")
        if history_records:
            self.date_in = history_records[0].date
        return True

    @api.one
    def update_date_out(self):
        """
        Updates ``date_out`` depending on the `project.task.history`
        logs recorded for the task.
        """
        history_model = self.env['project.task.history']
        history_records = history_model.search([
            ['task_id', '=', self.id],
            ['type_id.stage_type', '=', 'done']], order="date asc")
        if history_records:
            self.date_out = history_records[0].date
        return True


class ProjectExtension(models.Model):
    """
    Extends `project.project` Odoo model to add kanban metrics
    """
    _name = 'project.project'
    _inherit = 'project.project'

    average_lead_time = fields.Float(
        string='Average Lead Time', compute='_compute_average_time',
        store=False, readonly=True)

    @api.one
    def _compute_average_time(self):
        """
        Computes the average lead time of the related finished
        tasks.

        If the project has a working hours calendar, it returns
        only the working hours average.

        :returns: time in hours
        :rtype: float
        """
        task_model = self.env['project.task']
        task_ids = task_model.search([
            ['project_id', '=', self.id], ['date_out', '!=', False]])
        tasks = 0
        total_time = 0
        for task in task_ids:
            tasks += 1
            total_time += task.total_time
        if tasks:
            self.average_lead_time = total_time / tasks
        else:
            self.average_lead_time = 0

    @api.one
    def update_task_dates(self):
        """
        Updates ``date_in`` and ``date_out`` of every task related to
        the project.
        """
        task_model = self.env['project.task']
        task_ids = task_model.search([
            ['project_id', '=', self.id]])
        task_ids.update_date_in()
        task_ids.update_date_out()
        return True


class ProjectCategoryExtension(models.Model):
    """
    Extends `project.category` Odoo model to add kanban class of service
    """
    _name = 'project.category'
    _inherit = 'project.category'

    cos_id = fields.Many2one('sdk.class_of_service', 'Class of Service')

    @api.multi
    def cos_limit_overflow(self):
        """
        Checks if the number of tasks related to the project categories
        is greater than the related classes of service.

        :returns: True or False
        :rtype: bool
        """
        task_model = self.env['project.task']
        for cat in self:
            if cat.cos_id and cat.cos_id.limit:
                cats = self.search([['cos_id', '=', cat.cos_id.id]])
                cat_ids = [c.id for c in cats]
                tasks = task_model.search([
                    ['categ_ids', 'in', cat_ids],
                    ['date_out', '=', False]])
                if len(tasks) > cat.cos_id.limit:
                    return True
        return False

    @api.multi
    def get_cos_colour(self):
        """
        Finds the highest priority color among the classes of service
        related to the tags.

        :returns: color index
        :rtype: int
        """
        colour = 0
        priority = 0
        for cat in self:
            if cat.cos_id and cat.cos_id.colour:
                if cat.cos_id.priority < priority or not priority:
                    colour = cat.cos_id.colour
                    priority = cat.cos_id.priority
        return colour

    @api.multi
    def check_deadline_required(self, deadline):
        """
        Raises exception if deadline is required but not provided or
        if deadline must be empty and is provided.

        :param deadline: is deadline provided or not.
        :type deadline: bool
        :returns: True
        :rtype: bool
        """
        if self.filtered(
                lambda c: c.cos_id and c.cos_id.deadline == 'required'):
            if not deadline:
                raise models.except_orm(
                    'Deadline required!',
                    'This class of service requires deadline to be '
                    'provided.')
        if self.filtered(lambda c: c.cos_id and c.cos_id.deadline == 'nodate'):
            if deadline:
                raise models.except_orm(
                    'Deadline must NOT exist!',
                    'This class of service requires deadline to be '
                    'empty.')
        return True

    @api.multi
    def write(self, vals):
        """
        Extends Odoo `write` method to do class of service checks.

        :param vals: values dictionary
        :type vals: dict
        :returns: True
        :rtype: bool
        """
        res = super(ProjectCategoryExtension, self).write(vals)
        if vals.get('cos_id'):
            if self.cos_limit_overflow():
                raise models.except_orm(
                    'Class of Service Error!',
                    'Cannot link another tag with that class of service, as '
                    'it would break the maximum task amount limit.')
            task_model = self.env['project.task']
            tasks = task_model.search(
                [['categ_ids', 'in', [c.id for c in self]]])
            color = self.get_cos_colour()
            if color:
                tasks.write({'color': color})
        return res
