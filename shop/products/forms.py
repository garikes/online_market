from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import Form, IntegerField, StringField, BooleanField, TextAreaField, validators, DecimalField


class Addproducts(Form):
    name = StringField('Name', [validators.DataRequired()])
    price = DecimalField('Prise', [validators.DataRequired()])
    discount = IntegerField('Discount', default=0)
    stock = IntegerField('Stock', [validators.DataRequired()])
    discription = TextAreaField('Description', [validators.DataRequired()])
    colors = TextAreaField('Colors', [validators.DataRequired()])

    image_1 = FileField('Image 1',
                        validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'])])
    image_2 = FileField('Image 2',
                        validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'])])
    image_3 = FileField('Image 3',
                        validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'])])
