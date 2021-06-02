# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import logging
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path

from random import randrange
from PIL import Image

_logger = logging.getLogger(__name__)

class Company(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    empresa_copy_ldm = fields.Many2one('res.company', string='Compañía copia LdM', index=True,
                    readonly=True, states={'no_copy': [('readonly', False)]},)

    copy_ldm = fields.Many2many(string="Listas de materiales asociadas a Compañía copia LdM",
                    comodel_name='mrp.bom',
                    relation="bom_company_copy",
                    help="Selección de Listas de materiales asociadas a Compañía copia LdM.",
                    domain="[('company_id','=',empresa_copy_ldm)]",
                    #required=True,
                    readonly=True, states={'no_copy': [('readonly', False)]},)

    # Sistema de Estados
    state = fields.Selection([
        ('no_copy', 'LdM No copiada.'),
        ('copied', 'Ldm Copiada.')], string='Estado',
        copy=False, index=True, readonly=True,
        store=True, tracking=True, default='no_copy',
        help=" * LdM No copiada: La lista de materiales no se ha copiado.\n"
             " * LdM Copiada: La lista de materiales se ha copiado de la Compañía copia LdM seleccionada.")

    def action_copy_ldm(self):

        if self.copy_ldm:

            BomLine = self.env['mrp.bom.line']

            for ldm in self.copy_ldm:
                # Create BOM
                bom_created = self.env['mrp.bom'].create({
                    'company_id': self.id,
                    'product_tmpl_id': ldm.product_tmpl_id.id,
                    'product_id': ldm.product_id.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                })

                for linea_bom in ldm.bom_line_ids:
                    # _logger.critical("COPY: LÍNEA BOM: linea_bom")
                    # _logger.critical(linea_bom.display_name)
                    # _logger.critical(linea_bom.product_qty)
                    # _logger.critical(linea_bom.product_uom_id)uom_unit_id

                    line_qty = linea_bom.product_uom_id._compute_quantity(linea_bom.product_qty, linea_bom.product_id.uom_id)

                    BomLine.create({
                        'company_id': self.id,
                        'bom_id': bom_created.id,
                        'product_id': linea_bom.product_id.id,
                        'product_qty': line_qty,
                        'product_qty_display': linea_bom.product_qty_display,
                        'product_uom_id_display': linea_bom.product_uom_id_display.id,

                    })
                
        else:
            raise UserError(_("No se encuentra ninguna lista de materiales asociada a la companía seleccionada."))


        self.state = 'copied'


        return True


    @api.onchange('empresa_copy_ldm')
    def _onchange_empresa_copy_ldm(self):
        self.copy_ldm = None

        if self.empresa_copy_ldm:
            self.copy_ldm = self.env['mrp.bom'].search([('company_id', '=', self.empresa_copy_ldm.id)])
