from django import forms

class ProcessingConfigForm(forms.Form):
    """Formulario para configurar el procesamiento por lotes"""
    
    BATCH_KEY_CHOICES = [
        ('age', 'Edad'),
        ('job', 'Trabajo'),
        ('marital', 'Estado Civil'),
        ('education', 'Educación'),
        ('balance', 'Balance'),
        ('housing', 'Préstamo Vivienda'),
        ('loan', 'Préstamo Personal'),
        ('contact', 'Contacto'),
        ('day', 'Día del Mes'),
        ('month', 'Mes'),
        ('duration', 'Duración'),
        ('campaign', 'Campaña'),
        ('pdays', 'Días desde última campaña'),
        ('previous', 'Contactos previos'),
        ('poutcome', 'Resultado previo')
    ]
    
    batch_key = forms.ChoiceField(
        choices=BATCH_KEY_CHOICES,
        label='Clave de Fragmentación',
        help_text='Selecciona la columna por la cual se dividirán los datos en lotes'
    )
    
    batch_size = forms.IntegerField(
        min_value=100,
        max_value=5000,
        initial=1000,
        label='Tamaño del Lote',
        help_text='Número de registros por lote (entre 100 y 5000)'
    )
    
    use_sample = forms.BooleanField(
        required=False,
        initial=False,
        label='Usar muestra de datos',
        help_text='Si se marca, se usará solo una muestra del dataset para pruebas rápidas'
    )
    
    def clean_batch_size(self):
        batch_size = self.cleaned_data['batch_size']
        if batch_size < 100 or batch_size > 5000:
            raise forms.ValidationError('El tamaño del lote debe estar entre 100 y 5000 registros')
        return batch_size

class DataProcessingForm(forms.Form):
    """Formulario para procesar el archivo bank.csv y configurar el procesamiento por lotes"""
    
    batch_key = forms.ChoiceField(
        choices=[
            ('age', 'Edad'),
            ('job', 'Trabajo'),
            ('marital', 'Estado Civil'),
            ('education', 'Educación'),
            ('default', 'Default'),
            ('balance', 'Balance'),
            ('housing', 'Préstamo Vivienda'),
            ('loan', 'Préstamo Personal'),
            ('contact', 'Contacto'),
            ('day', 'Día'),
            ('month', 'Mes'),
            ('duration', 'Duración'),
            ('campaign', 'Campaña'),
            ('pdays', 'Días desde última campaña'),
            ('previous', 'Contactos previos'),
            ('poutcome', 'Resultado previo')
        ],
        label='Clave de Fragmentación',
        help_text='Selecciona la columna por la cual se dividirán los lotes'
    )
    
    batch_size = forms.IntegerField(
        min_value=100,
        max_value=10000,
        initial=1000,
        label='Tamaño del Lote',
        help_text='Número de registros por lote'
    )
    
    use_sample = forms.BooleanField(
        required=False,
        initial=False,
        label='Usar muestra',
        help_text='Si se marca, se usará solo una muestra del dataset para pruebas rápidas'
    )