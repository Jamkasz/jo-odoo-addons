# -*- encoding: utf-8 -*-
{
    'name': 'Software Development Kanban',
    'version': '0.0.1',
    'category': 'Project Management',
    'license': '',
    'summary': 'Extends Project to match better the Software Development '
               'Kanban working practices',
    'description': """Extends Project to match better the Software Development
    Kanban working practices, compatible with Odoo 8 or later""",
    'author': 'Joel Ortiz',
    'website': '',
    'depends': ['project', 'hr'],
    'data': ['views/project_view.xml',
             'views/users_view.xml',
             'views/team_view.xml',
             'data/update_data.xml'],
    'demo': ['data/fixtures.xml'],
    'css': [],
    'js': [],
    'qweb': [],
    'images': [],
    'application': True,
    'installable': True,
    'active': False,
}
