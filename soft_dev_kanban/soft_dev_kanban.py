"""
`soft_dev_kanban.py` adds extra models not present in default Odoo
necessary for the extra features implemented in this Kanban management
module.
"""

from openerp import models, fields, api


class KanbanUserTeam(models.Model):
    """
    Represents a Kanban user team which groups users together in order to
    manage metrics and limits for the team as a whole, instead of using
    just individuals.
    """
    _name = 'sdk.user.team'

    name = fields.Char('Name')
    user_ids = fields.Many2many('res.users', 'team_users_rel', 'team_id',
                                'user_id', 'Team Members')
    throughput = fields.Float(
        string='Throughput', compute='_compute_throughput',
        store=False, readonly=True)
    wip_limit = fields.Integer('WIP Limit', default=0)

    @api.one
    def _compute_throughput(self):
        """
        Computes the average throughput of the team.

        :returns: work items per day on average
        :rtype: float
        """
        if not self.user_ids:
            return 0
        return sum([u.throughput for u in self.user_ids])/len(self.user_ids)

    @api.one
    def current_wip_items(self):
        """
        Computes the current number of work in progress items of the
        team.

        :returns: number of work items
        :rtype: int
        """
        return sum(self.user_ids.current_wip_items())

    @api.one
    def check_wip_limit(self):
        """
        Checks the WIP item limit for the team and returns a warning
        message if it is overloaded.
        """
        if self.wip_limit:
            if sum(self.current_wip_items()) > self.wip_limit:
                return '{0} is overloaded'.format(self.name)
        return False


class ClassOfService(models.Model):
    """
    Represents a Kanban work item class of service.
    """
    _name = 'sdk.class_of_service'

    _colour_selection = [[0, 'None'], [1, 'Grey'], [2, 'Red'], [3, 'Yellow'],
                         [4, 'Green'], [5, 'Teal'], [6, 'Blue'], [7, 'Indigo'],
                         [8, 'Purple'], [9, 'Pink']]
    _deadline_selection = [['required', 'Required'],
                           ['nodate', 'Must be Empty'],
                           ['noreq', 'Not Required']]
    _dynprio_selection = [['none', 'Manual'],
                          ['deadline', 'The closer deadline gets'],
                          ['blocked', 'The longer stays in stage']]

    name = fields.Char('Name')
    limit = fields.Integer('Active Limited Amount', default=0)
    colour = fields.Selection(_colour_selection, 'Kanban Colour', default=0)
    priority = fields.Integer('Colour Priority', default=0)
    ignore_limit = fields.Boolean('Ignore WIP limits', default=False)
    deadline = fields.Selection(_deadline_selection, 'Task Deadline Date',
                                default='noreq')
    dynamic_priority = fields.Selection(_dynprio_selection,
                                        'Dynamic Priority Changes',
                                        default='none')
    deadline_normal = fields.Float(
        'Normal Priority Breakpoint',
        help="If the remaining time until the deadline is less than the "
             "average lead time * times this number, priority will increase "
             "to Normal")
    deadline_high = fields.Float(
        'High Priority Breakpoint',
        help="If the remaining time until the deadline is less than the "
             "average lead time * times this number, priority will increase "
             "to High")
    time_normal = fields.Integer(
        'Normal Priority (# Days)',
        help="If the task stays for this amount of days in the same stage, "
             "priority will increase to Normal")
    time_high = fields.Integer(
        'High Priority (# Days)',
        help="If the task stays for this amount of days in the same stage, "
             "priority will increase to High")
    tag_ids = fields.One2many('project.category', 'cos_id', 'Tags', readonly=1)
    can_be_parent = fields.Boolean(
        'Can be Parent', default=False,
        help="If the class of service has this option active, tasks related to"
             " it will be selectable as Feature for other tasks.")
    track_stage = fields.Boolean(
        'Track Childs Stage', default=False,
        help="If the class of service has this option active, tasks related to"
             " it will automatically set their stage to the earliest child "
             "task stage.")

    @api.model
    def create(self, vals):
        if vals.get('track_stage') and not vals.get('can_be_parent'):
            raise models.except_orm(
                'Class of Service Error!',
                'In order to track child tasks stages the Class of Service '
                'needs to be flagged as parent.')
        return super(ClassOfService, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Extends Odoo `write` method to do class of service checks.

        :param vals: values dictionary
        :type vals: dict
        :returns: True
        :rtype: bool
        """
        if 'can_be_parent' in vals and not vals.get('can_be_parent'):
            vals['track_stage'] = False
        elif vals.get('track_stage'):
            if not self.can_be_parent:
                raise models.except_orm(
                    'Class of Service Error!',
                    'In order to track child tasks stages the Class of '
                    'Service needs to be flagged as parent.')
        res = super(ClassOfService, self).write(vals)
        if vals.get('colour') or vals.get('priority'):
            tag_model = self.env['project.category']
            tags = tag_model.search([['cos_id', 'in', [c.id for c in self]]])
            task_model = self.env['project.task']
            tasks = task_model.search(
                [['categ_ids', 'in', [t.id for t in tags]]])
            color = tags.get_cos_colour()
            if color:
                tasks.write({'color': color})
        return res
