from odoo import models

class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    def write(self,vals):
        """
            ** Karena selain access right product creation yang hanya bisa create, update bahkan unlink mengreturn error
            ** jika ada field compute dan menggunakan attribute store=True maka bypass secara backend data yang di update menggunakan superuser atau sudo()
            
        """
        return super(ProductTemplate,self.sudo()).write(vals)