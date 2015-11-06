"""
'log_message_wizard.py' defines the wizard to log task messages through
a pop up window.
"""
from openerp import models, fields, api


class LogMessageWizard(models.TransientModel):
    _name = 'log.message.wizard'

    res_model = fields.Char('Resource Model', size=128)
    res_id = fields.Integer('Resource ID')
    subject = fields.Char('Subject')
    message = fields.Html('Message')

    @api.one
    def log_message(self):
        message_model = self.env['mail.message']
        message_model.create({
            'type': 'comment',
            'author_id': self.env.user.partner_id.id,
            'model': self.res_model,
            'res_id': self.res_id,
            'subject': self.subject,
            'body': self.message
        })
        return {'type': 'ir.actions.act_window_close'}
