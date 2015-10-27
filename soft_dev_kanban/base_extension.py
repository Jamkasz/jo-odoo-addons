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

    wip_finished = fields.Integer('WIP Items Finished Today', default=0)
    total_wip_days = fields.Integer('Total Days Processed', default=0)
    wip_average = fields.Float('WIP Items per Day Average', default=0)
    wip_limit = fields.Integer('WIP Items Limit', default=2)
    date_last_wip_update = fields.Date('Last WIP update')

    @api.one
    def add_wip(self):
        """
        If the last WIP update was done today, it just adds another
        item to the number of finished tasks.

        If not, it will update the items per day average and update
        the other attributes as needed.

        It always updates the ``date_last_wip_update``
        """
        if self.date_last_wip_update == date.today().strftime(DF) or \
                not self.date_last_wip_update:
            self.wip_finished += 1
        else:
            self.wip_average = (self.wip_average * self.total_wip_days +
                                self.wip_finished) / (self.total_wip_days + 1)
            self.wip_finished = 1
            self.total_wip_days += 1
        self.date_last_wip_update = date.today().strftime(DF)

    @api.one
    def current_wip_items(self):
        """
        Computes the current number of work in progress items of the
        user.

        :returns: number of work items
        :rtype: int
        """
        task_model = self.env['project.task']
        analysis_items = task_model.search([
            ['stage_id.stage_type', '=', 'analysis'],
            ['analyst_id', '=', self.id]])
        dev_items = task_model.search([
            ['stage_id.stage_type', '=', 'dev'],
            ['user_id', '=', self.id]])
        review_items = task_model.search([
            ['stage_id.stage_type', '=', 'review'],
            ['reviewer_id', '=', self.id]])
        return len(analysis_items) + len(dev_items) + len(review_items)
