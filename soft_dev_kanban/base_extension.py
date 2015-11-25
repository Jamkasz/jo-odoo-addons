"""
`base_extension.py` extends base Odoo models to add software development
kanban process features.
"""
from openerp import models, fields, api
from datetime import date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ResUsersExtension(models.Model):
    """
    Extends `res.users` Odoo model to add Work In Progress metrics.
    """
    _name = 'res.users'
    _inherit = 'res.users'

    wi_finished = fields.Integer('Work Items Finished Today', default=0)
    total_days = fields.Integer('Total Days Processed', default=0)
    throughput = fields.Float('Work Items per Day Average', default=0)
    wip_limit = fields.Integer('WIP Limit', default=0)
    date_last_wip_update = fields.Date('Last WIP update')
    team_ids = fields.Many2many('sdk.user.team', 'team_users_rel', 'user_id',
                                'team_id', 'Kanban Teams')

    @api.one
    def add_finished_item(self):
        """
        If the last WIP update was done today, it just adds another
        item to the number of finished tasks.

        If not, it will update the items per day average and update
        the other attributes as needed.

        It always updates the ``date_last_wip_update``
        """
        values = {}
        if self.date_last_wip_update == date.today().strftime(DF) or \
                not self.date_last_wip_update:
            values['wi_finished'] = self.wi_finished + 1
        else:
            values['throughput'] = (self.throughput * self.total_days +
                                    self.wi_finished) / (self.total_days + 1)
            values['wi_finished'] = 1
            values['total_days'] = self.total_days + 1
        values['date_last_wip_update'] = date.today().strftime(DF)
        self.write(values)

    @api.one
    def current_wip_items(self):
        """
        Computes the current number of work in progress items of the
        user.

        :returns: number of work items
        :rtype: int
        """
        task_model = self.env['project.task']
        return task_model.search_count(
            ['|', '&',
             ('stage_id.stage_type', '=', 'analysis'),
             ('analyst_id', '=', self.id),
             '|', '&',
             ('stage_id.stage_type', '=', 'dev'),
             ('user_id', '=', self.id),
             '|', '&',
             ('stage_id.stage_type', '=', 'review'),
             ('reviewer_id', '=', self.id),
             '|', '&',
             ('stage_id.stage_type', '=', 'queue'), '&',
             ('stage_id.related_stage_id.stage_type', '=', 'analysis'),
             ('analyst_id', '=', self.id),
             '|', '&',
             ('stage_id.stage_type', '=', 'queue'), '&',
             ('stage_id.related_stage_id.stage_type', '=', 'dev'),
             ('user_id', '=', self.id),
             '&',
             ('stage_id.stage_type', '=', 'queue'), '&',
             ('stage_id.related_stage_id.stage_type', '=', 'review'),
             ('reviewer_id', '=', self.id)])
