"""
`team.py` adds the concept of User Team for the Kanban management.
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
    wi_finished = fields.Integer('Work Items Finished Today', default=0)
    total_days = fields.Integer('Total Days Processed', default=0)
    throughput = fields.Float('Work Items per Day Average', default=0)
    wip_limit = fields.Integer('WIP Limit', default=0)
    date_last_wip_update = fields.Date('Last WIP update')

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
