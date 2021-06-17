# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from collections import defaultdict
import logging
import re
from datetime import datetime
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    listado_areas_cliente = fields.Many2one(
        'keralty_module.formulario.cliente', 'Listado de Áreas', check_company=True)

class FormularioCliente(models.Model):
    _name = 'keralty_module.formulario.cliente'
    _inherit = 'mail.thread'
    _description = 'Formulario Cliente'
    _rec_name = 'nombre_proyecto'

    #
    imagen_empresa = fields.Char(readonly=True, default="/keralty_module/static/src/img/logos/logo_keralty_default.svg",)
    imagen_empresa_html = fields.Html('Imágen Html', readonly=True, compute = '_compute_imagen_empresa_html',)

    nombre_proyecto = fields.Char(required=True, string="Nombre Proyecto",)
    # Configuración empresa
    empresa_seleccionada = fields.Many2many(string="Selección de Empresa(s)",
                    comodel_name='res.partner',
                    relation="product_cliente_empresa_partner",
                    help="Selección de Empresas asociadas a la solicitud.",
                    # domain="[('user_ids', '=', False)]",
                    # domain="[['attribute_id.name','ilike','Empresa']]",
                    domain="['&',('is_company', '=', True), ('supplier_rank', '=', '0'), ('name', '!=', 'Colombia'), ('name', '!=', 'Venezuela')]",
                    check_company=True,
                    required=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
    producto_seleccionado = fields.Many2many(string="Selección de Producto(s)",
                    # comodel_name='product.attribute.value',
                    comodel_name='product.attribute.value',
                    relation="product_cliente_producto",
                    help="Selección de Productos asociados a la solicitud.",
                    domain="[['attribute_id.name','ilike','Producto']]",
                    required=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
    sede_seleccionada = fields.Many2many(string="Selección de Sede(s)",
                    comodel_name='product.template',
                    help="Selección de Sede(s) asociadas a la solicitud.",
                    domain="[('categ_id.name','ilike','Sede')]",
                    required=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
    tipo_intervencion = fields.Selection([('sede_nueva', 'Sede Nueva'),('adecuacion', 'Adecuación'),('remodelacion', 'Remodelación'),('ampliacion', 'Ampliación')],
                    readonly=True, states={'draft': [('readonly', False)]},)

    # Listado de áreas asociadas en campo BoM de mrp.production
    sedes_seleccionadas = fields.Many2many(string="Selección de Sede(s)",
                    comodel_name='mrp.bom',
                    relation="bom_cliente_sedes",
                    help="Selección de Sedes asociados a la solicitud.",
                    domain="[('product_tmpl_id','=',sede_seleccionada)]",
                    required=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
    ldm_producto_nuevo = fields.Many2many(string="Producto nuevo creado para proyecto.",
                    comodel_name='mrp.bom',
                    relation="bom_cliente_producto_nuevo",
                    readonly=True, states={'draft': [('readonly', False)]},)
    # TODO: encontrar el filtro necesario por cada una de las variantes E,mpresa y Producto, por lo pronto se dejan solamente las SEDES.
    # TODO: Al momento de editar cada línea no afecte la cantidad preconfigurada
    areas_asociadas_sede = fields.Many2many(string="Selección de Áreas",
                    comodel_name='mrp.bom.line',
                    relation="x_bom_line_cliente_areas_asistenciales",
                    column1="product_id",
                    column2="product_qty",
                    help="Selección de Áreas asociadas a la(s) Sede(s) seleccionada(s).",
                    domain="['&',('parent_product_tmpl_id','in',sede_seleccionada),('product_id.categ_id.name','like','Cliente'),('product_tmpl_id.categ_id.name','ilike','Cliente')]",
                    required=True,
                    copy=True,
                    readonly=True, states={'draft': [('readonly', False)]},)

    # Ubicación geográfica
    pais = fields.Many2one(required=True, string="País", comodel_name='res.country',help="País seleccionado.", readonly=True, states={'draft': [('readonly', False)]},)
    departamento = fields.Many2one('res.country.state', 'Departamento / Estado', domain="[('country_id', '=', pais)]", required=True, readonly=True, states={'draft': [('readonly', False)]},)
    ciudad = fields.Char(required=True, string="Ciudad / Municipio", readonly=True, states={'draft': [('readonly', False)]},)
    poligono = fields.Char(required=False, string="Polígonos de búsqueda", readonly=True, states={'draft': [('readonly', False)]},)
    especificaciones_adicionales = fields.Char(required=False, string="Especificaciones adicionales", readonly=True, states={'draft': [('readonly', False)]},)


    # Ocupación centro médico
    numero_usuarios = fields.Float(string="Número de Usuarios", required=False, help="Número de Usuarios",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    numero_empleados = fields.Float(string="Número de Empleados", required=False, help="Número de Empleados",
                                    readonly=True, states={'draft': [('readonly', False)]},)
    terceros = fields.Float(string="Terceros", required=False, help="Terceros",
                    readonly=True, states={'draft': [('readonly', False)]},)
    especificaciones_adicionales = fields.Char(required=False, string="Especificaciones adicionales",
                    readonly=True, states={'draft': [('readonly', False)]},)

    # usuarios
    # por género
    usuarios_femenino = fields.Float(string="Femenino", required=True, help="Número de Usuarios Femeninos",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    usuarios_masculino = fields.Float(string="Masculino", required=True, help="Número de Usuarios Masculinos",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    # por grupo etario
    usuarios_menores_10_anos = fields.Float(string="Menores de 10 años", required=True, help="Número de Usuarios Menores de 10 años",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    usuarios_entre_10_19_anos = fields.Float(string="Entre 10 y 19 años", required=True, help="Número de Usuarios Entre 10 y 19 años",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    usuarios_entre_20_59_anos = fields.Float(string="Entre 20 y 59 años", required=True, help="Número de Usuarios Entre 20 y 59 años",
                                   readonly=True, states={'draft': [('readonly', False)]},)
    usuarios_mayores_59_anos = fields.Float(string="Mayores de 59 años", required=True, help="Número de Usuarios Mayores de 59 años",
                                   readonly=True, states={'draft': [('readonly', False)]},)

    # Empleados
    # por género
    empleados_femenino = fields.Float(string="Femenino", required=True, help="Número de Empleados Femeninos",
                                     readonly=True, states={'draft': [('readonly', False)]}, )
    empleados_masculino = fields.Float(string="Masculino", required=True, help="Número de Empleados Masculinos",
                                      readonly=True, states={'draft': [('readonly', False)]}, )
    personal_administrativo = fields.Float(string="Personal administrativo", required=True, help="Cantidad de Personal administrativo",
                                      readonly=True, states={'draft': [('readonly', False)]}, )
    personal_asistencial = fields.Float(string="Personal asistencial", required=True, help="Cantidad de Personal asistencial",
                                      readonly=True, states={'draft': [('readonly', False)]}, )

    # Terceros
    # por género
    terceros_femenino = fields.Float(string="Femenino", required=True, help="Número de Tercecros Femeninos",
                                     readonly=True, states={'draft': [('readonly', False)]}, )
    terceros_masculino = fields.Float(string="Masculino", required=True, help="Número de Terceros Masculinos",
                                      readonly=True, states={'draft': [('readonly', False)]}, )
    servicios_generales = fields.Float(string="Servicios Generales", required=True, help="Cantidad de Terceros Servicios Generales",
                                      readonly=True, states={'draft': [('readonly', False)]}, )
    seguridad = fields.Float(string="Seguridad", required=True, help="Cantidad de Terceros Seguridad ",
                                      readonly=True, states={'draft': [('readonly', False)]}, )

    # Sistema de Estados
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado')], string='Estado',
        copy=False, index=True, readonly=True,
        store=True, tracking=True, compute='_compute_state', default='draft',
        help=" * Borrador: El proyecto se encuentra en edición.\n"
             " * Confirmado: El proyecto ha sido confirmado y no es editable por el cliente.\n"
             " * Realizado: El proyecto se ha ejecutado. \n"
             " * Cancelado: El proyecto ha sido cancelado.")

    @api.depends('state')
    def _compute_state(self):
        if not self.state:
            self.state = 'draft'


    @api.depends('imagen_empresa_html', 'imagen_empresa', 'empresa_seleccionada')
    def _compute_imagen_empresa_html(self):
        if len(self.empresa_seleccionada) > 0:
            for empresa in self.empresa_seleccionada:
                if 'colsanitas' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_colsanitas.svg"
                elif 'eps' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_eps_sanitas.svg"
                elif 'lab' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_lab_clinico.svg"
                elif 'dental' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_clinica_dental.png"
                elif 'ptic' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_optica.png"
                else:
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_keralty_default.svg"
                break
        else:
            self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_keralty_default.svg"

        self.imagen_empresa_html = '<img id="img" src="%s" width="150px" height="100px" alt="Logo Formulario"/>' % self.imagen_empresa


    @api.onchange('empresa_seleccionada')
    def _onchange_empresa_seleccionada(self):
        if len(self.empresa_seleccionada) > 0:
            for empresa in self.empresa_seleccionada:
                if 'colsanitas' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_colsanitas.svg"
                elif 'eps' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_eps_sanitas.svg"
                elif 'lab' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_lab_clinico.svg"
                elif 'odonto' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_clinica_dental.png"
                elif 'ptic' in empresa.name.lower():
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_optica.png"
                else:
                    self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_keralty_default.svg"
                break
        else:
            self.imagen_empresa = "/keralty_module/static/src/img/logos/logo_keralty_default.svg"

        self.imagen_empresa_html = '<img id="img" src="%s" width="150px" height="100px" alt="Logo Formulario"/>' % self.imagen_empresa

    @api.onchange('producto_seleccionado')
    def _onchange_producto_seleccionado(self):
        self.sede_seleccionada = None
        self.areas_asociadas_sede = None
    #
    '''
        Copia LdM
        Cuando cambia la sede seleccionada copia la lista de materiales (LdM) de la Sede (product)
        y la muestra en el campo areas_asociadas_sede     
    '''
    @api.onchange('sede_seleccionada')
    def _onchange_sede_seleccionada(self):

        company_id = self.env.company
        warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = warehouse.manufacture_pull_id.route_id.id
        route_mto = warehouse.mto_pull_id.route_id.id

        # Create Category
        existe_categoria = self.env['product.category'].search([('name', '=', 'Formularios Cliente'.title())])
        if not existe_categoria:
            categoria_consul_requer = self.env['product.category'].create({
                'name': 'Formularios Cliente'.title(),
            })
        else:
            categoria_consul_requer = existe_categoria

        if not self._origin:

            siguiente_codigo_secuencia = self.env['keralty_module.formulario.cliente'].search([], order='id ASC')
            
            if len(siguiente_codigo_secuencia) > 0:
                siguiente_codigo_secuencia = siguiente_codigo_secuencia[-1].id + 1
            else:
                siguiente_codigo_secuencia = 1

            existe_producto = self.env['product.template'].search([('name', '=', 'Formulario Cliente (' + str(siguiente_codigo_secuencia) + ')' )])
            
            # Create Template Product
            if not existe_producto:
                product_template = self.env['product.template'].create({
                    'name': 'Formulario Cliente (' + str(siguiente_codigo_secuencia) + ')',
                    'purchase_ok': False,
                    'type': 'product',
                    'categ_id': categoria_consul_requer.id,
                    'company_id': company_id.id,
                    'route_ids': [(6, 0, [route_manufacture, route_mto])]
                })
                # Create BOM
                bom_created = self.env['mrp.bom'].create({
                    'product_tmpl_id': product_template.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                })
            else:
                product_template = existe_producto
                # validar el bom seleccionado
                bom_created = existe_producto.bom_ids[0]

            self.ldm_producto_nuevo = bom_created

            total_bom_line_ids = None

            if len(self.sede_seleccionada) == 0:
                for linea in bom_created.bom_line_ids:
                    linea.unlink()
                self.areas_asociadas_sede |= bom_created.bom_line_ids

            for sede_product_template in self.sede_seleccionada:
                for area in sede_product_template.bom_ids:

                    for linea_bom in area.bom_line_ids:

                        for producto_seleccionado in self.producto_seleccionado:
                            # if producto_seleccionado.name in linea_bom.display_name:\
                            if linea_bom.bom_product_template_attribute_value_ids:
                                if producto_seleccionado.name in linea_bom.bom_product_template_attribute_value_ids.name:
                                    if "Cliente" in linea_bom.product_id.categ_id.name:
                                        if total_bom_line_ids:
                                            total_bom_line_ids += linea_bom
                                        else:
                                            total_bom_line_ids = linea_bom


                    # lineas_consultadas_names = {record.name for record in total_bom_line_ids}
                    lineas_existentes_names = {record.product_tmpl_id.name for record in bom_created.bom_line_ids}

                    # for lineas_existentes in bom_created.bom_line_ids:
                    for lineas_consultadas in total_bom_line_ids:
                        if lineas_consultadas.product_tmpl_id.name in lineas_existentes_names:
                            continue
                        else:
                            lineas_consultadas.product_qty = 1
                            lineas_consultadas.cantidad_final = 1
                            linea_bom_copy = lineas_consultadas.copy()
                            linea_bom_copy.product_qty = 1
                            linea_bom_copy.cantidad_final = 1                            
                            linea_bom_copy.bom_id = bom_created.id

                    # Si hay más registros de bom_line en las existentes, se deben eliminar
                    if len(self.areas_asociadas_sede) > len(total_bom_line_ids):
                        lineas_consultadas_names = {record.product_tmpl_id.name for record in total_bom_line_ids}

                        for lineas_existentes in self.areas_asociadas_sede:
                            if lineas_existentes.product_tmpl_id.name not in lineas_consultadas_names:
                                self.areas_asociadas_sede.remove(lineas_existentes)
                                # lineas_existentes.bom_id.unlink()
                                # lineas_existentes.bom_id = False

                    self.areas_asociadas_sede |= bom_created.bom_line_ids

                    if not total_bom_line_ids:
                        raise exceptions.UserError("No se encuentra ninguna asociación entre el Producto y la Sede seleccionados.")
        else:
            if len(self.sede_seleccionada) >= len(self._origin.sede_seleccionada):
                sede_nueva = None

                self.areas_asociadas_sede = self._origin.areas_asociadas_sede

                for items in self.sede_seleccionada:

                    for item in items.ids:
                        if item not in self._origin.sede_seleccionada.ids:
                            if sede_nueva:
                                sede_nueva += items
                            else:
                                sede_nueva = items

                total_bom_line_ids = None
                if sede_nueva:
                    for sede in sede_nueva:
                        for area in sede.bom_ids:
                            for linea_bom in area.bom_line_ids:
                                for producto_seleccionado in self.producto_seleccionado:
                                    if linea_bom.bom_product_template_attribute_value_ids:
                                        if producto_seleccionado.name in linea_bom.bom_product_template_attribute_value_ids.name:
                                            if "Cliente" in linea_bom.product_id.categ_id.name:
                                                if total_bom_line_ids:
                                                    total_bom_line_ids += linea_bom
                                                else:
                                                    total_bom_line_ids = linea_bom
                            

                            lineas_existentes_names = {record.product_tmpl_id.name for record in self._origin.ldm_producto_nuevo.bom_line_ids}

                            # for lineas_existentes in bom_created.bom_line_ids:
                            for lineas_consultadas in total_bom_line_ids:
                                if lineas_consultadas.product_tmpl_id.name in lineas_existentes_names:
                                    continue
                                else:
                                    lineas_consultadas.product_qty = 1
                                    lineas_consultadas.cantidad_final = 1
                                    linea_bom_copy = lineas_consultadas.copy()
                                    linea_bom_copy.product_qty = 1
                                    linea_bom_copy.cantidad_final = 1
                                    linea_bom_copy.bom_id = self._origin.ldm_producto_nuevo.id

                            self.areas_asociadas_sede |= self._origin.ldm_producto_nuevo.bom_line_ids


            else:
                self.sede_seleccionada = self._origin.sede_seleccionada



    def action_validar_proyecto(self):
        self.state = 'draft'
        # _logger.critical("Validar proyecto")
        return True

    def action_confirmar_proyecto(self):
        if self.state == 'confirmed':
            raise exceptions.UserError("El formulario ya ha sido marcado como confirmado.")
        self.state = 'confirmed'
        msg = ('Formulario Cliente \"{}\", confirmado por el usuario: \"{}\". \n\n'.format(self.nombre_proyecto, self.env.user.name)) #base_url))

        # Buscar el grupo, buscar los usuarios del grupo, obtener el partner y guardarlo en notifications IDs
        grupo_encontrado = self.env['res.groups'].search([('name', 'ilike', 'Usuarios Técnicos Keralty')], limit=1)

        if grupo_encontrado:
            # _logger.critical(grupo_encontrado)
            # _logger.critical(grupo_encontrado.users)
            notification_ids = []
            for usuario_grupo in grupo_encontrado.users:
                # _logger.critical(usuario_grupo.partner_id)
                notification_ids.append((0,0,
                            {
                                'res_partner_id': usuario_grupo.partner_id.id,
                                'notification_type': 'inbox'
                            }))
            message_sent = self.message_post(body=msg, message_type="notification",
                              subtype="mail.mt_comment",
                              # author_id=self.env.user.partner_id.id,
                              author_id=2,
                              notification_ids=notification_ids)
        else:
            raise exceptions.UserError("No se encontró el grupo Usuarios Técnicos Keralty, se debe configurar para permitir la funcionalidad de alertas.")


        # _logger.critical("Confirmar proyecto")
        return True

    def copy(self, default=None):
        self.ensure_one()


        company_id = self.env.company
        warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = warehouse.manufacture_pull_id.route_id.id
        route_mto = warehouse.mto_pull_id.route_id.id

        # Create Category
        existe_categoria = self.env['product.category'].search([('name', '=', 'Formularios Cliente'.title())])
        if not existe_categoria:
            categoria_consul_requer = self.env['product.category'].create({
                'name': 'Formularios Cliente'.title(),
            })
        else:
            categoria_consul_requer = existe_categoria

        product_template = self.env['product.template'].create({
            'name': self.ldm_producto_nuevo.product_tmpl_id.name + ' (copy)',
            'purchase_ok': False,
            'type': 'product',
            'categ_id': categoria_consul_requer.id,
            'company_id': company_id.id,
            'route_ids': [(6, 0, [route_manufacture, route_mto])]
        })

        # Create BOM
        bom_created = self.env['mrp.bom'].create({
            'product_tmpl_id': product_template.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        for linea_bom in self.areas_asociadas_sede:
            linea_bom_copy = linea_bom.copy()
            linea_bom_copy.bom_id = bom_created.id

        nombre_proyecto_copy = self.nombre_proyecto + ' (copy)'

        default = dict(default or {}, ldm_producto_nuevo=bom_created, nombre_proyecto=nombre_proyecto_copy, areas_asociadas_sede=bom_created.bom_line_ids)
        return super(FormularioCliente, self).copy(default)

# crear campo nombre_proyecto en ordenes de compra por proveedor

class PurchaseOrder(models.Model):
    """ Defines bills of material for a product or a product template """
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    nombre_proyecto = fields.Char(required=False, string="Proyecto Asociado", compute='_compute_nombre_proyecto',)

    @api.depends('nombre_proyecto', 'origin')
    def _compute_nombre_proyecto(self):
        for record in self:
            if record.origin:
                origin_split = record.origin.split(',')
                referencia_origen = self.env['mrp.production'].search([('name', '=', origin_split[-1].strip())])
                origen_producto = self.env['mrp.production'].search([('name', '=', referencia_origen.origin)])

                if origen_producto:
                    record.nombre_proyecto = origen_producto.product_id.name

                    if origen_producto.origin:
                        origen_producto_deep_level = self.env['mrp.production'].search([('name', '=', origen_producto.origin)])
                        record.nombre_proyecto = origen_producto_deep_level.product_id.name
                else:
                    record.nombre_proyecto = 'N/A'

            else:
                record.nombre_proyecto = 'N/A'

class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _name = 'mrp.bom'
    _inherit = 'mrp.bom'

    # M2 Utilizados para áreas cliente, derivadas, y diseño. Cada una contempla un cálculo diferente asignado a la misma variable
    m2 = fields.Float('M2', default=1.0)
    total_m2 = fields.Float('Total', default=1.0, digits=(16, 2), readonly=True, group_operator="sum",
                            compute='_compute_total_m2',)
    cantidad_final = fields.Float(
        'Cantidad Final', default=1.0,
        digits='Unit of Measure',)
    product_name_only = fields.Char(string="Nombre", compute='_compute_product_name_only')

    @api.depends('m2','total_m2', 'cantidad_final')
    def _compute_total_m2(self):
        for record in self:
            # _logger.critical(" COMPUTE TOTAL_M2 ")
            record.total_m2 = record.cantidad_final * record.m2


    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for record in self:
            if record.product_qty > 0:
                record.cantidad_final = record.product_qty
            else:
                raise exceptions.UserError(
                    "La Cantidad Inicial ingresada no puede ser 0 o menor. Elimine el registro si no lo requiere.")


    @api.onchange('cantidad_final')
    def _onchange_cantidad_final(self):
        for record in self:
            if record.cantidad_final < record.product_qty:
                raise exceptions.UserError(
                    "La Cantidad Final ingresada no puede ser menor a la cantidad inicial.")


    @api.depends('product_name_only')
    def _compute_product_name_only(self):
        for record in self:
            if record.product_id:
                record.product_name_only = record.product_id.name
            if record.product_tmpl_id:
                record.product_name_only = record.product_tmpl_id.name


class MrpBomLine(models.Model):
    _name = 'mrp.bom.line'
    _inherit = 'mrp.bom.line'

    # M2 Utilizados para áreas cliente, derivadas, y diseño. Cada una contempla un cálculo diferente asignado a la misma variable
    m2 = fields.Float('M2', default=1.0)
    total_m2 = fields.Float('Total', default=1.0, digits=(16, 2), readonly=True, group_operator="sum",
                            compute='_compute_total_m2',)
    product_image = fields.Binary(string="Imágen Área", compute='_compute_product_image')
    cantidad_final = fields.Float(
        'Cantidad Final', default=1.0,
        digits='Unit of Measure',)


    product_name_only = fields.Char(string="Nombre", compute='_compute_product_name_only')
    @api.depends('product_name_only')
    def _compute_product_name_only(self):
        for record in self:
            if record.product_id:
                record.product_name_only = record.product_id.name




    @api.depends('product_image')
    def _compute_product_image(self):
        for record in self:
            if record.product_id:
                if record.product_id.image_1024:
                    record.product_image = record.product_id.image_1024
                elif record.product_id.image_128:
                    record.product_image = record.product_id.image_128
                elif record.product_id.image_1920:
                    record.product_image = record.product_id.image_1920
                elif record.product_id.image_256:
                    record.product_image = record.product_id.image_256
                elif record.product_id.image_512:
                    record.product_image = record.product_id.image_512
                else:
                    record.product_image = None

                if record.product_tmpl_id:
                    if record.product_tmpl_id.image_1024:
                        record.product_image = record.product_tmpl_id.image_1024
                    elif record.product_tmpl_id.image_128:
                        record.product_image = record.product_tmpl_id.image_128
                    elif record.product_tmpl_id.image_1920:
                        record.product_image = record.product_tmpl_id.image_1920
                    elif record.product_tmpl_id.image_256:
                        record.product_image = record.product_tmpl_id.image_256
                    elif record.product_tmpl_id.image_512:
                        record.product_image = record.product_tmpl_id.image_512
                    else:
                        record.product_image = None


    @api.depends('m2','total_m2', 'cantidad_final')
    def _compute_total_m2(self):
        for record in self:
            # _logger.critical(" COMPUTE TOTAL_M2 ")
            record.total_m2 = record.cantidad_final * record.m2

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for record in self:
            if record.product_qty > 0:
                record.cantidad_final = record.product_qty
            else:
                raise exceptions.UserError(
                    "La Cantidad Inicial ingresada no puede ser 0 o menor. Elimine el registro si no lo requiere.")


    @api.onchange('cantidad_final')
    def _onchange_cantidad_final(self):
        for record in self:
            if record.cantidad_final < record.product_qty:
                raise exceptions.UserError(
                    "La Cantidad Final ingresada no puede ser menor a la cantidad inicial.")


# TODO: Crear campo adicional en modelo bom_line para que me permita
#  añadir la cantidad sin modificar nada de los productos asociados.
# class Area(models.Model):
#     _name = 'keralty_module.area'
#     _rec_name = "product_id"
#     _description = 'Área'
#
#     product_id = fields.Many2one('product.product', 'Área', required=True)
#     product_tmpl_id = fields.Many2one('product.template', 'Área Template', related='product_id.product_tmpl_id', readonly=False)
#     product_qty = fields.Float(
#         'Quantity', default=1.0,
#         digits='Cantidad Unidades', required=True)

# class MrpBomLineK(models.Model):
#     _name = 'keralty_module.bom_line'
#     _rec_name = "product_id"
#     _description = 'Bill of Material Line Keralty'
#
#     product_id = fields.Many2one( 'product.product', 'Área', required=True, check_company=True)
#     product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id', readonly=False)
#     product_qty = fields.Float(
#         'Quantity', default=1.0,
#         digits='Product Unit of Measure', required=True)
#     company_id = fields.Many2one(
#         related='bom_id.company_id', store=True, index=True, readonly=True)
#     bom_id = fields.Many2one(
#         'mrp.bom', 'Parent BoM',
#         index=True, ondelete='cascade', required=True)
#     parent_product_tmpl_id = fields.Many2one('product.template', 'Parent Product Template', related='bom_id.product_tmpl_id')


class FormularioValidacion(models.Model):
    _name = 'keralty_module.formulario.validacion'
    _description = 'Formulario Validación Técnica'
    _rec_name = 'nombre_tecnico'

    nombre_tecnico = fields.Char(required=True, string="Código Revisión",)
    formulario_cliente = fields.Many2one(string="Formulario Cliente",
                    comodel_name='keralty_module.formulario.cliente',
                    help="Formulario Cliente asociado para validación técnica.",
                    readonly=True, states={'draft': [('readonly', False)]},)

    imagen_empresa_html = fields.Html('Imágen Html', readonly=True, default='<img id="img" src="/keralty_module/static/src/img/logos/logo_keralty_default.svg" width="150px" height="100px" alt="Logo Formulario"/>', compute='_compute_imagen_empresa_html')

    areas_cliente = fields.Many2many(string="Áreas Cliente",
                    comodel_name='mrp.bom.line',
                    relation="validacion_areas_cliente",
                    column1="product_id",
                    column2="product_qty",
                    help="Listado de áreas solicitadas por el cliente.",
                    #domain="['|',('parent_product_tmpl_id','in',sede_seleccionada),('product_id.attribute_line_ids.id','=',empresa_seleccionada)]",
                    required=True,
                    copy=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
                    #compute='_compute_areas_cliente',)
                    # readonly=True, states={'draft': [('readonly', False)]},)

    areas_derivadas = fields.Many2many(string="Áreas Derivadas",
                    comodel_name='mrp.bom.line',
                    relation="validacion_areas_derivadas_line",
                    # column1="product_id",
                    # column2="product_qty",
                    help="Listado de áreas derivadas de la solicitud del cliente.",
                    domain="[('product_id.categ_id.name','ilike','Derivada')]",
                    #domain="['|',('parent_product_tmpl_id','in',sede_seleccionada),('product_id.attribute_line_ids.id','=',empresa_seleccionada)]",
                    required=True,
                    copy=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
                    #compute='_compute_areas_cliente',)
                    #readonly=True, states={'draft': [('readonly', False)]},)

    areas_diseño = fields.Many2many(string="Áreas Diseño",
                    comodel_name='mrp.bom.line',
                    relation="validacion_areas_diseno_line",
                    # column1="product_id",
                    # column2="product_qty",
                    help="Listado de áreas de diseño de la solicitud del cliente.",
                    domain="[('product_id.categ_id.name','ilike','Diseño')]",
                    #domain="['|',('parent_product_tmpl_id','in',sede_seleccionada),('product_id.attribute_line_ids.id','=',empresa_seleccionada)]",
                    required=True,
                    copy=True,
                    readonly=True, states={'draft': [('readonly', False)]},)
                    #compute='_compute_areas_cliente',)
                    #readonly=True, states={'draft': [('readonly', False)]},)

    porcentaje_pasillos = fields.Float('Porcentaje de pasillos y muros adicionales', default=30.0,
                    readonly=True, states={'draft': [('readonly', False)]},)
    total_m2_areas_cliente = fields.Float('Total M2 áreas cliente', default=1.0, digits=(16, 2), readonly=True, compute='_compute_m2_totales')
    total_m2_areas_derivadas = fields.Float('Total M2 áreas derivadas', default=1.0, digits=(16, 2), readonly=True, compute='_compute_m2_totales')
    total_m2_areas_diseno = fields.Float('Total M2 áreas diseño', default=1.0, digits=(16, 2), readonly=True, compute='_compute_m2_totales')
    total_m2_areas = fields.Float('Total M2 proyecto', default=1.0, digits=(16, 2), readonly=True, compute='_compute_m2_totales')

    ldm_areas_cliente = fields.Many2many(string="Producto nuevo creado para áreas cliente.",
                    comodel_name='mrp.bom',
                    relation="bom_producto_nuevo_cliente",
                    readonly=True, states={'draft': [('readonly', False)]},)
    ldm_areas_derivadas = fields.Many2many(string="Producto nuevo creado para áreas derivadas.",
                    comodel_name='mrp.bom',
                    relation="bom_producto_nuevo_derivadas",
                    readonly=True, states={'draft': [('readonly', False)]},)
    ldm_areas_disenio = fields.Many2many(string="Producto nuevo creado para áreas de diseño.",
                    comodel_name='mrp.bom',
                    relation="bom_producto_nuevo_disenio",
                    readonly=True, states={'draft': [('readonly', False)]},)
    # Sistema de Estados
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado')], string='Estado',
        copy=False, index=True, readonly=True,
        store=True, tracking=True, default='draft',
        help=" * Borrador: El proyecto se encuentra en edición.\n"
             " * Confirmado: El proyecto ha sido confirmado y no es editable por el cliente.\n"
             " * Realizado: El proyecto se ha ejecutado. \n"
             " * Cancelado: El proyecto ha sido cancelado.")

    @api.depends('total_m2_areas_cliente', 'total_m2_areas_derivadas', 'total_m2_areas_diseno', 'total_m2_areas', 'porcentaje_pasillos')
    def _compute_m2_totales(self):
        self.total_m2_areas_cliente = 0
        self.total_m2_areas_derivadas = 0
        self.total_m2_areas_diseno = 0
        self.total_m2_areas = 0

        for line in self.areas_cliente:
            self.total_m2_areas_cliente += line.total_m2
            self.total_m2_areas += line.total_m2

        for line in self.areas_derivadas:
            self.total_m2_areas_derivadas += line.total_m2
            self.total_m2_areas += line.total_m2

        for line in self.areas_diseño:
            self.total_m2_areas_diseno += line.total_m2
            self.total_m2_areas += line.total_m2

        if self.porcentaje_pasillos > 0:
            self.total_m2_areas = self.total_m2_areas + (self.total_m2_areas * self.porcentaje_pasillos) / 100
            # self.total_m2_areas = self.areas_cliente.total_m2# + self.areas_derivadas.total_m2 + self.areas_diseño.total_m2


    @api.depends('imagen_empresa_html')
    def _compute_imagen_empresa_html(self):
        if self.formulario_cliente:
            if self.formulario_cliente.imagen_empresa_html:
                self.imagen_empresa_html = self.formulario_cliente.imagen_empresa_html
        else:
            self.imagen_empresa_html = '<img id="img" src="/keralty_module/static/src/img/logos/logo_keralty_default.svg" width="150px" height="100px" alt="Logo Formulario"/>'

    '''
        Copia LdM
        Cuando cambia la sede seleccionada copia la lista de materiales (LdM) de la Sede (product)
        y la muestra en el campo areas_asociadas_sede     
    '''
    @api.onchange('formulario_cliente')
    def _onchange_formulario_cliente(self):
        # if self.formulario_cliente:
        objetoBusqueda = None
        # _logger.critical(self.formulario_cliente.areas_asociadas_sede)
        # if self.formulario_cliente.areas_asociadas_sede:
        #     self.areas_cliente = self.formulario_cliente.areas_asociadas_sede

        
        if self.formulario_cliente.imagen_empresa_html:
            self.imagen_empresa_html = self.formulario_cliente.imagen_empresa_html


        # Creación de categoría, producto y bom

        company_id = self.env.company
        warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = warehouse.manufacture_pull_id.route_id.id
        route_mto = warehouse.mto_pull_id.route_id.id

        # Create Category
        existe_categoria = self.env['product.category'].search([('name', '=', 'Formularios Validación'.title())])
        if not existe_categoria:
            categoria_consul_requer = self.env['product.category'].create({
                'name': 'Formularios Validación'.title(),
            })
        else:
            categoria_consul_requer = existe_categoria

        siguiente_codigo_secuencia = self.env['keralty_module.formulario.validacion'].search([], order='id ASC')
            
        if len(siguiente_codigo_secuencia) > 0:
            siguiente_codigo_secuencia = siguiente_codigo_secuencia[-1].id + 1
        else:
            siguiente_codigo_secuencia = 1

        existe_producto_cliente = self.env['product.template'].search([('name', '=', 'Areas Cliente Validación (' + str(siguiente_codigo_secuencia) + ')' )])
        existe_producto_derivada = self.env['product.template'].search([('name', '=', 'Areas Derivadas Validación (' + str(siguiente_codigo_secuencia) + ')' )])
        existe_producto_disenio = self.env['product.template'].search([('name', '=', 'Areas Diseño Validación (' + str(siguiente_codigo_secuencia) + ')' )])
        
        # Create Template Product cliente
        if not existe_producto_cliente:
            product_template_cliente = self.env['product.template'].create({
                'name': 'Areas Cliente Validación (' + str(siguiente_codigo_secuencia) + ')',
                'purchase_ok': False,
                'type': 'product',
                'categ_id': categoria_consul_requer.id,
                'company_id': company_id.id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]
            })
            # Create BOM
            bom_created_cliente = self.env['mrp.bom'].create({
                'product_tmpl_id': product_template_cliente.id,
                'product_qty': 1.0,
                'type': 'normal',
            })
        else:
            product_template_cliente = existe_producto_cliente
            # validar el bom seleccionado
            bom_created_cliente = existe_producto_cliente.bom_ids[0]

        # Create Template Product
        if not existe_producto_derivada:
            product_template_derivada = self.env['product.template'].create({
                'name': 'Areas Derivadas Validación (' + str(siguiente_codigo_secuencia) + ')',
                'purchase_ok': False,
                'type': 'product',
                'categ_id': categoria_consul_requer.id,
                'company_id': company_id.id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]
            })
            # Create BOM
            bom_created_derivada = self.env['mrp.bom'].create({
                'product_tmpl_id': product_template_derivada.id,
                'product_qty': 1.0,
                'type': 'normal',
            })
        else:
            product_template_derivada = existe_producto_derivada
            # validar el bom seleccionado
            bom_created_derivada = existe_producto_derivada.bom_ids[0]

        # Create Template Product diseño
        if not existe_producto_disenio:

            product_template_disenio = self.env['product.template'].create({
                'name': 'Areas Diseño Validación (' + str(siguiente_codigo_secuencia) + ')',
                'purchase_ok': False,
                'type': 'product',
                'categ_id': categoria_consul_requer.id,
                'company_id': company_id.id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]
            })
            # Create BOM
            bom_created_disenio = self.env['mrp.bom'].create({
                'product_tmpl_id': product_template_disenio.id,
                'product_qty': 1.0,
                'type': 'normal',
            })
        else:
            product_template_disenio = existe_producto_disenio
            # validar el bom seleccionado
            bom_created_disenio = product_template_disenio.bom_ids[0]

        self.ldm_areas_cliente = bom_created_cliente
        self.ldm_areas_derivadas = bom_created_derivada
        self.ldm_areas_disenio = bom_created_disenio


        # Cargar Áreas Derivadas automáticamente

        self.areas_cliente = None
        self.areas_derivadas = None
        self.areas_diseño = None
        total_bom_line_ids_derivada = None
        total_bom_line_ids_disenio = None

        # carga las áreas cliente a un nuevo producto ldm
        if self.formulario_cliente.areas_asociadas_sede:
            for linea_bom_cliente in self.formulario_cliente.areas_asociadas_sede:
                linea_bom_copy = linea_bom_cliente.copy()
                linea_bom_copy.bom_id = bom_created_cliente.id

        self.areas_cliente |= bom_created_cliente.bom_line_ids


        for sede_product_template in self.formulario_cliente.sede_seleccionada:
            for area in sede_product_template.bom_ids:
                for linea_bom in area.bom_line_ids:
                    # _logger.warning('LINEA BOOOOOM!!')
                    # _logger.warning(linea_bom)
                    for producto_seleccionado in self.formulario_cliente.producto_seleccionado:
                        # if producto_seleccionado.name in linea_bom.display_name:\
                        if linea_bom.bom_product_template_attribute_value_ids:
                            if producto_seleccionado.name in linea_bom.bom_product_template_attribute_value_ids.name:

                                # if "Derivada" in linea_bom.child_bom_id.product_tmpl_id.categ_id.name:
                                if "Derivada" in linea_bom.product_id.categ_id.name:
                                    if total_bom_line_ids_derivada:
                                        total_bom_line_ids_derivada += linea_bom#.child_bom_id
                                    else:
                                        total_bom_line_ids_derivada = linea_bom#.child_bom_id

                            
                                #if "Diseño" in linea_bom.child_bom_id.product_tmpl_id.categ_id.name:
                                if "Diseño" in linea_bom.product_id.categ_id.name:
                                    if total_bom_line_ids_disenio:
                                        total_bom_line_ids_disenio += linea_bom#.child_bom_id
                                    else:
                                        total_bom_line_ids_disenio = linea_bom#.child_bom_id

                for lineas_consultadas in total_bom_line_ids_derivada:
                    lineas_consultadas.product_qty = 1
                    lineas_consultadas.cantidad_final = 1
                    linea_bom_copy = lineas_consultadas.copy()
                    linea_bom_copy.product_qty = 1
                    linea_bom_copy.cantidad_final = 1
                    linea_bom_copy.bom_id = bom_created_derivada.id

                self.areas_derivadas |= bom_created_derivada.bom_line_ids

                for lineas_consultadas in total_bom_line_ids_disenio:
                    lineas_consultadas.product_qty = 1
                    lineas_consultadas.cantidad_final = 1
                    linea_bom_copy = lineas_consultadas.copy()
                    linea_bom_copy.product_qty = 1
                    linea_bom_copy.cantidad_final = 1
                    linea_bom_copy.bom_id = bom_created_disenio.id

                self.areas_diseño |= bom_created_disenio.bom_line_ids

    def action_realizar(self):
        total_boom_line_ids = None

        # _logger.critical("Realizar proyecto")
        '''
            TODO:
                Traer todas las áreas diligenciadas del formulario de falicación
                Copiar las áreas y crearlas en el módulo Inventario como productos y asociarles los materiales de construcción:
                Jerarquía:
                    Se copian áreas
                    Se copian materiales de construcción
                    
        '''
        if self.state != 'done':

            Product = self.env['product.product']
            BomLine = self.env['mrp.bom.line']

            # Create Category
            existe_categoria = self.env['product.category'].search([('name', '=', 'Consultas y Requerimientos'.title())])
            if not existe_categoria:
                categoria_consul_requer = self.env['product.category'].create({
                    'name': 'Consultas y Requerimientos'.title(),
                })
            else:
                categoria_consul_requer = existe_categoria

            # Referencia Interna: Existe, con timestamp y creamos. Iniciales del nombre del proyecto
            iniciales_proyecto = [s[0] for s in self.nombre_tecnico.split()]
            timestamp = datetime.timestamp(datetime.now())
            iniciales_proyecto = ''.join(str(x) for x in iniciales_proyecto) + '-' + str(timestamp).split('.')[0]
            # existe_ref_interna = self.env['product.category'].search([('name', '=', 'Consultas y Requerimientos')])

            company_id = self.env.company

            warehouse = self.env.ref('stock.warehouse0')
            route_manufacture = warehouse.manufacture_pull_id.route_id.id
            route_mto = warehouse.mto_pull_id.route_id.id

            # Create Template Product
            product_template = self.env['product.template'].create({
                'name': self.nombre_tecnico.title(),
                'purchase_ok': False,
                'type': 'product',
                'categ_id': categoria_consul_requer.id,
                'default_code': iniciales_proyecto.upper(),
                'company_id': company_id.id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]

            })
            # product = Product.create({
            #             'name': self.nombre_tecnico,
            #             # 'product_qty': area_derivada.product_qty,
            #         })

            # Create BOM
            bom_created = self.env['mrp.bom'].create({
                'product_tmpl_id': product_template.id,
                'product_qty': 1.0,
                'type': 'normal',
                # 'bom_line_ids': [0, 0,
                #                  total_boom_line_ids
                #     ]
                #     [
                #     (0, 0, {
                #         'product_id': product_A.id,
                #         'product_qty': 1,
                #         'bom_product_template_attribute_value_ids': [(4, sofa_red.id), (4, sofa_blue.id), (4, sofa_big.id)],
                #     }),
                #     (0, 0, {
                #         'product_id': product_B.id,
                #         'product_qty': 1,
                #         'bom_product_template_attribute_value_ids': [(4, sofa_red.id), (4, sofa_blue.id)]
                #     })
                # ]
            })

            '''
                DONE: Extraer el BomLine del producto del BOM de cada areas_derivadas y areas_diseño
            '''
            if total_boom_line_ids == None:
                total_boom_line_ids = self.areas_cliente
            else:
                total_boom_line_ids += self.areas_cliente

            # _logger.critical("BOM: AREAS CLIENTE: ")
            # _logger.critical(self.areas_cliente)

            for area_derivada in self.areas_derivadas:
                # _logger.critical("BOM: AREAS DERIVADAS: ")
                # _logger.critical(bom_created)
                # _logger.critical(area_derivada)
                # area_derivada.product_tmpl_id = product_template.id # Cambia el producto asociado, no sirve, se debe duplicar
                # Create Product
                # _logger.critical("BOM: AREAS DERIVADAS: ")
                # _logger.critical(area_derivada)
                # _logger.critical(area_derivada.product_tmpl_id)
                # _logger.critical(area_derivada.product_id)

                BomLine.create({
                    'bom_id': bom_created.id,
                    # 'product_id': area_derivada.product_id.id,
                    'product_id': area_derivada.product_tmpl_id.product_variant_id.id,
                    # 'product_tmpl_id': area_derivada.product_tmpl_id.id,
                    'product_qty': area_derivada.product_qty,
                })
                # if total_boom_line_ids == None:
                #     total_boom_line_ids = area_derivada.bom_line_ids
                # else:
                #     total_boom_line_ids += area_derivada.bom_line_ids

            for area_diseño in self.areas_diseño:
                # area_diseño.product_tmpl_id = product_template.id
                # Create Product
                # _logger.critical("BOM: AREAS DISEÑO: ")
                # _logger.critical(area_diseño)
                # _logger.critical(area_diseño.product_tmpl_id)
                # _logger.critical(area_diseño.product_id)

                BomLine.create({
                    'bom_id': bom_created.id,
                    # 'product_id': area_diseño.product_id.id,
                    'product_id': area_diseño.product_tmpl_id.product_variant_id.id,
                    # 'product_tmpl_id': area_diseño.product_tmpl_id.id,
                    'product_qty': area_diseño.product_qty,
                })

                # if total_boom_line_ids == None:
                #     total_boom_line_ids = area_diseño.bom_line_ids
                # else:
                #     total_boom_line_ids += area_diseño.bom_line_ids

            for bom_without_attrs in total_boom_line_ids:
                #bom_without_attrs.bom_product_template_attribute_value_ids = None

                BomLine.create({
                    'bom_id': bom_created.id,
                    'product_id': bom_without_attrs.product_id.id,
                    'product_qty': bom_without_attrs.product_qty,
                })

            # _logger.critical('-------------------------------')
            # _logger.critical('--------TOTAL BOM IDs----------')
            # _logger.critical('-------------------------------')
            # _logger.critical(total_boom_line_ids)
            # _logger.critical('-------------------------------')


            self.state = 'done'
        else:
            raise exceptions.UserError("El proyecto ya ha sido marcado como realizado.")

        return True


    def action_producir(self):

        '''
            TODO: Crear orden de producción de las sublistas de materiales, que contenga cada producto creado, dejar en estado borrador cada orden de producción creada.
            La validación de los materiales de construcción la realizará el área de construcción y dotación para luego ser marcada como realizada la orden.

            PRE: Revisar estructura de objeto mrp.production, traer la información de la creación del objeto
                 Buscar el product.product creado y asignarlo a la creación del objeto mrp.production
            1. Crear el objeto mrp.production y asignar los productos que se crearán
            2. Asignar el estado borrador o draft a cada una de las ordenes de producción creadas.
        '''
        if self.state == 'done':

            producto = self.env['product.product'].search([('name', '=', self.nombre_tecnico.title())], order='id asc')
            product_template = self.env['product.template'].search([('name', '=', self.nombre_tecnico.title())], order='id asc')
            if len(product_template) > 1:
                raise exceptions.UserError("Ya se encuentran creadas las órdenes de producción iniciales para éste proyecto.")

            bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_template.id)], order='id asc')
            _logger.critical('--------PRODUCTO ENCONTRADO----------')
            _logger.critical(producto)
            _logger.critical('--------BOM ID ENCONTRADO----------')
            _logger.critical(bom_id)

            # Obtener compañía:
            company_id = self.env.company
            if producto:
                production_id = self.env['mrp.production'].create({
                    'product_id': producto.id,
                    'product_tmpl_id': producto.product_tmpl_id.id,
                    'product_qty': 1,
                    'product_uom_id': producto.uom_id.id,
                    'company_id': company_id.id,
                    'bom_id': bom_id.id,
                    # 'move_raw_ids': bom.bom_line_id
                })

                production_id.product_qty = bom_id.product_qty
                production_id.product_uom_id = bom_id.product_uom_id.id
                production_id.move_raw_ids = [(2, move.id) for move in production_id.move_raw_ids.filtered(lambda x: not x.bom_line_id)]
                production_id.bom_id = bom_id.id
                # ////////////////////////////////
                # for bom_line in bom_id:
                #     # mo.move_raw_ids =
                #     # ._generate_workorders(boms)
                #     # move = production_id._generate_raw_move(bom_line, {'qty': bom_line.product_qty, 'parent_line': None})
                #     production_id._generate_finished_moves()
                #     production_id.move_raw_ids._adjust_procure_method()
                #
                #     # move = production_id._generate_workorders(bom_id)
                #
                #     _logger.critical('--------MOVE_RAW_IDs----------')
                #     _logger.critical('------------------------------')
                #     # _logger.critical(move)
                #     _logger.critical('------------------------------')
                #
                #     production_id._adjust_procure_method()
                #     move.action_confirm()
                #     bom_line.unlink()
                # mo.picking_type_id = bom_id.picking_type_id
                _logger.critical('--------MOVE_RAW_IDs----------')
                _logger.critical('------------------------------')
                _logger.critical(production_id.move_raw_ids)
                _logger.critical(production_id._onchange_move_raw())
                _logger.critical(production_id._onchange_location())
                _logger.critical(production_id._get_moves_raw_values())
                # _logger.critical(production_id.action_assign())
                # _logger.critical(production_id._get_moves_raw_values())
                # _logger.critical(production_id.move_raw_ids._adjust_procure_method())
                # _logger.critical(production_id.button_plan())
                # _logger.critical(production_id._get_ready_to_produce_state())
                _logger.critical(production_id._generate_finished_moves())
                _logger.critical('------------------------------')

                production_id._get_moves_raw_values()
                production_id._generate_finished_moves()
                production_id.move_raw_ids._adjust_procure_method()


                # production_id.onchange_product_id()
                # production_id._onchange_bom_id()

                # with self.assertRaises(exceptions.UserError):
                production_id.action_confirm()

                all_purchase_orders = self.env['purchase.order'].search([('state', '=', 'draft')], order='id asc')

                # _logger.critical('--------ORDEN COMPRA ----------')
                # _logger.critical('----------------------------------')
                # _logger.critical(all_purchase_orders)
                # _logger.critical('----------------------------------')

                for order in all_purchase_orders:
                    order.button_confirm()

                # _logger.critical('--------ORDEN PRODUCCIÓN----------')
                # _logger.critical('----------------------------------')
                # _logger.critical(production_id)
                # _logger.critical('----------------------------------')

                # _logger.critical('--------ORDEN COMPRA ----------')
                # _logger.critical('----------------------------------')
                # _logger.critical(all_purchase_orders)
                # _logger.critical('----------------------------------')
            else:
                raise exceptions.UserError("El proyecto no se ha encontrado o el nombre ha cambiado.")
        else:
            raise exceptions.UserError("El proyecto sebe estar marcado como realizado para poder crear la orden de fabricación.")

        return True

    def action_realizar_final(self):
        total_boom_line_ids = None

        # _logger.critical("Realizar proyecto")
        '''
            TODO:
                Traer todas las áreas diligenciadas del formulario de falicación
                Copiar las áreas action_producir_finaly crearlas en el módulo Inventario como productos y asociarles los materiales de construcción:
                Jerarquía:
                    Se copian áreas
                    Se copian materiales de construcción

        '''
        # if self.state != 'done':

        Product = self.env['product.product']
        BomLine = self.env['mrp.bom.line']

        # Create Category
        existe_categoria = self.env['product.category'].search(
            [('name', '=', 'Consultas y Requerimientos'.title())])
        if not existe_categoria:
            categoria_consul_requer = self.env['product.category'].create({
                'name': 'Consultas y Requerimientos'.title(),
            })
        else:
            categoria_consul_requer = existe_categoria

        # Referencia Interna: Existe, con timestamp y creamos. Iniciales del nombre del proyecto
        iniciales_proyecto = [s[0] for s in (self.nombre_tecnico + ' Final').split()]
        timestamp = datetime.timestamp(datetime.now())
        iniciales_proyecto = ''.join(str(x) for x in iniciales_proyecto) + '-' + str(timestamp).split('.')[0]
        # existe_ref_interna = self.env['product.category'].search([('name', '=', 'Consultas y Requerimientos')])

        company_id = self.env.company

        warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = warehouse.manufacture_pull_id.route_id.id
        route_mto = warehouse.mto_pull_id.route_id.id

        # Create Template Product
        existe_producto = self.env['product.template'].search(
            [('name', '=', self.nombre_tecnico.title() + ' Final')])
        if not existe_producto:

            product_template = self.env['product.template'].create({
                'name': self.nombre_tecnico.title() + ' Final',
                'purchase_ok': False,
                'type': 'product',
                'categ_id': categoria_consul_requer.id,
                'default_code': iniciales_proyecto.upper(),
                'company_id': company_id.id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]

            })
        else:
            raise exceptions.UserError("Ya se ha marcado como realizado. Revise la lista de productos de Inventario. Nombre del proyecto: " + self.nombre_tecnico.title() + ' Final')

        # product = Product.create({
        #             'name': self.nombre_tecnico,
        #             # 'product_qty': area_derivada.cantidad_final,
        #         })

        # Create BOM
        bom_created = self.env['mrp.bom'].create({
            'product_tmpl_id': product_template.id,
            'product_qty': 1.0,
            'type': 'normal',
            # 'bom_line_ids': [0, 0,
            #                  total_boom_line_ids
            #     ]
            #     [
            #     (0, 0, {
            #         'product_id': product_A.id,
            #         'product_qty': 1,
            #         'bom_product_template_attribute_value_ids': [(4, sofa_red.id), (4, sofa_blue.id), (4, sofa_big.id)],
            #     }),
            #     (0, 0, {
            #         'product_id': product_B.id,
            #         'product_qty': 1,
            #         'bom_product_template_attribute_value_ids': [(4, sofa_red.id), (4, sofa_blue.id)]
            #     })
            # ]
        })

        '''
            DONE: Extraer el BomLine del producto del BOM de cada areas_derivadas y areas_diseño
        '''
        if total_boom_line_ids == None:
            total_boom_line_ids = self.areas_cliente
        else:
            total_boom_line_ids += self.areas_cliente

        # _logger.critical("BOM: AREAS CLIENTE: ")
        # _logger.critical(self.areas_cliente)

        for area_derivada in self.areas_derivadas:
            # _logger.critical("BOM: AREAS DERIVADAS: ")
            # _logger.critical(bom_created)
            # _logger.critical(area_derivada)
            # area_derivada.product_tmpl_id = product_template.id # Cambia el producto asociado, no sirve, se debe duplicar
            # Create Product
            # _logger.critical("BOM: AREAS DERIVADAS: ")
            # _logger.critical(area_derivada)
            # _logger.critical(area_derivada.product_tmpl_id)
            # _logger.critical(area_derivada.product_id)

            BomLine.create({
                'bom_id': bom_created.id,
                # 'product_id': area_derivada.product_id.id,
                'product_id': area_derivada.product_tmpl_id.product_variant_id.id,
                # 'product_tmpl_id': area_derivada.product_tmpl_id.id,
                'product_qty': area_derivada.cantidad_final,
            })
            # if total_boom_line_ids == None:
            #     total_boom_line_ids = area_derivada.bom_line_ids
            # else:
            #     total_boom_line_ids += area_derivada.bom_line_ids

        for area_diseño in self.areas_diseño:
            # area_diseño.product_tmpl_id = product_template.id
            # Create Product
            # _logger.critical("BOM: AREAS DISEÑO: ")
            # _logger.critical(area_diseño)
            # _logger.critical(area_diseño.product_tmpl_id)
            # _logger.critical(area_diseño.product_id)

            BomLine.create({
                'bom_id': bom_created.id,
                # 'product_id': area_diseño.product_id.id,
                'product_id': area_diseño.product_tmpl_id.product_variant_id.id,
                # 'product_tmpl_id': area_diseño.product_tmpl_id.id,
                'product_qty': area_diseño.cantidad_final,
            })

            # if total_boom_line_ids == None:
            #     total_boom_line_ids = area_diseño.bom_line_ids
            # else:
            #     total_boom_line_ids += area_diseño.bom_line_ids

        for bom_without_attrs in total_boom_line_ids:
            # bom_without_attrs.bom_product_template_attribute_value_ids = None

            BomLine.create({
                'bom_id': bom_created.id,
                'product_id': bom_without_attrs.product_id.id,
                'product_qty': bom_without_attrs.cantidad_final,
            })

        # _logger.critical('-------------------------------')
        # _logger.critical('--------TOTAL BOM IDs----------')
        # _logger.critical('-------------------------------')
        # _logger.critical(total_boom_line_ids)
        # _logger.critical('-------------------------------')

        self.state = 'done'
        # else:
        #     raise exceptions.UserError("El proyecto ya ha sido marcado como realizado.")

        return True

    def action_producir_final(self):

        '''
            TODO: Crear orden de producción de las sublistas de materiales, que contenga cada producto creado, dejar en estado borrador cada orden de producción creada.
            La validación de los materiales de construcción la realizará el área de construcción y dotación para luego ser marcada como realizada la orden.

            PRE: Revisar estructura de objeto mrp.production, traer la información de la creación del objeto
                 Buscar el product.product creado y asignarlo a la creación del objeto mrp.production
            1. Crear el objeto mrp.production y asignar los productos que se crearán
            2. Asignar el estado borrador o draft a cada una de las ordenes de producción creadas.
        '''
        # if self.state == 'done':

        producto = self.env['product.product'].search([('name', '=', self.nombre_tecnico.title() + ' Final')],
                                                      order='id asc')
        product_template = self.env['product.template'].search(
            [('name', '=', self.nombre_tecnico.title() + ' Final')], order='id asc')
        if len(product_template) > 1:
            raise exceptions.UserError("Ya se encuentran creadas las órdenes de producción finales para éste proyecto.")

        bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_template.id)], order='id asc')
        # _logger.critical('--------PRODUCTO ENCONTRADO----------')
        # _logger.critical(producto)
        # _logger.critical('--------BOM ID ENCONTRADO----------')
        # _logger.critical(bom_id)

        # Obtener compañía:
        company_id = self.env.company
        if producto:
            production_id = self.env['mrp.production'].create({
                'product_id': producto.id,
                'product_tmpl_id': producto.product_tmpl_id.id,
                'product_qty': 1,
                'product_uom_id': producto.uom_id.id,
                'company_id': company_id.id,
                'bom_id': bom_id.id,
                # 'move_raw_ids': bom.bom_line_id
            })

            production_id.product_qty = bom_id.cantidad_final
            production_id.product_uom_id = bom_id.product_uom_id.id
            production_id.move_raw_ids = [(2, move.id) for move in
                                          production_id.move_raw_ids.filtered(lambda x: not x.bom_line_id)]
            # ////////////////////////////////
            # for bom_line in bom_id:
            #     # mo.move_raw_ids =
            #     # ._generate_workorders(boms)
            #     # move = production_id._generate_raw_move(bom_line, {'qty': bom_line.product_qty, 'parent_line': None})
            #     production_id._generate_finished_moves()
            #     production_id.move_raw_ids._adjust_procure_method()
            #
            #     # move = production_id._generate_workorders(bom_id)
            #
            #     _logger.critical('--------MOVE_RAW_IDs----------')
            #     _logger.critical('------------------------------')
            #     # _logger.critical(move)
            #     _logger.critical('------------------------------')
            #
            #     production_id._adjust_procure_method()
            #     move.action_confirm()
            #     bom_line.unlink()
            # mo.picking_type_id = bom_id.picking_type_id
            _logger.critical('--------MOVE_RAW_IDs----------')
            _logger.critical('------------------------------')
            _logger.critical(production_id.move_raw_ids)
            _logger.critical(production_id._onchange_move_raw())
            _logger.critical(production_id._onchange_location())
            _logger.critical(production_id._get_moves_raw_values())
            # _logger.critical(production_id.action_assign())
            # _logger.critical(production_id._get_moves_raw_values())
            # _logger.critical(production_id.move_raw_ids._adjust_procure_method())
            # _logger.critical(production_id.button_plan())
            # _logger.critical(production_id._get_ready_to_produce_state())
            _logger.critical(production_id._generate_finished_moves())
            _logger.critical('------------------------------')

            production_id._get_moves_raw_values()
            production_id._generate_finished_moves()
            production_id.move_raw_ids._adjust_procure_method()

            # production_id.onchange_product_id()
            # production_id._onchange_bom_id()

            # with self.assertRaises(exceptions.UserError):
            production_id.action_confirm()

            all_purchase_orders = self.env['purchase.order'].search([('state', '=', 'draft')], order='id asc')

            # _logger.critical('--------ORDEN COMPRA ----------')
            # _logger.critical('----------------------------------')
            # _logger.critical(all_purchase_orders)
            # _logger.critical('----------------------------------')

            for order in all_purchase_orders:
                order.button_confirm()

            # _logger.critical('--------ORDEN PRODUCCIÓN----------')
            # _logger.critical('----------------------------------')
            # _logger.critical(production_id)
            # _logger.critical('----------------------------------')

            # _logger.critical('--------ORDEN COMPRA ----------')
            # _logger.critical('----------------------------------')
            # _logger.critical(all_purchase_orders)
            # _logger.critical('----------------------------------')
        else:
            raise exceptions.UserError("El proyecto no se ha encontrado o el nombre ha cambiado.")
        # else:
        #     raise exceptions.UserError(
        #         "El proyecto sebe estar marcado como realizado para poder crear la orden de fabricación.")

        return True

    def action_calcular_areas(self):
        # _logger.critical("Calcular Áreas")
        self.total_m2_areas_cliente = 0
        self.total_m2_areas_derivadas = 0
        self.total_m2_areas_diseno = 0
        self.total_m2_areas = 0
        '''
            TODO: 
                PRE: 
                    Crear campos M2 Parametrizados y Total para áreas cliente
                                  M2 Calculados y Total para áreas derivadas
                                  M2 Sugeridos y Total para áreas de diseño
                                  Porcentaje de pasillos y muros adicionales
                                  Total para Formulario de Validación Técnica que realice la sumatoria de cada sección de áreas...
                ÁREAS CLIENTE                                  
                    1 Consultar M2 asociados a un área seleccionada (producto)
                    2 Calcular el total de metros cuadrados para área cliente utilizando el valor consultado
                ÁREAS DERIVADAS
                    1 Consultar la fórmula para el área derivada seleccionada desde el formulario de parametrización de cálculos
                    2 Calcular el total m2 del área derivada utilizando la fórmula consultada.
                ÁREAS DISEÑO
                    1 Consultar M2 asociados a un área de diseño o dejar campo en blanco
                    2 Calcular el total de M2 utilizando el valor ingresado/consultado
                
                CÁLCULO TOTAL DE ÁREAS (SUMATORIA) y porcentaje pasillos.
                    Mostrar total
                
                POST: 
                    Crear restricción en edición para cammpos M2 y Total para las áreas de cliente y las áreas derivadas (validar)
            
        '''
        for area_ciente in self.areas_cliente:
            # _logger.warning(area_ciente.product_id.name)
            for child_bom in area_ciente.child_line_ids:
                # _logger.critical(child_bom.product_id.name)
                # str.find("soccer")
                # TODO: Validar que la variante sea la misma del área seleccionada para traer el valor de M2 correcto.
                if "Área" in child_bom.product_id.name or "Area" in child_bom.product_id.name:
                    # _logger.critical(child_bom.product_qty)
                    area_ciente.m2 = child_bom.product_qty
                    self.total_m2_areas += area_ciente.m2 * area_ciente.cantidad_final # child_bom.total_m2
                    # _logger.critical("ÁREAS CLIENTES -> TOTAL_M2: " + str(self.total_m2_areas))

                    # _logger.critical(" CALC TOTAL_M2 ")
                    # area_ciente.total_m2 = area_ciente.product_qty * area_ciente.m2

        for area_derivada in self.areas_derivadas:
            # for bom_line in area_derivada.bom_line_ids:
            for bom_line in area_derivada.child_line_ids:
                # TODO: Validar que la variante sea la misma del área seleccionada para traer el valor de M2 correcto.
                if "Área" in bom_line.product_id.name or "Area" in bom_line.product_id.name:
                    area_derivada.m2 = bom_line.product_qty
                    self.total_m2_areas += area_derivada.m2 * area_derivada.cantidad_final

            # Consultar si el área derivada tiene formulación creada
            # encuentra_formulas_area = self.env['keralty_module.calculos'].search([('area_derivada.name', '=', area_derivada.product_tmpl_id.name)], order='id asc')
            encuentra_formulas_area = self.env['keralty_module.calculos'].search([('area_derivada.name', '=', area_derivada.product_id.name)], order='id asc')

            if len(encuentra_formulas_area) > 0:
                for formula_area_encontrada in encuentra_formulas_area:
                    find_vars_in_formula = re.findall('"(.+?)"', formula_area_encontrada.formula_aritmetica)
                    # _logger.critical(find_vars_in_formula)
                    calculo_formula = formula_area_encontrada.formula_aritmetica
                    calculo_formula_final = formula_area_encontrada.formula_aritmetica

                    for variable in find_vars_in_formula:
                        for area_cliente in self.areas_cliente:
                            if formula_area_encontrada.area_criterio_independiente:
                                if variable in area_cliente.product_id.name:
                                    calculo_formula = calculo_formula.replace(variable, str(area_cliente.product_qty))
                                    calculo_formula_final = calculo_formula_final.replace(variable, str(area_cliente.cantidad_final))
                            if formula_area_encontrada.campo_criterio_independiente:
                                variable_texto = 'self.formulario_cliente.' + variable
                                calculo_formula = calculo_formula.replace(variable, str(eval(variable_texto)))
                                calculo_formula_final = calculo_formula_final.replace(variable, str(eval(variable_texto)))
                                # _logger.critical(variable_texto)
                                # _logger.critical(calculo_formula)

                    for variable in find_vars_in_formula:
                        if variable in calculo_formula:
                            calculo_formula = calculo_formula.replace(variable, str(0))
                            calculo_formula_final = calculo_formula_final.replace(variable, str(0))
                            # raise exceptions.UserError("Una o más áreas dependientes no se han encontrado, por favor verifique que el área dependiente se encuentre en el listado de Áreas Cliente. Área: (" + variable + ")")
                            _logger.critical("Se ha asignado el valor de la variable (" + variable + ") por 0 (cero). Resultado de la fórmula: " + calculo_formula)

                    if formula_area_encontrada.variable_derivada == 'cantidad':
                        calculo_formula = calculo_formula.replace('"', '')
                        calculo_formula_final = calculo_formula_final.replace('"', '')
                        # _logger.critical(eval(calculo_formula))  # 1.4
                        area_derivada.product_qty = eval(calculo_formula)
                        area_derivada.cantidad_final = eval(calculo_formula_final)

                    if formula_area_encontrada.variable_derivada == 'area':
                        calculo_formula = calculo_formula.replace('"', '')
                        calculo_formula_final = calculo_formula_final.replace('"', '')
                        # _logger.critical(eval(calculo_formula))  # 1.4
                        area_derivada.m2 = eval(calculo_formula)
                        area_derivada.total_m2 = area_derivada.m2 * area_derivada.cantidad_final






        for area_diseño in self.areas_diseño:
            # _logger.warning(area_derivada.bom_line_ids)
            # for bom_line in area_diseño.bom_line_ids:
            for bom_line in area_diseño.child_line_ids:
                # _logger.critical(bom_line.product_id.name)
                # for child_bom in bom_line.child_line_ids:
                # _logger.critical(child_bom.product_id.name)
                # str.find("soccer")
                # TODO: Validar que la variante sea la misma del área seleccionada para traer el valor de M2 correcto.
                if "Área" in bom_line.product_id.name or "Area" in bom_line.product_id.name:
                    # _logger.critical(child_bom.product_qty)
                    area_diseño.m2 = bom_line.product_qty
                    self.total_m2_areas += area_diseño.m2 * area_diseño.cantidad_final # bom_line.total_m2
                    # _logger.critical("ÁREAS DISEÑO -> TOTAL_M2: " + str(self.total_m2_areas))

                    # _logger.critical(" CALC TOTAL_M2 ")
                    # area_ciente.total_m2 = area_derivada.product_qty * area_ciente.m2

        # TODO: Utilizar valor de pasillos... Eliminar calculos de suma total anteriores
        self.total_m2_areas = 0
        for line in self.areas_cliente:
            self.total_m2_areas_cliente += line.total_m2
            self.total_m2_areas += line.total_m2

        for line in self.areas_derivadas:
            self.total_m2_areas_derivadas += line.total_m2
            self.total_m2_areas += line.total_m2
        for line in self.areas_diseño:
            self.total_m2_areas_diseno += line.total_m2
            self.total_m2_areas += line.total_m2

        if self.porcentaje_pasillos > 0:
            self.total_m2_areas = self.total_m2_areas + (self.total_m2_areas * self.porcentaje_pasillos) / 100
        # self.total_m2_areas = self.areas_cliente.total_m2# + self.areas_derivadas.total_m2 + self.areas_diseño.total_m2
        return True

    @api.depends('areas_cliente','areas_derivadas','areas_diseño')
    def _compute_areas_cliente(self):

        for line in self:
            line.areas_cliente = line.areas_cliente

            line.areas_derivadas = line.areas_derivadas
            line.areas_diseño = line.areas_diseño

    def copy(self, default=None):
        self.ensure_one()


        company_id = self.env.company
        warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = warehouse.manufacture_pull_id.route_id.id
        route_mto = warehouse.mto_pull_id.route_id.id

        # Create Category
        existe_categoria = self.env['product.category'].search([('name', '=', 'Formularios Validación'.title())])
        if not existe_categoria:
            categoria_consul_requer = self.env['product.category'].create({
                'name': 'Formularios Validación'.title(),
            })
        else:
            categoria_consul_requer = existe_categoria


        # bom cliente
        product_template_cliente = self.env['product.template'].create({
            'name': self.ldm_areas_cliente.product_tmpl_id.name + ' (copy)',
            'purchase_ok': False,
            'type': 'product',
            'categ_id': categoria_consul_requer.id,
            'company_id': company_id.id,
            'route_ids': [(6, 0, [route_manufacture, route_mto])]
        })

        # Create BOM cliente
        bom_created_cliente = self.env['mrp.bom'].create({
            'product_tmpl_id': product_template_cliente.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

        # bom derivadas
        product_template_derivadas = self.env['product.template'].create({
            'name': self.ldm_areas_derivadas.product_tmpl_id.name + ' (copy)',
            'purchase_ok': False,
            'type': 'product',
            'categ_id': categoria_consul_requer.id,
            'company_id': company_id.id,
            'route_ids': [(6, 0, [route_manufacture, route_mto])]
        })

        # Create BOM derivadas
        bom_created_derivadas = self.env['mrp.bom'].create({
            'product_tmpl_id': product_template_derivadas.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

        # bom disenio
        product_template_disenio = self.env['product.template'].create({
            'name': self.ldm_areas_disenio.product_tmpl_id.name + ' (copy)',
            'purchase_ok': False,
            'type': 'product',
            'categ_id': categoria_consul_requer.id,
            'company_id': company_id.id,
            'route_ids': [(6, 0, [route_manufacture, route_mto])]
        })

        # Create BOM disenio
        bom_created_disenio = self.env['mrp.bom'].create({
            'product_tmpl_id': product_template_disenio.id,
            'product_qty': 1.0,
            'type': 'normal',
        })


        for linea_bom in self.areas_cliente:
            linea_bom_copy = linea_bom.copy()
            linea_bom_copy.bom_id = bom_created_cliente.id

        for linea_bom in self.areas_derivadas:
            linea_bom_copy = linea_bom.copy()
            linea_bom_copy.bom_id = bom_created_derivadas.id

        for linea_bom in self.areas_diseño:
            linea_bom_copy = linea_bom.copy()
            linea_bom_copy.bom_id = bom_created_disenio.id



        nombre_tecnico_copy = self.nombre_tecnico + ' (copy)'

        default = dict(default or {},
            nombre_tecnico=nombre_tecnico_copy, 
            ldm_areas_cliente=bom_created_cliente, 
            ldm_areas_derivadas=bom_created_derivadas, 
            ldm_areas_disenio=bom_created_disenio, 
            areas_cliente=bom_created_cliente.bom_line_ids,
            areas_derivadas=bom_created_derivadas.bom_line_ids,
            areas_diseño=bom_created_disenio.bom_line_ids,)

        return super(FormularioValidacion, self).copy(default)



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_cancel_all(self):
        """ Cancels production order, unfinished stock moves and set procurement
        orders in exception """
        if not self.move_raw_ids:
            self.state = 'cancel'
            return True
        self._action_cancel_all()
        # _logger.critical('action_cancel_all')
        # _logger.critical(self.move_raw_ids)
        return True

    def _action_cancel_all(self):
        documents_by_production = {}
        for production in self:
            documents = defaultdict(list)
            for move_raw_id in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                iterate_key = self._get_document_iterate_key(move_raw_id)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents(
                        {move_raw_id: (move_raw_id.product_uom_qty, 0)}, iterate_key, 'UP')
                    for key, value in document.items():
                        documents[key] += [value]
            if documents:
                documents_by_production[production] = documents

        self.workorder_ids.filtered(lambda x: x.state not in ['done', 'cancel']).action_cancel()
        finish_moves = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        raw_moves = self.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        (finish_moves | raw_moves)._action_cancel()
        picking_ids = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        picking_ids.action_cancel()

        for production, documents in documents_by_production.items():
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if not parent or parent._name == 'stock.picking' and parent.state == 'cancel' or parent == production:
                    continue
                filtered_documents[(parent, responsible)] = rendering_context
            production._log_manufacture_exception(filtered_documents, cancel=True)

        # In case of a flexible BOM, we don't know from the state of the moves if the MO should
        # remain in progress or done. Indeed, if all moves are done/cancel but the quantity produced
        # is lower than expected, it might mean:
        # - we have used all components but we still want to produce the quantity expected
        # - we have used all components and we won't be able to produce the last units
        #
        # However, if the user clicks on 'Cancel', it is expected that the MO is either done or
        # canceled. If the MO is still in progress at this point, it means that the move raws
        # are either all done or a mix of done / canceled => the MO should be done.
        self.filtered(lambda p: p.state not in ['done', 'cancel'] and p.bom_id.consumption == 'flexible').write(
            {'state': 'done'})


        production_to_cancel = self.env['mrp.production'].search([('origin', '=', self.name)])
        # _logger.critical('_____action_cancel_all OOOK')
        # _logger.critical(production_to_cancel)

        for move in production_to_cancel:
            move.action_cancel_all()
        # _logger.critical(self.move_raw_ids)
        return True
# hereda de producto y añade campo para relación con Categoría
# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#     categorias_ids = fields.Char(required=True, string="Categorias")
#     #categoria_ids = fields.Many2one(string="Categorías", comodel_name='keralty_module.categoria',
#     #                                help='Categorías asociadas al producto.')

class Categoria(models.Model):
    _name = 'keralty_module.categoria'
    _description = 'Categoria'

    formulario_cliente = fields.Many2one(string="Formulario Cliente", comodel_name='keralty_module.formulario.cliente',
                    help="Formulario Cliente asociado para validacion tecnica.")
    #productos_asociados = fields.One2many('product.TEMPLATE', 'categoria_ids', 'Productos Asociados')

class Sede(models.Model):
    _name = 'keralty_module.sede'
    _description = 'Sedes'
    _rec_name = 'nombre'

    nombre = fields.Char(required=True, string="Nombre Sede")
    descripcion = fields.Char(required=True, string="Descripción")

# Parametrización de Cálculos
class Calculos(models.Model):
    _name = 'keralty_module.calculos'
    _description = 'Parametrización de Cálculos'
    #_rec_name = 'nombre'

    # Restricción Cálculo Único
    _sql_constraints = [('unique_calculo', 'unique(empresa, area_derivada, variable_derivada)',
                         'Empresa, área derivada y variable derivada ya configuradas previamente!\nPor favor, verifique la información.')]

    empresa = fields.Many2one(string="Empresa", comodel_name='res.company',
                    help="Empresa asociada al cálculo.", required=True)
    area_derivada = fields.Many2one(string="Área Derivada", comodel_name='product.template',
                    help="Área Derivada asociada al cálculo.",
                    domain="[('categ_id.name','ilike','Derivada')]",
                    required=True)
    variable_derivada = fields.Selection([('area', 'Área'),('cantidad', 'Cantidad')])
    fuente_criterio = fields.Selection([('predeterminado', 'Valor Predeterminado'),('formulario', 'Formulario de Cliente')])
    area_criterio_independiente = fields.Many2one(string="Área como criterio independiente", comodel_name='product.template',
                    help="Criterio a utilizar en el cálculo.",
                    domain="[('categ_id.name','ilike','Cliente')]")
    campo_criterio_independiente = fields.Many2one(string="Campo como criterio independiente", comodel_name='ir.model.fields',
                    help="Criterio a utilizar en el cálculo.",
                    domain="[('model_id.model', 'ilike', 'formulario.cliente'), ('ttype', 'in', ('float', 'integer')), ('store', '=', 'True')]")

    variable_criterio = fields.Selection([('area', 'Área'),('cantidad', 'Cantidad')])
    formula_aritmetica = fields.Char(required=True, string="Fórmula")

    @api.onchange('fuente_criterio')
    def _onchange_fuente_criterio(self):
        if self.fuente_criterio == "predeterminado":
            self.area_criterio_independiente = None
            self.campo_criterio_independiente = None
            self.variable_criterio = None

    @api.onchange('formula_aritmetica')
    def _onchange_formula_aritmetica(self):
        res = {}
        if self.fuente_criterio == "formulario":
            if self.area_criterio_independiente.name:
                if not ('"' + self.area_criterio_independiente.name + '"' in self.formula_aritmetica):
                    warning = {
                        'title': "Error validación en la fórmula: {}".format(
                            self.formula_aritmetica
                        ),
                        'message': "La fórmula aritmética debe contener entre comillas dobles el nombre del criterio independiente: \"{}\" ".format(
                            self.area_criterio_independiente.name
                        ),
                    }
                    self.formula_aritmetica = ""
                    res.update({'warning': warning})
            if self.campo_criterio_independiente.name:
                if not ('"' + self.campo_criterio_independiente.name + '"' in self.formula_aritmetica):
                    warning = {
                        'title': "Error validación en la fórmula: {}".format(
                            self.formula_aritmetica
                        ),
                        'message': "La fórmula aritmética debe contener entre comillas dobles el nombre del criterio independiente: \"{}\" ".format(
                            self.campo_criterio_independiente.name
                        ),
                        #'type': 'notification',
                    }
                    self.formula_aritmetica = ""
                    res.update({'warning': warning})

            if not (self.area_criterio_independiente.name or self.campo_criterio_independiente.field_description):
                warning = {
                    'title': "Error validación en la fórmula: {}".format(
                        self.formula_aritmetica
                    ),
                    'message': "Debe seleccionar un criterio independiente, Área o Campo para la fuente de criterio: \"{}\" ".format(
                        dict(self._fields['fuente_criterio'].selection).get(self.fuente_criterio)
                    ),
                    # 'type': 'notification',
                }
                res.update({'warning': warning})
        return res

    def name_get(self):
        result = []
        for s in self:
            name = s.area_derivada.name + ' - (' + dict(s._fields['variable_derivada'].selection).get(s.variable_derivada) + ')'
            result.append((s.id, name))
        return result

class ProductCategory(models.Model):
    _inherit = "product.category"
    _sql_constraints = [
            ('name', 'UNIQUE (name)', 'El nombre de la Categoría debe ser único.')
        ]



class ProductTemplate(models.Model):
    _inherit = "product.template"

    adjunto = fields.Binary(string="Adjunto",)

    _sql_constraints = [('nombre_unico', 'unique(name)','El nombre del producto debe ser único.'),
                        ('referencia_unica', 'unique(default_code)','La referencia interna del producto debe ser única.')]

    name = fields.Char('Name', index=True, required=True, translate=True)
    company_id = fields.Many2one(
        'res.company', 'Company', index=1)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True)

    #No poder modificar el nombre de un producto por un nombre existente
    @api.onchange('name','company_id')
    def unrepeatable_name(self):
        name_pro=self.name
        pay=self.company_id.name
        exists = self.env['product.template'].search([('name','=',name_pro),('company_id','=',pay)])
        if len(exists) > 0:
            raise UserError(_('El producto con nombre "' + name_pro + '" ya esta creado en este país, por favor modifiquelo.'))


class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [('nombre_unico', 'unique(name)','El nombre del producto debe ser único.'),
                        ('referencia_unica', 'unique(default_code)','La referencia interna del producto debe ser única.')]

    default_code = fields.Char('Internal Reference', index=True)