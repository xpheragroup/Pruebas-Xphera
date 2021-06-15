# -*- coding: utf-8 -*-

from odoo import http


class KeraltyModule(http.Controller):
    @http.route('/keralty/', auth='public')
    def index(self, **kw):
        return "Hello, world"

# class KeraltyModule(http.Controller):
#     @http.route('/keralty_module/keralty_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/keralty_module/keralty_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('keralty_module.listing', {
#             'root': '/keralty_module/keralty_module',
#             'objects': http.request.env['keralty_module.keralty_module'].search([]),
#         })

#     @http.route('/keralty_module/keralty_module/objects/<model("keralty_module.keralty_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('keralty_module.object', {
#             'object': obj
#         })
